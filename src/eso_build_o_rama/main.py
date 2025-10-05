"""
Main orchestration script for ESO Build-O-Rama.
"""

import argparse
import asyncio
import json
import logging
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class ESOBuildORM:
    """Main application orchestrator."""
    
    def __init__(self):
        """Initialize the application."""
        self.scanner = TrialScanner()
        self.page_generator = PageGenerator()
        self.data_store = DataStore()
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
            # Load trials data
            all_trials = self._load_trials()
            
            # Determine which trials to scan
            trials_to_scan = self._get_trials_to_scan(all_trials, test_mode, trial_name, trial_id)
            
            # Scan selected trials
            logger.info(f"\nScanning {len(trials_to_scan)} trials...")
            all_reports = await self.scanner.scan_all_trials(trials_to_scan, top_n=10)
            
            if not all_reports:
                logger.error("No reports found!")
                return
            
            logger.info(f"Successfully scanned {len(all_reports)} trials")
            
            # Get publishable builds
            publishable_builds = self.scanner.get_publishable_builds(all_reports)
            
            if not publishable_builds:
                logger.warning("No publishable builds found (need 5+ occurrences)")
                return
            
            logger.info(f"\nFound {len(publishable_builds)} publishable builds")
            
            # Save trial data incrementally
            if trial_name or trial_id:
                # Single trial mode - save this trial's data
                update_version = self._get_most_common_version(all_reports)
                for trial_name_scanned, trial_builds in self._group_builds_by_trial(publishable_builds).items():
                    self.data_store.save_trial_builds(trial_name_scanned, trial_builds, update_version)
                    logger.info(f"Saved {len(trial_builds)} builds for trial '{trial_name_scanned}'")
            else:
                # Full scan mode - save all trials
                update_version = self._get_most_common_version(all_reports)
                for trial_name_scanned, trial_builds in self._group_builds_by_trial(publishable_builds).items():
                    self.data_store.save_trial_builds(trial_name_scanned, trial_builds, update_version)
                    logger.info(f"Saved {len(trial_builds)} builds for trial '{trial_name_scanned}'")
            
            # Generate pages using all saved builds
            logger.info("\nGenerating HTML pages...")
            all_saved_builds = self.data_store.get_all_builds()
            trials_metadata = self.data_store.get_trials_metadata()
            update_version = self._get_most_common_version(all_reports)
            
            logger.info(f"Using game version: {update_version}")
            logger.info(f"Total builds across all trials: {len(all_saved_builds)}")
            
            generated_files = self.page_generator.generate_all_pages(
                all_saved_builds,
                update_version,
                trials_metadata
            )
            
            logger.info(f"Generated {len(generated_files)} HTML files")
            
            # Print summary
            self._print_summary(publishable_builds, generated_files)
            
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
    
    args = parser.parse_args()
    
    app = ESOBuildORM()
    
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
