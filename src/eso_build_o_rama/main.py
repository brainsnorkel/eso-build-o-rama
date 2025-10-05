"""
Main orchestration script for ESO Build-O-Rama.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .trial_scanner import TrialScanner
from .page_generator import PageGenerator
from .models import CommonBuild

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
        self.trials_file = Path(__file__).parent.parent.parent / "data" / "trials.json"
    
    async def run(self, test_mode: bool = False):
        """
        Run the complete build scanning and generation process.
        
        Args:
            test_mode: If True, only scan one trial for testing
        """
        logger.info("="*60)
        logger.info("ESO Build-O-Rama - Starting scan")
        logger.info("="*60)
        
        try:
            # Load trials data
            trials = self._load_trials()
            
            if test_mode:
                # In test mode, only process first trial
                trials = [trials[0]]
                logger.info("TEST MODE: Processing only first trial")
            
            # Scan all trials
            logger.info(f"\nScanning {len(trials)} trials...")
            all_reports = await self.scanner.scan_all_trials(trials, top_n=5)
            
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
            
            # Generate pages
            logger.info("\nGenerating HTML pages...")
            update_version = "U48"  # TODO: Get from game data
            
            generated_files = self.page_generator.generate_all_pages(
                publishable_builds,
                update_version
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
    app = ESOBuildORM()
    
    # For testing, use test_mode=True
    await app.run(test_mode=True)


if __name__ == "__main__":
    asyncio.run(main())
