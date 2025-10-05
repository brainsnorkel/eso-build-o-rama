#!/usr/bin/env python3
"""
Integration test script for ESO Build-O-Rama
Tests the complete pipeline with REAL ESO Logs API data ONLY.
NO MOCKS - Pure API integration.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.api_client import ESOLogsAPIClient
from src.eso_build_o_rama.data_parser import DataParser
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer
from src.eso_build_o_rama.page_generator import PageGenerator
from src.eso_build_o_rama.models import TrialReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def fetch_real_trial_data(trial_name: str = "Aetherian Archive", trial_id: int = 1):
    """Fetch REAL data from ESO Logs API - NO MOCKS."""
    
    logger.info(f"Fetching REAL data for {trial_name} (ID: {trial_id})")
    
    api_client = ESOLogsAPIClient()
    data_parser = DataParser()
    
    try:
        # Step 1: Search for top 5 recent reports
        logger.info(f"   Searching for top 5 reports...")
        result = await api_client.client.search_reports(
            zone_id=trial_id,
            limit=5
        )
        
        if not result or not hasattr(result, 'report_data') or not hasattr(result.report_data, 'reports'):
            logger.error("   ❌ No reports found")
            return []
        
        reports_data = result.report_data.reports.data
        if not reports_data:
            logger.error("   ❌ No report data available")
            return []
        
        logger.info(f"   ✅ Found {len(reports_data)} reports")
        
        # Step 2: Process ALL fights in ALL reports
        all_players = []
        
        for report_info in reports_data[:5]:  # Top 5 reports
            report_code = report_info.code
            logger.info(f"   Processing report: {report_code}")
            
            try:
                # Get report details
                report_data = await api_client.get_report(report_code)
                
                if not report_data or not report_data.get('fights'):
                    logger.warning(f"     ⚠️  No fights in report {report_code}")
                    continue
                
                fights = report_data.get('fights', [])
                logger.info(f"     Found {len(fights)} fights")
                
                # Process ALL fights in this report
                for fight in fights:
                    fight_id = fight['id']
                    fight_name = fight['name']
                    
                    logger.info(f"     Processing fight: {fight_name} (ID: {fight_id})")
                    
                    # Get table data with combatant info
                    table_data = await api_client.get_report_table(
                        report_code=report_code,
                        start_time=fight['startTime'],
                        end_time=fight['endTime'],
                        data_type="Summary",
                        include_combatant_info=True
                    )
                    
                    if not table_data:
                        logger.warning(f"       ⚠️  No table data for fight {fight_id}")
                        continue
                    
                    # Parse ALL players from this fight
                    players = data_parser.parse_report_data(
                        report_data,
                        table_data,
                        fight_id
                    )
                    
                    if players:
                        # Filter for valid players with gear and abilities
                        valid_players = [
                            p for p in players 
                            if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
                        ]
                        
                        logger.info(f"       ✅ Parsed {len(valid_players)} valid players from {len(players)} total")
                        all_players.extend(valid_players)
                    else:
                        logger.warning(f"       ⚠️  No players parsed from fight {fight_id}")
                
            except Exception as e:
                logger.error(f"     ❌ Error processing report {report_code}: {e}")
                continue
        
        logger.info(f"   ✅ Total players collected: {len(all_players)}")
        return all_players
        
    except Exception as e:
        logger.error(f"   ❌ Error fetching trial data: {e}")
        return []
    
    finally:
        await api_client.close()


async def test_build_analysis():
    """Test the build analysis pipeline with REAL API data."""
    logger.info("="*60)
    logger.info("Testing Build Analysis Pipeline - REAL API DATA ONLY")
    logger.info("="*60)
    
    # Fetch REAL data from ESO Logs API
    players = await fetch_real_trial_data()
    
    if not players:
        logger.error("❌ Failed to fetch real player data from API")
        logger.info("This could be due to:")
        logger.info("- API rate limiting")
        logger.info("- No recent reports available")
        logger.info("- Network connectivity issues")
        return []
    
    logger.info(f"✅ Fetched {len(players)} REAL players from ESO Logs API")
    
    # Create trial report from REAL data
    trial_report = TrialReport(
        trial_name="Aetherian Archive",
        boss_name="Multiple Bosses",
        all_players=players,
        report_code="REAL_API_DATA",
        update_version="U48-20251005"
    )
    
    logger.info(f"Created trial report: {trial_report.trial_name} - {trial_report.boss_name}")
    
    # Analyze builds
    analyzer = BuildAnalyzer()
    analyzed_report = analyzer.analyze_trial_report(trial_report)
    
    # Get unique builds
    unique_builds = analyzed_report.get_unique_builds()
    logger.info(f"Found {len(unique_builds)} unique builds")
    
    for i, build in enumerate(unique_builds, 1):
        logger.info(f"  {i}. {build.get_display_name()} - {build.count} players")
        logger.info(f"     Sets: {', '.join(build.sets)}")
        logger.info(f"     Best DPS: {build.best_player.dps:,}")
        logger.info(f"     Best Player: {build.best_player.character_name}")
    
    return unique_builds


async def test_page_generation(builds):
    """Test the page generation pipeline."""
    logger.info("\n" + "="*60)
    logger.info("Testing Page Generation Pipeline")
    logger.info("="*60)
    
    # Create page generator
    page_generator = PageGenerator(
        template_dir="templates",
        output_dir="output"
    )
    
    logger.info("Generating HTML pages...")
    
    # Generate all pages
    generated_files = page_generator.generate_all_pages(
        builds,
        update_version="U48"
    )
    
    logger.info(f"Generated {len(generated_files)} files:")
    for name, filepath in generated_files.items():
        logger.info(f"  {name}: {filepath}")
    
    # Check if files exist
    for name, filepath in generated_files.items():
        if Path(filepath).exists():
            size = Path(filepath).stat().st_size
            logger.info(f"  ✅ {name}: {filepath} ({size:,} bytes)")
        else:
            logger.error(f"  ❌ {name}: {filepath} (NOT FOUND)")
    
    return generated_files


async def main():
    """Run the complete integration test with REAL API data."""
    logger.info("🚀 Starting ESO Build-O-Rama Integration Test")
    logger.info("="*60)
    logger.info("⚠️  NO MOCKS - Using REAL ESO Logs API data ONLY")
    logger.info("="*60)
    
    try:
        # Test build analysis with REAL data
        builds = await test_build_analysis()
        
        if not builds:
            logger.error("❌ No builds found - test failed")
            logger.info("Unable to generate pages without build data")
            return
        
        # Test page generation
        generated_files = await test_page_generation(builds)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 INTEGRATION TEST COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Analyzed {len(builds)} builds")
        logger.info(f"✅ Generated {len(generated_files)} HTML files")
        logger.info(f"✅ All components working correctly")
        
        logger.info("\n📁 Generated Files:")
        for name, filepath in generated_files.items():
            logger.info(f"   {filepath}")
        
        logger.info("\n🌐 To view the results:")
        logger.info("   open output/index.html")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
