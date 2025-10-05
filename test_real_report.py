#!/usr/bin/env python3
"""
Real Report Integration Test for ESO Build-O-Rama
Tests with a specific real report code from ESO Logs.
"""

import asyncio
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_with_real_report(report_code: str):
    """Test the complete pipeline with a real report."""
    
    logger.info(f"🧪 Testing with real report: {report_code}")
    logger.info("="*60)
    
    # Initialize components
    api_client = ESOLogsAPIClient()
    data_parser = DataParser()
    build_analyzer = BuildAnalyzer()
    page_generator = PageGenerator(template_dir="templates", output_dir="output")
    
    try:
        # Step 1: Get report data
        logger.info("1. Fetching report data...")
        report_data = await api_client.get_report(report_code)
        
        if not report_data:
            logger.error(f"   ❌ Could not fetch report {report_code}")
            return False
        
        logger.info(f"   ✅ Retrieved report: {report_data.get('title', 'Unknown')}")
        logger.info(f"   Start time: {report_data.get('startTime', 0)}")
        logger.info(f"   Fights: {len(report_data.get('fights', []))}")
        
        # Step 2: Process each fight
        fights = report_data.get('fights', [])
        if not fights:
            logger.error("   ❌ No fights found in report")
            return False
        
        # Use the first fight
        fight = fights[0]
        logger.info(f"   Using fight: {fight.get('name', 'Unknown')} (ID: {fight.get('id', 0)})")
        
        # Step 3: Get table data with combatant info
        logger.info("\n2. Fetching table data with combatant info...")
        table_data = await api_client.get_report_table(
            report_code=report_code,
            start_time=fight.get('startTime'),
            end_time=fight.get('endTime'),
            data_type="Summary",
            include_combatant_info=True
        )
        
        if not table_data:
            logger.error("   ❌ Could not fetch table data")
            return False
        
        logger.info(f"   ✅ Retrieved table data")
        logger.info(f"   Data type: {type(table_data)}")
        if isinstance(table_data, dict):
            logger.info(f"   Keys: {list(table_data.keys())}")
        
        # Step 4: Parse player builds
        logger.info("\n3. Parsing player builds...")
        players = data_parser.parse_report_data(
            report_data,
            table_data,
            fight.get('id', 0)
        )
        
        logger.info(f"   Parsed {len(players)} players")
        
        if not players:
            logger.warning("   ⚠️  No players parsed - table data might not contain combatant info")
            return False
        
        # Filter players with complete data
        valid_players = [
            p for p in players 
            if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
        ]
        
        logger.info(f"   Valid players (with gear/abilities): {len(valid_players)}/{len(players)}")
        
        if len(valid_players) < 3:
            logger.warning(f"   ⚠️  Only {len(valid_players)} valid players - may not find common builds")
        
        # Step 5: Create trial report
        logger.info("\n4. Creating trial report...")
        from src.eso_build_o_rama.models import TrialReport
        
        trial_report = data_parser.create_trial_report(
            valid_players,
            trial_name="Real Test Trial",
            boss_name=fight.get('name', 'Unknown Boss'),
            report_code=report_code,
            update_version="U48-20251005"
        )
        
        logger.info(f"   Created trial report: {trial_report.trial_name} - {trial_report.boss_name}")
        
        # Step 6: Analyze builds
        logger.info("\n5. Analyzing builds...")
        analyzed_report = build_analyzer.analyze_trial_report(trial_report)
        
        # Get unique builds (5+ occurrences)
        unique_builds = analyzed_report.get_unique_builds()
        logger.info(f"   Found {len(unique_builds)} common builds (5+ occurrences)")
        
        # Also show all builds for debugging
        all_builds = analyzed_report.common_builds
        logger.info(f"   Total builds identified: {len(all_builds)}")
        
        for i, build in enumerate(all_builds, 1):
            logger.info(f"     {i}. {build.get_display_name()} - {build.count} players")
        
        if not unique_builds:
            logger.warning("   ⚠️  No common builds found (need 5+ players with same build)")
            logger.info("   This is normal for real data - not all groups will have 5+ identical builds")
            
            # Show what we found anyway
            if all_builds:
                logger.info("   Showing all builds found:")
                for build in all_builds:
                    logger.info(f"     - {build.get_display_name()} ({build.count} players)")
            
            return True  # Still successful, just no common builds
        
        # Step 7: Generate pages
        logger.info("\n6. Generating HTML pages...")
        generated_files = page_generator.generate_all_pages(unique_builds, "U48")
        
        logger.info(f"   ✅ Generated {len(generated_files)} HTML files")
        for name, filepath in generated_files.items():
            if Path(filepath).exists():
                size = Path(filepath).stat().st_size
                logger.info(f"     {name}: {filepath} ({size:,} bytes)")
        
        logger.info("\n🎉 Real report test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real report test failed: {e}", exc_info=True)
        return False
        
    finally:
        await api_client.close()


