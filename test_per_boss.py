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


async def fetch_trial_data_by_boss(trial_name: str = "Aetherian Archive", trial_id: int = 1, max_reports: int = 10):
    """Fetch data organized by boss encounter."""
    
    logger.info(f"Fetching data for {trial_name} (ID: {trial_id}) organized by boss")
    
    api_client = ESOLogsAPIClient()
    data_parser = DataParser()
    
    try:
        # Get top ranked reports using the rankings API (with leaderboard: LogsOnly)
        # We need to query per encounter to get truly top-ranked reports
        logger.info(f"   Fetching top {max_reports} RANKED reports per encounter (increased from 5 to 10)...")
        
        # For Aetherian Archive, only encounter 4 has rankings (overall trial)
        # We'll fetch reports from encounter 4 and then process individual boss fights within them
        logger.info(f"\n   📊 Fetching top {max_reports} ranked reports for {trial_name}...")
        
        # Organize players by boss name
        players_by_boss = defaultdict(list)
        processed_reports = set()  # Track which reports we've already processed
        
        # Use get_top_logs which uses leaderboard: LogsOnly
        # For AA, encounter 4 is the only one with rankings
        rankings = await api_client.get_top_logs(
            zone_id=trial_id,
            encounter_id=4,  # Overall trial encounter
            limit=max_reports
        )
        
        if not rankings:
            logger.warning(f"      ⚠️  No rankings found for {trial_name}")
            return {}
        
        logger.info(f"      ✅ Found {len(rankings)} top-ranked reports")
        
        # Boss names we want to analyze (will filter by difficulty in reports)
        target_bosses = {
            "Lightning Storm Atronach",
            "Foundation Stone Atronach",
            "Varlariel",
            "The Mage"
        }
        
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
                
                # Process all boss fights in this report
                for fight in fights:
                    fight_id = fight['id']
                    fight_name = fight['name']
                    
                    # Skip if not a boss fight (bosses have difficulty values, trash doesn't)
                    if fight.get('difficulty') is None:
                        continue
                    
                    # Skip if not one of our target bosses
                    if fight_name not in target_bosses:
                        continue
                    
                    logger.info(f"        Processing: {fight_name} (ID: {fight_id})")
                    
                    # Get table data with combatant info - both Summary and DamageDone
                    summary_data = await api_client.get_report_table(
                        report_code=report_code,
                        start_time=fight['startTime'],
                        end_time=fight['endTime'],
                        data_type="Summary",
                        include_combatant_info=True
                    )
                    
                    damage_data = await api_client.get_report_table(
                        report_code=report_code,
                        start_time=fight['startTime'],
                        end_time=fight['endTime'],
                        data_type="DamageDone",
                        include_combatant_info=True
                    )
                    
                    if not damage_data:
                        logger.warning(f"          ⚠️  No damage data")
                        continue
                        
                    # Parse players from this specific fight
                    # Debug: Check damage_data structure
                    logger.info(f"          🔍 Processing report {report_code}, fight {fight_id}: {fight_name}")
                    if hasattr(damage_data, 'report_data'):
                        table = damage_data.report_data.report.table
                        data = table['data']
                        logger.info(f"          🔍 Table data keys: {list(data.keys())}")
                        logger.info(f"          🔍 Has playerDetails: {'playerDetails' in data}")
                        if 'playerDetails' in data:
                            pd = data.get('playerDetails')
                            logger.info(f"          🔍 playerDetails value: {pd}")
                            logger.info(f"          🔍 bool(playerDetails): {bool(pd)}")
                            if pd and isinstance(pd, dict):
                                logger.info(f"          🔍 playerDetails keys: {list(pd.keys())}")
                                if 'dps' in pd:
                                    dps_list = pd.get('dps', [])
                                    logger.info(f"          🔍 dps players: {len(dps_list)}")
                                    if dps_list:
                                        first_dps = dps_list[0]
                                        logger.info(f"          🔍 First DPS player keys: {list(first_dps.keys())[:10]}")
                                        logger.info(f"          🔍 First DPS player dps field: {first_dps.get('dps')}")
                        if 'entries' in data:
                            entries = data.get('entries', [])
                            logger.info(f"          🔍 Entries count: {len(entries)}")
                            if entries:
                                first = entries[0]
                                logger.info(f"          🔍 First entry total: {first.get('total')}, activeTime: {first.get('activeTime')}")
                    
                    players = data_parser.parse_report_data(
                        report_data,
                        damage_data,
                        fight_id,
                        player_details_data=summary_data
                    )
                    
                    if players:
                        # Debug: Check player values BEFORE filtering
                        logger.info(f"          🔍 BEFORE filtering: {len(players)} players")
                        for i, p in enumerate(players[:3]):
                            logger.info(f"            Raw player {i+1}: {p.character_name} - DPS: {p.dps:,} - Role: {getattr(p, 'role', 'Unknown')}")
                        
                        # Filter for valid players
                        valid_players = [
                            p for p in players 
                            if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
                        ]
                        
                        logger.info(f"          ✅ {len(valid_players)} valid players")
                        
                        # Debug: Check player values right after parsing
                        if valid_players:
                            top_dps = max(p.dps for p in valid_players)
                            logger.info(f"          Top DPS in this fight: {top_dps:,}")
                            # Debug: Show first few players' values
                            for i, p in enumerate(valid_players[:3]):
                                logger.info(f"            Player {i+1}: {p.character_name} - DPS: {p.dps:,} - Role: {getattr(p, 'role', 'Unknown')}")
                        
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
        
        # Debug: Check DPS values before creating TrialReport
        logger.info(f"   Top 3 DPS before TrialReport:")
        for p in sorted(unique_players, key=lambda x: x.dps, reverse=True)[:3]:
            logger.info(f"     {p.character_name}: {p.dps:,}")
        
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
        
        # Get builds with role-specific thresholds:
        # - DPS: 4+ occurrences (there are ~8-10 DPS per trial)
        # - Healers/Tanks: 2+ occurrences (there are only 2-3 healers/tanks per trial)
        common_builds = []
        for b in analyzed_report.common_builds:
            if b.best_player and b.best_player.role in ['healer', 'tank']:
                # Lower threshold for healers and tanks
                if b.count >= 2:
                    common_builds.append(b)
            else:
                # Standard threshold for DPS
                if b.count >= 4:
                    common_builds.append(b)
        
        logger.info(f"   Common builds (DPS: 4+, Healer/Tank: 2+): {len(common_builds)}")
        
        if common_builds:
            builds_by_boss[boss_name] = common_builds
            
            # Show top 3
            for i, build in enumerate(common_builds[:3], 1):
                logger.info(f"   {i}. {build.get_display_name()} - {build.count} players")
                logger.info(f"      Sets: {', '.join(build.sets)}")
                if build.best_player:
                    # Debug: Print actual DPS value
                    actual_dps = build.best_player.dps
                    logger.info(f"      Best Player: {build.best_player.character_name}")
                    logger.info(f"      Best DPS: {actual_dps:,} (raw value: {actual_dps})")
                    
                    # Also check all players in this build
                    logger.info(f"      All players in build:")
                    for p in build.all_players[:3]:
                        logger.info(f"        - {p.character_name}: {p.dps:,}")
                else:
                    logger.info(f"      Best Player: None")
        else:
            logger.info(f"   ⚠️  No common builds found for {boss_name}")
    
    return builds_by_boss


