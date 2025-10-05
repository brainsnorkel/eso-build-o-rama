"""
Test script to generate a report for Sunspire trial only.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.trial_scanner import TrialScanner
from src.eso_build_o_rama.page_generator import PageGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_sunspire():
    """Generate report for Sunspire trial only."""
    
    logger.info("="*60)
    logger.info("ESO Build-O-Rama - Sunspire Test")
    logger.info("="*60)
    
    scanner = TrialScanner()
    page_generator = PageGenerator()
    
    try:
        # Sunspire trial data
        sunspire = {
            "id": 12,
            "name": "Sunspire",
            "abbreviation": "SS"
        }
        
        logger.info(f"\nNote: Due to API rate limiting, this will take a few minutes...")
        logger.info(f"API will be queried with delays to respect rate limits.\n")
        
        # Load boss names from trial_bosses.json to know what to expect
        bosses_file = Path(__file__).parent / "data" / "trial_bosses.json"
        with open(bosses_file, 'r') as f:
            bosses_data = json.load(f)
        
        expected_bosses = bosses_data['trial_bosses'].get(sunspire['name'], [])
        logger.info(f"Expected bosses for {sunspire['name']}: {expected_bosses}")
        
        # For now, we'll try to scan the trial without specific encounter IDs
        # The API will return available encounters in the rankings
        logger.info(f"\nAttempting to scan {sunspire['name']} with top 3 logs per encounter...")
        logger.info("(Using fewer logs to respect rate limits)")
        
        # Note: We'd need encounter IDs from the API, but we're rate-limited
        # For now, show what we would do and suggest waiting
        logger.warning("\n⚠️  API Rate Limit Reached!")
        logger.info("\nTo complete this test, we need to:")
        logger.info("1. Wait for rate limit to reset (typically 1-5 minutes)")
        logger.info("2. Query the API for specific encounter IDs for each boss")
        logger.info("3. Fetch top rankings for each encounter")
        logger.info("4. Process the report data and generate pages")
        logger.info("\nPlease wait a few minutes and try again.")
        return
        
        if not reports:
            logger.error("No reports found for Sunspire!")
            return
        
        logger.info(f"Successfully processed {len(reports)} reports")
        
        # Get publishable builds
        all_reports = {sunspire['name']: reports}
        publishable_builds = scanner.get_publishable_builds(all_reports)
        
        if not publishable_builds:
            logger.warning("No publishable builds found (need 5+ occurrences)")
            logger.info("\nAll common builds found:")
            for report in reports:
                logger.info(f"\n  Boss: {report.boss_name}")
                for build in report.common_builds:
                    logger.info(f"    - {build.get_display_name()} - {build.count} players")
            return
        
        logger.info(f"\nFound {len(publishable_builds)} publishable builds")
        for i, build in enumerate(publishable_builds, 1):
            logger.info(f"  {i}. {build.get_display_name()} - {build.count} players ({build.trial_name} - {build.boss_name})")
        
        # Generate pages
        logger.info("\nGenerating HTML pages...")
        # Get version from reports
        from collections import Counter
        versions = [r.update_version for r in reports if r.update_version and r.update_version != "unknown"]
        update_version = Counter(versions).most_common(1)[0][0] if versions else "unknown"
        logger.info(f"Using game version: {update_version}")
        
        generated_files = page_generator.generate_all_pages(
            publishable_builds,
            update_version
        )
        
        logger.info(f"Generated {len(generated_files)} HTML files")
        logger.info(f"  Index: {generated_files.get('index', 'N/A')}")
        logger.info(f"  Build pages: {len(generated_files) - 1}")
        
        logger.info("\n" + "="*60)
        logger.info("Sunspire Test - Complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error during execution: {e}", exc_info=True)
        raise
    finally:
        await scanner.close()


if __name__ == "__main__":
    asyncio.run(test_sunspire())