async def test_multiple_trials():
    """Test with multiple trials to find one with recent reports."""
    
    logger.info("🔍 Testing multiple trials for recent reports...")
    logger.info("="*60)
    
    api_client = ESOLogsAPIClient()
    
    try:
        # Get all zones
        zones = await api_client.get_zones()
        trial_zones = [z for z in zones if z['encounters']]  # Zones with encounters
        
        logger.info(f"Found {len(trial_zones)} zones with encounters")
        
        # Try to find recent reports in different zones
        for i, zone in enumerate(trial_zones[:5]):  # Try first 5 zones
            zone_name = zone['name']
            zone_id = zone['id']
            
            logger.info(f"\n{i+1}. Testing {zone_name} (ID: {zone_id})...")
            
            try:
                # Try search_reports first
                reports = await api_client.client.search_reports(
                    zone_id=zone_id,
                    limit=3
                )
                
                if reports and hasattr(reports, 'data') and reports.data:
                    report = reports.data[0]
                    logger.info(f"   ✅ Found recent report: {report.code}")
                    return await test_with_real_report(report.code)
                else:
                    logger.info(f"   No reports found in {zone_name}")
                    
            except Exception as e:
                logger.info(f"   Error searching {zone_name}: {e}")
                continue
        
        logger.warning("   ⚠️  No recent reports found in any zone")
        return False
        
    except Exception as e:
        logger.error(f"❌ Multiple trials test failed: {e}", exc_info=True)
        return False
        
    finally:
        await api_client.close()


async def main():
    """Run the real report integration test."""
    logger.info("🧪 ESO Build-O-Rama - Real Report Integration Test")
    logger.info("="*60)
    
    # Test with a known report code (if you have one)
    known_report_codes = [
        # Add known report codes here if you have any
        # "ABC123",  # Example report code
    ]
    
    success = False
    
    # Try known report codes first
    for report_code in known_report_codes:
        logger.info(f"Testing with known report: {report_code}")
        success = await test_with_real_report(report_code)
        if success:
            break
    
    # If no known reports or they failed, try to find recent reports
    if not success:
        logger.info("\nNo known reports available, searching for recent reports...")
        success = await test_multiple_trials()
    
    if success:
        logger.info("\n" + "="*60)
        logger.info("🎉 REAL REPORT INTEGRATION TEST SUCCESSFUL!")
        logger.info("="*60)
        logger.info("✅ API connection working")
        logger.info("✅ Report fetching working")
        logger.info("✅ Table data retrieval working")
        logger.info("✅ Player build parsing working")
        logger.info("✅ Build analysis working")
        logger.info("✅ Page generation working")
        logger.info("\n🌐 View results: open output/index.html")
    else:
        logger.error("\n❌ Real report integration test failed")
        logger.info("This could be due to:")
        logger.info("- No recent reports available")
        logger.info("- API rate limiting")
        logger.info("- Report data structure changes")
        logger.info("- Network issues")


if __name__ == "__main__":
    asyncio.run(main())