async def generate_pages_per_boss(builds_by_boss):
    """Generate HTML pages organized by boss with 3-tier structure."""
    
    logger.info("\n" + "="*60)
    logger.info("Generating Pages (3-Tier Structure)")
    logger.info("="*60)
    
    page_generator = PageGenerator(
        template_dir="templates",
        output_dir="output"
    )
    
    all_generated_files = {}
    
    # Organize builds by trial -> boss
    builds_by_trial = {}
    trial_name = "Aetherian Archive"  # Hardcoded for now
    builds_by_trial[trial_name] = builds_by_boss
    
    # Generate home page
    logger.info("\n📄 Generating home page...")
    home_file = page_generator.generate_home_page(builds_by_trial)
    all_generated_files['home'] = home_file
    logger.info(f"   ✅ Generated: {home_file}")
    
    # Generate trial pages
    for trial_name, bosses in builds_by_trial.items():
        logger.info(f"\n📄 Generating trial page for {trial_name}...")
        trial_file = page_generator.generate_trial_page(trial_name, bosses)
        all_generated_files[f'trial_{trial_name}'] = trial_file
        logger.info(f"   ✅ Generated: {trial_file}")
    
    # Generate build pages
    logger.info("\n📄 Generating build pages...")
    for boss_name, builds in builds_by_boss.items():
        logger.info(f"   {boss_name}: {len(builds)} builds")
        for build in builds:
            try:
                filepath = page_generator.generate_build_page(build, "U48")
                all_generated_files[build.build_slug] = filepath
            except Exception as e:
                logger.error(f"   Error generating {build.build_slug}: {e}")
    
    return all_generated_files


async def main():
    """Run per-boss build analysis."""
    
    logger.info("🚀 ESO Build-O-Rama - Per-Boss Analysis")
    logger.info("="*60)
    
    try:
        # Step 1: Fetch data organized by boss
        players_by_boss = await fetch_trial_data_by_boss(max_reports=10)
        
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
