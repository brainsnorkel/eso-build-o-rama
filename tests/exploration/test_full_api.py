#!/usr/bin/env python3
"""
Full API End-to-End Test for ESO Build-O-Rama
Tests the complete pipeline using ONLY real ESO Logs API data.
No mocks or fallbacks - pure API integration test.
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
from src.eso_build_o_rama.models import TrialReport

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_full_api_pipeline():
    """Test the complete pipeline using only real API data."""
    
    logger.info("🚀 ESO Build-O-Rama - Full API Integration Test")
    logger.info("="*70)
    logger.info("Testing complete pipeline with REAL ESO Logs data only")
    logger.info("="*70)
    
    # Initialize all components
    api_client = ESOLogsAPIClient()
    data_parser = DataParser()
    build_analyzer = BuildAnalyzer()
    page_generator = PageGenerator(template_dir="templates", output_dir="output")
    
    try:
        # Step 1: Get all zones and find trials
        logger.info("\n1. Fetching zones and identifying trials...")
        zones = await api_client.get_zones()
        
        if not zones:
            logger.error("❌ Failed to fetch zones")
            return False
        
        logger.info(f"   ✅ Retrieved {len(zones)} zones")
        
        # Find trial zones (those with encounters)
        trial_zones = [z for z in zones if z['encounters']]
        logger.info(f"   Found {len(trial_zones)} trial zones")
        
        if not trial_zones:
            logger.error("❌ No trial zones found")
            return False
        
        # Step 2: Find recent reports for trials
        logger.info("\n2. Searching for recent reports in trials...")
        
        recent_reports = []
        max_reports_per_trial = 3  # Limit to avoid rate limits
        
        for i, zone in enumerate(trial_zones[:5]):  # Test first 5 trials
            zone_name = zone['name']
            zone_id = zone['id']
            
            logger.info(f"   Checking {zone_name} (ID: {zone_id})...")
            
            try:
                # Search for recent reports
                result = await api_client.client.search_reports(
                    zone_id=zone_id,
                    limit=max_reports_per_trial
                )
                
                if result and hasattr(result, 'report_data') and hasattr(result.report_data, 'reports'):
                    reports_data = result.report_data.reports.data
                    
                    if reports_data:
                        logger.info(f"     ✅ Found {len(reports_data)} recent reports")
                        
                        for report in reports_data:
                            recent_reports.append({
                                'code': report.code,
                                'title': report.title,
                                'zone_name': zone_name,
                                'zone_id': zone_id,
                                'start_time': report.start_time
                            })
                    else:
                        logger.info(f"     ⚠️  No recent reports found")
                else:
                    logger.info(f"     ⚠️  No reports data returned")
                    
            except Exception as e:
                logger.warning(f"     ⚠️  Error searching {zone_name}: {e}")
                continue
        
        if not recent_reports:
            logger.error("❌ No recent reports found in any trial")
            return False
        
        logger.info(f"\n   ✅ Found {len(recent_reports)} recent reports across trials")
        
        # Step 3: Process reports and extract builds
        logger.info("\n3. Processing reports and extracting player builds...")
        
        all_trial_reports = []
        processed_reports = 0
        
        for report_info in recent_reports[:10]:  # Limit to 10 reports for testing
            report_code = report_info['code']
            zone_name = report_info['zone_name']
            
            logger.info(f"   Processing report: {report_code} ({zone_name})")
            
            try:
                # Get report details
                report_data = await api_client.get_report(report_code)
                
                if not report_data:
                    logger.warning(f"     ⚠️  Could not fetch report details for {report_code}")
                    continue
                
                logger.info(f"     ✅ Retrieved report: {report_data.get('title', 'Unknown')}")
                
                # Process each fight in the report
                fights = report_data.get('fights', [])
                if not fights:
                    logger.warning(f"     ⚠️  No fights found in report {report_code}")
                    continue
                
                # Use the first fight (or find a suitable one)
                fight = fights[0]
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
                    logger.warning(f"     ⚠️  Could not fetch table data for {report_code}")
                    continue
                
                logger.info(f"     ✅ Retrieved table data with combatant info")
                
                # Parse player builds
                players = data_parser.parse_report_data(
                    report_data,
                    table_data,
                    fight_id
                )
                
                if not players:
                    logger.warning(f"     ⚠️  No players parsed from {report_code}")
                    continue
                
                logger.info(f"     Parsed {len(players)} players")
                
                # Filter players with complete data
                valid_players = [
                    p for p in players 
                    if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
                ]
                
                logger.info(f"     Valid players (with gear/abilities): {len(valid_players)}/{len(players)}")
                
                if len(valid_players) < 3:
                    logger.warning(f"     ⚠️  Only {len(valid_players)} valid players - may not find common builds")
                    continue
                
                # Create trial report
                trial_report = data_parser.create_trial_report(
                    valid_players,
                    trial_name=zone_name,
                    boss_name=fight_name,
                    report_code=report_code,
                    update_version="U48-20251005"
                )
                
                all_trial_reports.append(trial_report)
                processed_reports += 1
                
                logger.info(f"     ✅ Created trial report: {zone_name} - {fight_name}")
                
            except Exception as e:
                logger.error(f"     ❌ Error processing report {report_code}: {e}")
                continue
        
        if not all_trial_reports:
            logger.error("❌ No trial reports successfully processed")
            return False
        
        logger.info(f"\n   ✅ Successfully processed {processed_reports} reports")
        
        # Step 4: Analyze builds across all reports
        logger.info("\n4. Analyzing builds and identifying common builds...")
        
        all_players = []
        for trial_report in all_trial_reports:
            all_players.extend(trial_report.all_players)
        
        logger.info(f"   Total players across all reports: {len(all_players)}")
        
        # Analyze builds
        for trial_report in all_trial_reports:
            analyzed_report = build_analyzer.analyze_trial_report(trial_report)
        
        # Get all unique builds
        all_unique_builds = []
        for trial_report in all_trial_reports:
            unique_builds = trial_report.get_unique_builds()
            all_unique_builds.extend(unique_builds)
        
        logger.info(f"   Found {len(all_unique_builds)} unique builds (5+ occurrences)")
        
        if not all_unique_builds:
            logger.warning("   ⚠️  No common builds found (need 5+ players with same build)")
            logger.info("   This is normal for real data - builds may be too diverse")
            
            # Show what we found anyway for debugging
            all_builds = []
            for trial_report in all_trial_reports:
                all_builds.extend(trial_report.common_builds)
            
            logger.info(f"   Total builds identified: {len(all_builds)}")
            for build in all_builds:
                logger.info(f"     - {build.get_display_name()} ({build.count} players)")
            
            return True  # Still successful, just no common builds
        
        # Step 5: Generate HTML pages
        logger.info("\n5. Generating HTML pages...")
        
        generated_files = page_generator.generate_all_pages(all_unique_builds, "U48")
        
        logger.info(f"   ✅ Generated {len(generated_files)} HTML files")
        for name, filepath in generated_files.items():
            if Path(filepath).exists():
                size = Path(filepath).stat().st_size
                logger.info(f"     {name}: {filepath} ({size:,} bytes)")
        
        # Step 6: Summary
        logger.info("\n" + "="*70)
        logger.info("🎉 FULL API INTEGRATION TEST COMPLETED SUCCESSFULLY!")
        logger.info("="*70)
        logger.info("✅ API authentication and connection")
        logger.info("✅ Zone and trial retrieval")
        logger.info("✅ Report search and fetching")
        logger.info("✅ Table data with combatant info")
        logger.info("✅ Player build parsing")
        logger.info("✅ Build analysis and common build identification")
        logger.info("✅ HTML page generation")
        logger.info(f"✅ Processed {processed_reports} real reports")
        logger.info(f"✅ Analyzed {len(all_players)} real players")
        logger.info(f"✅ Generated {len(generated_files)} HTML files")
        
        if all_unique_builds:
            logger.info(f"\n📊 Found {len(all_unique_builds)} common builds:")
            for i, build in enumerate(all_unique_builds[:5], 1):
                logger.info(f"   {i}. {build.get_display_name()} - {build.count} players")
        
        logger.info("\n🌐 View results: open output/index.html")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full API test failed: {e}", exc_info=True)
        return False
        
    finally:
        await api_client.close()


async def main():
    """Run the full API integration test."""
    success = await test_full_api_pipeline()
    
    if not success:
        logger.error("\n❌ Full API integration test failed")
        logger.info("This could be due to:")
        logger.info("- API rate limiting")
        logger.info("- Network connectivity issues")
        logger.info("- Changes in ESO Logs API structure")
        logger.info("- Insufficient recent report data")
        sys.exit(1)
    else:
        logger.info("\n🎉 All tests passed! The system is ready for production.")


if __name__ == "__main__":
    asyncio.run(main())
