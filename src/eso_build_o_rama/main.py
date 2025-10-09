"""
Main orchestration script for ESO Build-O-Rama.
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .trial_scanner import TrialScanner
from .page_generator import PageGenerator
from .models import CommonBuild
from .data_store import DataStore
from .cache_manager import CacheManager
from .social_preview_generator import SocialPreviewGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ESOBuildORM:
    """Main application orchestrator."""
    
    def get_output_directory(self) -> str:
        """Determine output directory based on git branch."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            if branch == 'main':
                return 'output'
            return 'output-dev'
        except Exception:
            # Default to 'output-dev' if git command fails (safer for development)
            return 'output-dev'
    
    def __init__(self, use_cache: bool = True, clear_cache: bool = False):
        """
        Initialize the application.
        
        Args:
            use_cache: Whether to use API response caching (default: True)
            clear_cache: Whether to clear existing cache on startup (default: False)
        """
        self.cache_manager = CacheManager() if use_cache else None
        
        # Clear cache if requested
        if clear_cache and self.cache_manager:
            self.cache_manager.clear_cache()
            logger.info("Cache cleared on startup")
        
        # Determine output directory based on git branch
        output_dir = self.get_output_directory()
        logger.info(f"Using output directory: {output_dir}")
        
        self.scanner = TrialScanner(cache_manager=self.cache_manager)
        self.page_generator = PageGenerator(output_dir=output_dir)
        self.data_store = DataStore(builds_file=f"{output_dir}/builds.json")
        self.trials_file = Path(__file__).parent.parent.parent / "data" / "trials.json"
    
    async def run(self, test_mode: bool = False, trial_name: Optional[str] = None, trial_id: Optional[int] = None):
        """
        Run the complete build scanning and generation process.
        
        Args:
            test_mode: If True, only scan one trial for testing
            trial_name: Specific trial name to scan (overrides test_mode)
            trial_id: Specific trial ID to scan (overrides test_mode)
        """
        logger.info("="*60)
        logger.info("ESO Build-O-Rama - Starting scan")
        logger.info("="*60)
        
        try:
            # Generate social media preview images first
            logger.info("Generating social media preview images...")
            self._generate_social_previews()
            
            # Load trials data
            all_trials = self._load_trials()
            
            # Determine which trials to scan
            trials_to_scan = self._get_trials_to_scan(all_trials, test_mode, trial_name, trial_id)
            
            # Scan selected trials
            logger.info(f"\nScanning {len(trials_to_scan)} trials...")
            all_reports = await self.scanner.scan_all_trials(trials_to_scan, top_n=12)
            
            if not all_reports:
                logger.error("No reports found!")
                return
            
            logger.info(f"Successfully scanned {len(all_reports)} trials")
            
            # Get publishable builds (includes optimized mundus fetching)
            publishable_builds = await self.scanner.get_publishable_builds(all_reports)
            
            if not publishable_builds:
                logger.warning("No publishable builds found for this trial (need 5+ occurrences for DPS, 3+ for tank/healer)")
                # Still regenerate pages from existing saved builds
                logger.info("Regenerating pages from existing saved builds...")
                all_saved_builds = self.data_store.get_all_builds()
                trials_metadata = self.data_store.get_trials_metadata()
                
                if all_saved_builds:
                    generated_files = self.page_generator.generate_all_pages(
                        all_saved_builds,
                        "unknown",
                        trials_metadata,
                        None
                    )
                    logger.info(f"Generated {len(generated_files)} HTML files from existing data")
                else:
                    logger.warning("No existing builds found to generate pages from")
                return
            
            logger.info(f"\nFound {len(publishable_builds)} publishable builds")
            
            # Save trial data incrementally
            # Get cache statistics if available
            cache_stats = None
            if hasattr(self, 'cache_manager'):
                cache_stats = self.cache_manager.get_cache_stats()
            
            if trial_name or trial_id:
                # Single trial mode - save this trial's data
                update_version = self._get_most_common_version(all_reports)
                for trial_name_scanned, trial_builds in self._group_builds_by_trial(publishable_builds).items():
                    # DEBUG: Log mundus status just before saving
                    mundus_count = sum(1 for b in trial_builds if b.best_player and b.best_player.mundus)
                    logger.info(f"DEBUG: Before save - {len(trial_builds)} builds, {mundus_count} have mundus")
                    for build in trial_builds[:3]:
                        if build.best_player:
                            logger.debug(f"  Build {build.build_slug[:40]}: mundus='{build.best_player.mundus}' (obj id={id(build.best_player)})")
                    
                    self.data_store.save_trial_builds(trial_name_scanned, trial_builds, update_version, cache_stats)
                    logger.info(f"Saved {len(trial_builds)} builds for trial '{trial_name_scanned}'")
            else:
                # Full scan mode - save all trials
                update_version = self._get_most_common_version(all_reports)
                for trial_name_scanned, trial_builds in self._group_builds_by_trial(publishable_builds).items():
                    self.data_store.save_trial_builds(trial_name_scanned, trial_builds, update_version, cache_stats)
                    logger.info(f"Saved {len(trial_builds)} builds for trial '{trial_name_scanned}'")
            
            # Generate pages using all saved builds
            logger.info("\nGenerating HTML pages...")
            all_saved_builds = self.data_store.get_all_builds()
            
            # BUGFIX: Merge freshly scanned builds (with mundus) into loaded builds
            # This ensures newly scanned trials have mundus data in generated pages
            if publishable_builds:
                # Create a mapping of (trial_name, boss_name, build_slug) to fresh builds
                fresh_builds_map = {}
                for fresh_build in publishable_builds:
                    key = (fresh_build.trial_name, fresh_build.boss_name, fresh_build.build_slug)
                    fresh_builds_map[key] = fresh_build
                
                # Replace loaded builds with fresh ones where available
                for i, loaded_build in enumerate(all_saved_builds):
                    key = (loaded_build.trial_name, loaded_build.boss_name, loaded_build.build_slug)
                    if key in fresh_builds_map:
                        all_saved_builds[i] = fresh_builds_map[key]
                        logger.debug(f"Replaced loaded build with fresh: {loaded_build.build_slug}")
            
            trials_metadata = self.data_store.get_trials_metadata()
            update_version = self._get_most_common_version(all_reports)
            
            logger.info(f"Using game version: {update_version}")
            logger.info(f"Total builds across all trials: {len(all_saved_builds)}")
            
            generated_files = self.page_generator.generate_all_pages(
                all_saved_builds,
                update_version,
                trials_metadata,
                cache_stats
            )
            
            logger.info(f"Generated {len(generated_files)} HTML files")
            
            # Print summary
            self._print_summary(publishable_builds, generated_files)
            
            # Log cache performance
            if self.cache_manager:
                self.cache_manager.log_cache_performance()
            
            logger.info("\n" + "="*60)
            logger.info("ESO Build-O-Rama - Complete!")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error during execution: {e}", exc_info=True)
            raise
        finally:
            await self.scanner.close()
    
    def _load_trials(self) -> List[Dict[str, Any]]:
        """Load trials data from JSON file."""
        if not self.trials_file.exists():
            logger.error(f"Trials file not found: {self.trials_file}")
            raise FileNotFoundError(f"Trials file not found: {self.trials_file}")
        
        with open(self.trials_file, 'r') as f:
            data = json.load(f)
        
        trials = data.get('trials', [])
        logger.info(f"Loaded {len(trials)} trials from {self.trials_file}")
        
        return trials
    
    def _get_trials_to_scan(self, all_trials: List[Dict[str, Any]], test_mode: bool, trial_name: Optional[str], trial_id: Optional[int]) -> List[Dict[str, Any]]:
        """
        Determine which trials to scan based on parameters.
        
        Args:
            all_trials: List of all available trials
            test_mode: If True, scan only first trial
            trial_name: Specific trial name to scan
            trial_id: Specific trial ID to scan
            
        Returns:
            List of trials to scan
        """
        if trial_id:
            # Find trial by ID
            matching_trials = [t for t in all_trials if t.get('id') == trial_id]
            if not matching_trials:
                logger.error(f"Trial with ID {trial_id} not found!")
                raise ValueError(f"Trial with ID {trial_id} not found")
            logger.info(f"Scanning trial by ID: {trial_id} ({matching_trials[0]['name']})")
            return matching_trials
        
        if trial_name:
            # Find trial by name (case-insensitive)
            matching_trials = [t for t in all_trials if t.get('name', '').lower() == trial_name.lower()]
            if not matching_trials:
                logger.error(f"Trial with name '{trial_name}' not found!")
                raise ValueError(f"Trial with name '{trial_name}' not found")
            logger.info(f"Scanning trial by name: {trial_name}")
            return matching_trials
        
        if test_mode:
            # In test mode, only process first trial
            logger.info("TEST MODE: Processing only first trial")
            return [all_trials[0]]
        
        # Default: scan all trials
        logger.info("Scanning all trials")
        return all_trials
    
    def _group_builds_by_trial(self, builds: List[CommonBuild]) -> Dict[str, List[CommonBuild]]:
        """
        Group builds by trial name.
        
        Args:
            builds: List of CommonBuild objects
            
        Returns:
            Dictionary mapping trial names to lists of builds
        """
        grouped = {}
        for build in builds:
            trial = build.trial_name
            if trial not in grouped:
                grouped[trial] = []
            grouped[trial].append(build)
        return grouped
    
    def _get_most_common_version(self, all_reports: Dict[str, List]) -> str:
        """Get the most common update version from all reports."""
        from collections import Counter
        
        versions = []
        for trial_reports in all_reports.values():
            for report in trial_reports:
                if report.update_version and report.update_version != "unknown":
                    versions.append(report.update_version)
        
        if versions:
            # Get the most common version
            most_common = Counter(versions).most_common(1)[0][0]
            return most_common
        
        return "unknown"
    
    def _generate_social_previews(self):
        """Generate social media preview images."""
        try:
            output_dir = self.get_output_directory()
            is_develop = 'dev' in output_dir.lower()
            
            # Generate to the correct output directory's static folder
            output_static_dir = Path(output_dir) / "static"
            output_static_dir.mkdir(parents=True, exist_ok=True)
            
            # Also generate to main static directory for reference
            main_static_dir = Path("static")
            main_static_dir.mkdir(exist_ok=True)
            
            # Generate preview to main static dir first
            generator = SocialPreviewGenerator(static_dir=str(main_static_dir))
            main_preview = generator.create_main_preview(is_develop)
            logger.info(f"Generated main social preview: {main_preview}")
            
            # Copy to output directory's static folder
            main_filename = "social-preview-dev.png" if is_develop else "social-preview.png"
            shutil.copy2(main_static_dir / main_filename, output_static_dir / main_filename)
            
            # Also copy the build preview if it exists
            build_filename = "social-preview-build-dev.png" if is_develop else "social-preview-build.png"
            if (main_static_dir / build_filename).exists():
                shutil.copy2(main_static_dir / build_filename, output_static_dir / build_filename)
            
            logger.info(f"Copied social previews to {output_static_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to generate social media previews: {e}")
    
    def _print_summary(
        self,
        builds: List[CommonBuild],
        generated_files: Dict[str, str]
    ):
        """Print summary of results."""
        logger.info("\n" + "-"*60)
        logger.info("SUMMARY")
        logger.info("-"*60)
        
        # Group by trial
        by_trial = {}
        for build in builds:
            if build.trial_name not in by_trial:
                by_trial[build.trial_name] = []
            by_trial[build.trial_name].append(build)
        
        logger.info(f"\nBuilds by Trial:")
        for trial, trial_builds in sorted(by_trial.items()):
            logger.info(f"  {trial}: {len(trial_builds)} builds")
        
        logger.info(f"\nTop 5 Most Popular Builds:")
        for i, build in enumerate(builds[:5], 1):
            logger.info(f"  {i}. {build.get_display_name()} - {build.count} players")
        
        logger.info(f"\nGenerated Files:")
        logger.info(f"  Index: {generated_files.get('index', 'N/A')}")
        logger.info(f"  Build pages: {len(generated_files) - 1}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='ESO Build-O-Rama - Scan trials and generate build pages')
    parser.add_argument('--trial', type=str, help='Specific trial name to scan')
    parser.add_argument('--trial-id', type=int, help='Specific trial ID to scan')
    parser.add_argument('--test', action='store_true', help='Test mode - scan only first trial')
    
    # Cache control arguments
    parser.add_argument('--use-cache', action='store_true', default=True, 
                       help='Use cached API responses when available (default: True)')
    parser.add_argument('--no-cache', action='store_true', 
                       help='Disable caching (fetch all data from API)')
    parser.add_argument('--clear-cache', action='store_true', 
                       help='Clear existing cache before running')
    parser.add_argument('--cache-stats', action='store_true', 
                       help='Show cache statistics and exit')
    
    args = parser.parse_args()
    
    # Check branch for safety - prevent develop branch from running in GitHub Actions
    try:
        result = subprocess.run(
            ['git', 'branch', '--show-current'],
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()
        if branch == 'develop' and os.getenv('GITHUB_ACTIONS'):
            logger.error("Develop branch should not run in GitHub Actions!")
            sys.exit(1)
    except Exception:
        pass  # Ignore git errors
    
    # Handle cache stats
    if args.cache_stats:
        cache_manager = CacheManager()
        stats = cache_manager.get_cache_stats()
        print(f"Cache Statistics:")
        print(f"  Cache directory: {stats['cache_dir']}")
        print(f"  Total files: {stats['total_files']}")
        print(f"  Total size: {stats['total_size_bytes'] / 1024 / 1024:.2f} MB")
        print(f"\nBy Type:")
        print(f"  Reports: {stats['by_type']['reports']['count']} files ({stats['by_type']['reports']['size_bytes'] / 1024:.1f} KB)")
        print(f"  Rankings: {stats['by_type']['rankings']['count']} files ({stats['by_type']['rankings']['size_bytes'] / 1024:.1f} KB)")
        print(f"  Buffs: {stats['by_type']['buffs']['count']} files ({stats['by_type']['buffs']['size_bytes'] / 1024:.1f} KB)")
        print(f"  Tables: {stats['by_type']['tables']['count']} files ({stats['by_type']['tables']['size_bytes'] / 1024:.1f} KB)")
        print(f"  Other: {stats['by_type']['other']['count']} files ({stats['by_type']['other']['size_bytes'] / 1024:.1f} KB)")
        print(f"\nSession Statistics:")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache misses: {stats['cache_misses']}")
        if stats['cache_hits'] + stats['cache_misses'] > 0:
            print(f"  Hit rate: {stats['hit_rate']*100:.1f}%")
        return
    
    # Determine cache settings
    use_cache = args.use_cache and not args.no_cache
    
    app = ESOBuildORM(use_cache=use_cache, clear_cache=args.clear_cache)
    
    # Determine scan mode
    if args.trial_id:
        await app.run(trial_id=args.trial_id)
    elif args.trial:
        await app.run(trial_name=args.trial)
    elif args.test:
        await app.run(test_mode=True)
    else:
        # Default: full scan of all trials
        await app.run()


if __name__ == "__main__":
    asyncio.run(main())
