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
        
        logger.info(f"\nScanning {sunspire['name']} (Zone ID: {sunspire['id']})...")
        logger.info("This will query the API with rate limiting (0.5s between requests)")
        
        # Get encounter information from the API
        zones = await scanner.api_client.get_zones()
        sunspire_zone = None
        for zone in zones:
            if zone['id'] == sunspire['id']:
                sunspire_zone = zone
                break
        
        if not sunspire_zone or not sunspire_zone.get('encounters'):
            logger.error(f"Could not find encounters for {sunspire['name']}")
            return
        
        encounters = sunspire_zone['encounters']
        logger.info(f"Found {len(encounters)} encounters: {[e['name'] for e in encounters]}")
        
        # Scan each encounter
        all_reports = []
        for encounter in encounters:
            logger.info(f"\nScanning encounter: {encounter['name']} (ID: {encounter['id']})...")
            
            reports = await scanner.scan_trial(
                trial_zone_id=sunspire['id'],
                trial_name=sunspire['name'],
                encounter_id=encounter['id'],
                top_n=5
            )
            
            if reports:
                all_reports.extend(reports)
                logger.info(f"  ✅ Processed {len(reports)} reports for {encounter['name']}")
            else:
                logger.warning(f"  ⚠️  No reports found for {encounter['name']}")
        
        reports = all_reports
        
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
