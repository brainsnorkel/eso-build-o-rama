#!/usr/bin/env python3
"""
Integration test script for ESO Build-O-Rama - Per-Boss Analysis
Tests builds organized by specific boss encounters with fight-specific DPS.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from collections import defaultdict

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


async def fetch_trial_data_by_boss(trial_name: str = "Aetherian Archive", trial_id: int = 1, max_reports: int = 5):
    """Fetch data organized by boss encounter."""
    
    logger.info(f"Fetching data for {trial_name} (ID: {trial_id}) organized by boss")
    
    api_client = ESOLogsAPIClient()
    data_parser = DataParser()
    
    try:
        # Get top ranked reports using the rankings API (with leaderboard: LogsOnly)
        # We need to query per encounter to get truly top-ranked reports
        logger.info(f"   Fetching top {max_reports} RANKED reports per encounter...")
        
        # Aetherian Archive encounter IDs (from trials.json or API)
        encounters = {
            1: "Frost Atronach",
            2: "Firstmage Chainspinner", 
            3: "Lightning Storm Atronach",
            4: "Firstmage Nullifier",
            5: "Foundation Stone Atronach",
            6: "Firstmage Overcharger",
            7: "Varlariel",
            8: "The Mage"
        }
        
        # Organize players by boss name
        players_by_boss = defaultdict(list)
        processed_reports = set()  # Track which reports we've already processed
        
        # Get top ranked reports for each encounter
        for encounter_id, boss_name in encounters.items():
            logger.info(f"\n   📊 Fetching top ranked reports for {boss_name} (encounter {encounter_id})...")
            
            # Use get_top_logs which uses leaderboard: LogsOnly
            rankings = await api_client.get_top_logs(
                zone_id=trial_id,
                encounter_id=encounter_id,
                limit=max_reports
            )
            
            if not rankings:
                logger.warning(f"      ⚠️  No rankings found for {boss_name}")
                continue
            
            logger.info(f"      ✅ Found {len(rankings)} top-ranked reports")
            
            # Process each ranked report
            for rank_data in rankings:
                report_info = rank_data.get('report', {})
                report_code = report_info.get('code')
                
                if not report_code:
                    continue
                
                # Skip if we've already processed this report
                if report_code in processed_reports:
                    continue
                
                processed_reports.add(report_code)
                logger.info(f"      Processing report: {report_code}")
                
                try:
                    # Get report details
                    report_data = await api_client.get_report(report_code)
                    
                    if not report_data or not report_data.get('fights'):
                        logger.warning(f"        ⚠️  No fights in report {report_code}")
                        continue
                    
                    fights = report_data.get('fights', [])
                    logger.info(f"        Found {len(fights)} fights")
                    
                    # Only process fights for the CURRENT boss we're analyzing
                    for fight in fights:
                        fight_id = fight['id']
                        fight_name = fight['name']
                        
                        # Skip if not the boss we're looking for
                        if fight_name != boss_name:
                            continue
                        
                        logger.info(f"        Processing: {fight_name} (ID: {fight_id})")
                        
                        # Get table data with combatant info
                        table_data = await api_client.get_report_table(
                            report_code=report_code,
                            start_time=fight['startTime'],
                            end_time=fight['endTime'],
                            data_type="Summary",
                            include_combatant_info=True
                        )
                        
                        if not table_data:
                            logger.warning(f"          ⚠️  No table data")
                            continue
                        
                        # Parse players from this specific fight
                        players = data_parser.parse_report_data(
                            report_data,
                            table_data,
                            fight_id
                        )
                        
                        if players:
                            # Filter for valid players
                            valid_players = [
                                p for p in players 
                                if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
                            ]
                            
                            logger.info(f"          ✅ {len(valid_players)} valid players")
                            
                            # Add to boss-specific list
                            players_by_boss[fight_name].extend(valid_players)
                        else:
                            logger.warning(f"          ⚠️  No players parsed")
                    
                except Exception as e:
                    logger.error(f"        ❌ Error: {e}")
                    continue
        
        # Log summary
        logger.info(f"\n   ✅ Collected data for {len(players_by_boss)} bosses:")
        for boss_name, players in players_by_boss.items():
            logger.info(f"      - {boss_name}: {len(players)} player entries")
        
        return dict(players_by_boss)
        
    except Exception as e:
        logger.error(f"   ❌ Error fetching trial data: {e}")
        return {}
    
    finally:
        await api_client.close()


async def analyze_builds_per_boss(players_by_boss):
    """Analyze builds for each boss separately."""
    
    logger.info("\n" + "="*60)
    logger.info("Analyzing Builds Per Boss")
    logger.info("="*60)
    
    analyzer = BuildAnalyzer()
    builds_by_boss = {}
    
    for boss_name, players in players_by_boss.items():
        logger.info(f"\n📊 Analyzing {boss_name}:")
        logger.info(f"   Players: {len(players)}")
        
        # Deduplicate players for this boss (keep highest DPS per player/character)
        player_map = {}
        for player in players:
            key = f"{player.player_name}|{player.character_name}"
            if key not in player_map:
                player_map[key] = player
            else:
                # Keep the one with higher DPS
                if player.dps > player_map[key].dps:
                    player_map[key] = player
        
        unique_players = list(player_map.values())
        logger.info(f"   Unique players: {len(unique_players)}")
        
        # Create trial report for this boss
        trial_report = TrialReport(
            trial_name="Aetherian Archive",
            boss_name=boss_name,
            all_players=unique_players,
            report_code="REAL_API_DATA",
            update_version="U48"
        )
        
        # Analyze builds
        analyzed_report = analyzer.analyze_trial_report(trial_report)
        
        # Get builds with 2+ occurrences
        common_builds = [b for b in analyzed_report.common_builds if b.count >= 2]
        
        logger.info(f"   Common builds (2+): {len(common_builds)}")
        
        if common_builds:
            builds_by_boss[boss_name] = common_builds
            
            # Show top 3
            for i, build in enumerate(common_builds[:3], 1):
                logger.info(f"   {i}. {build.get_display_name()} - {build.count} players")
                logger.info(f"      Sets: {', '.join(build.sets)}")
                logger.info(f"      Best DPS: {build.best_player.dps:,}")
        else:
            logger.info(f"   ⚠️  No common builds found for {boss_name}")
    
    return builds_by_boss


async def generate_pages_per_boss(builds_by_boss):
    """Generate HTML pages organized by boss."""
    
    logger.info("\n" + "="*60)
    logger.info("Generating Pages Per Boss")
    logger.info("="*60)
    
    page_generator = PageGenerator(
        template_dir="templates",
        output_dir="output"
    )
    
    all_generated_files = {}
    
    for boss_name, builds in builds_by_boss.items():
        logger.info(f"\n📄 Generating pages for {boss_name}:")
        logger.info(f"   Builds: {len(builds)}")
        
        # Generate pages for this boss
        generated_files = page_generator.generate_all_pages(
            builds,
            update_version=f"U48-{boss_name.replace(' ', '-')}"
        )
        
        logger.info(f"   ✅ Generated {len(generated_files)} files")
        
        # Add to overall collection
        for name, filepath in generated_files.items():
            key = f"{boss_name}_{name}"
            all_generated_files[key] = filepath
    
    return all_generated_files


async def main():
    """Run per-boss build analysis."""
    
    logger.info("🚀 ESO Build-O-Rama - Per-Boss Analysis")
    logger.info("="*60)
    
    try:
        # Step 1: Fetch data organized by boss
        players_by_boss = await fetch_trial_data_by_boss(max_reports=5)
        
        if not players_by_boss:
            logger.error("❌ No data fetched")
            return
        
        # Step 2: Analyze builds per boss
        builds_by_boss = await analyze_builds_per_boss(players_by_boss)
        
        if not builds_by_boss:
            logger.error("❌ No builds found")
            return
        
        # Step 3: Generate pages
        generated_files = await generate_pages_per_boss(builds_by_boss)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 PER-BOSS ANALYSIS COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Analyzed {len(builds_by_boss)} bosses")
        logger.info(f"✅ Generated {len(generated_files)} HTML files")
        
        logger.info("\n📁 Generated Files:")
        for name, filepath in generated_files.items():
            logger.info(f"   {filepath}")
        
        logger.info("\n🌐 To view results:")
        logger.info("   open output/index.html")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
