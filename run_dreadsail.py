"""Run ESO Build-O-Rama for Dreadsail Reef."""
import asyncio
import logging
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.trial_scanner import TrialScanner
from src.eso_build_o_rama.page_generator import PageGenerator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    logger.info("="*60)
    logger.info("Running ESO Build-O-Rama for Dreadsail Reef")
    logger.info("="*60)
    
    scanner = TrialScanner()
    page_generator = PageGenerator()
    
    try:
        trial_name = "Dreadsail Reef"
        trial_id = 16
        
        logger.info(f"Fetching encounter list for {trial_name}...")
        zones = await scanner.api_client.get_zones()
        trial_zone = next((z for z in zones if z['id'] == trial_id), None)
        
        if not trial_zone or not trial_zone.get('encounters'):
            logger.error(f"No encounters found for {trial_name}")
            return
        
        encounters = trial_zone['encounters']
        logger.info(f"Found {len(encounters)} encounters")
        for enc in encounters:
            logger.info(f"  - {enc['name']} (ID: {enc['id']})")
        
        all_reports = {}
        trial_reports = []
        
        logger.info(f"\nScanning encounters (top 10 reports per boss)...")
        for encounter in encounters:
            enc_id = encounter['id']
            enc_name = encounter['name']
            
            logger.info(f"  Scanning: {enc_name}")
            reports = await scanner.scan_trial(
                trial_zone_id=trial_id,
                trial_name=trial_name,
                encounter_id=enc_id,
                top_n=10
            )
            
            if reports:
                trial_reports.extend(reports)
                logger.info(f"    ✓ Found {len(reports)} reports")
        
        if not trial_reports:
            logger.error("No reports found!")
            return
        
        all_reports[trial_name] = trial_reports
        logger.info(f"\nSuccessfully scanned {trial_name}: {len(trial_reports)} total reports")
        
        publishable_builds = scanner.get_publishable_builds(all_reports)
        
        if not publishable_builds:
            logger.warning("No publishable builds found")
            return
        
        logger.info(f"Found {len(publishable_builds)} publishable builds")
        
        # Check mundus data
        logger.info("\n" + "="*60)
        logger.info("MUNDUS STONE CHECK:")
        logger.info("="*60)
        for i, build in enumerate(publishable_builds[:10], 1):
            mundus = build.best_player.mundus if build.best_player else "N/A"
            player_name = build.best_player.player_name if build.best_player else "N/A"
            logger.info(f"{i}. {build.get_display_name()[:50]:<50} | Player: {player_name:<20} | Mundus: '{mundus}'")
        
        # Generate pages
        logger.info("\nGenerating HTML pages...")
        update_version = "test"
        for trial_reports in all_reports.values():
            for report in trial_reports:
                if report.update_version and not report.update_version.startswith("unknown"):
                    update_version = report.update_version
                    break
        
        generated_files = page_generator.generate_all_pages(publishable_builds, update_version)
        
        logger.info(f"Generated {len(generated_files)} HTML files")
        
        if 'index' in generated_files:
            import subprocess
            output_file = Path(generated_files['index'])
            logger.info(f"\n✓ Report generated: {output_file}")
            logger.info(f"  Opening in browser...")
            subprocess.run(['open', str(output_file)])
        
        logger.info("\n" + "="*60)
        logger.info("Complete!")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        raise
    finally:
        await scanner.close()

if __name__ == "__main__":
    asyncio.run(main())

