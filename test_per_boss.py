#!/usr/bin/env python3
"""
ESO Build-O-Rama - Multi-Trial Build Analysis
Analyzes builds across all ESO trials, organized by boss encounters with fight-specific DPS.
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
        # First, get the zone data to find the correct encounters for this trial
        logger.info(f"   Fetching encounter list for {trial_name}...")
        zones = await api_client.get_zones()
        
        # Find this trial's zone and get its encounters
        trial_zone = None
        for zone in zones:
            if zone['id'] == trial_id:
                trial_zone = zone
                break
        
        if not trial_zone or not trial_zone.get('encounters'):
            logger.warning(f"      ⚠️  No encounters found for {trial_name}")
            return {}
        
        encounters = trial_zone['encounters']
        logger.info(f"      ✅ Found {len(encounters)} encounters for {trial_name}")
        for enc in encounters:
            logger.info(f"         - {enc['name']} (ID: {enc['id']})")
        
        # Organize players by boss name
        players_by_boss = defaultdict(list)
        processed_reports = set()  # Track which reports we've already processed
        
        # Query rankings for each encounter to get trial-specific reports
        logger.info(f"\n   📊 Fetching top {max_reports} ranked reports per encounter...")
        
        all_rankings = []
        for encounter in encounters:
            enc_id = encounter['id']
            enc_name = encounter['name']
            
            logger.info(f"      Querying encounter: {enc_name} (ID: {enc_id})")
            rankings = await api_client.get_top_logs(
                zone_id=trial_id,
                encounter_id=enc_id,
                limit=max_reports
            )
            
            if rankings:
                logger.info(f"         ✅ Found {len(rankings)} reports")
                all_rankings.extend(rankings)
            else:
                logger.info(f"         ⚠️  No rankings for this encounter")
        
        if not all_rankings:
            logger.warning(f"      ⚠️  No rankings found for any encounter in {trial_name}")
            return {}
        
        logger.info(f"      ✅ Total: {len(all_rankings)} ranked reports across all encounters")
        
        # Process each ranked report
        # Note: We'll process all boss fights (those with difficulty values)
        # No hardcoded boss names - this makes it work for all trials
        for rank_data in all_rankings:
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


async def generate_pages_per_boss(builds_by_boss, trial_name: str = "Aetherian Archive"):
    """Generate HTML pages organized by boss with 3-tier structure."""
    
    logger.info(f"\n📄 Generating pages for {trial_name}...")
    
    page_generator = PageGenerator(
        template_dir="templates",
        output_dir="output"
    )
    
    all_generated_files = {}
    
    # Generate trial page for this trial
    logger.info(f"   Generating trial page for {trial_name}...")
    trial_file = page_generator.generate_trial_page(trial_name, builds_by_boss)
    all_generated_files[f'trial_{trial_name}'] = trial_file
    logger.info(f"   ✅ Generated: {trial_file}")
    
    # Generate build pages
    logger.info(f"   Generating build pages...")
    for boss_name, builds in builds_by_boss.items():
        logger.info(f"      {boss_name}: {len(builds)} builds")
        for build in builds:
            try:
                filepath = page_generator.generate_build_page(build, "U48")
                all_generated_files[build.build_slug] = filepath
            except Exception as e:
                logger.error(f"      Error generating {build.build_slug}: {e}")
    
    return all_generated_files


async def process_single_trial(trial: dict) -> tuple:
    """Process a single trial and return results."""
    trial_name = trial['name']
    trial_id = trial['id']
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🏛️  Processing: {trial_name} (ID: {trial_id})")
    logger.info(f"{'='*60}")
    
    try:
        # Step 1: Fetch data organized by boss
        players_by_boss = await fetch_trial_data_by_boss(
            trial_name=trial_name,
            trial_id=trial_id,
            max_reports=10
        )
        
        if not players_by_boss:
            logger.warning(f"⚠️  No data fetched for {trial_name}")
            return (trial_name, None, {})
        
        # Step 2: Analyze builds per boss
        builds_by_boss = await analyze_builds_per_boss(players_by_boss)
        
        if not builds_by_boss:
            logger.warning(f"⚠️  No builds found for {trial_name}")
            return (trial_name, None, {})
        
        # Step 3: Generate pages for this trial
        generated_files = await generate_pages_per_boss(builds_by_boss, trial_name)
        
        logger.info(f"✅ {trial_name}: {len(builds_by_boss)} bosses, {len(generated_files)} files")
        
        return (trial_name, builds_by_boss, generated_files)
        
    except Exception as e:
        logger.error(f"❌ Error processing {trial_name}: {e}", exc_info=True)
        return (trial_name, None, {})


async def main():
    """Run per-boss build analysis for all trials with parallel processing."""
    
    logger.info("🚀 ESO Build-O-Rama - Multi-Trial Analysis (Parallel)")
    logger.info("="*60)
    
    try:
        # Load trials data
        # Use trials_test.json if it exists (for testing), otherwise use trials.json
        test_file = Path(__file__).parent / "data" / "trials_test.json"
        trials_file = test_file if test_file.exists() else Path(__file__).parent / "data" / "trials.json"
        with open(trials_file, 'r') as f:
            trials_data = json.load(f)
        
        trials = trials_data['trials']
        logger.info(f"📋 Found {len(trials)} trials to process")
        logger.info(f"⚡ Processing 3 trials in parallel for faster execution")
        
        all_trials_data = {}
        total_generated_files = {}
        
        # Process trials in batches of 3 (parallel)
        batch_size = 3
        for i in range(0, len(trials), batch_size):
            batch = trials[i:i+batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(trials) + batch_size - 1) // batch_size
            
            logger.info(f"\n{'='*60}")
            logger.info(f"📦 Processing Batch {batch_num}/{total_batches}: {[t['name'] for t in batch]}")
            logger.info(f"{'='*60}")
            
            # Process batch in parallel
            tasks = [process_single_trial(trial) for trial in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"❌ Batch processing error: {result}")
                    continue
                    
                trial_name, builds_by_boss, generated_files = result
                if builds_by_boss:
                    all_trials_data[trial_name] = builds_by_boss
                    total_generated_files.update(generated_files)
            
            # Add delay between batches to avoid rate limits (except after last batch)
            if batch_num < total_batches:
                delay_seconds = 60  # 1 minute delay between batches
                logger.info(f"\n⏳ Waiting {delay_seconds} seconds before next batch to avoid rate limits...")
                await asyncio.sleep(delay_seconds)
        
        # Step 4: Generate home page with all trials
        if all_trials_data:
            logger.info(f"\n{'='*60}")
            logger.info("📄 Generating home page with all trials...")
            logger.info(f"{'='*60}")
            
            page_generator = PageGenerator(
                template_dir="templates",
                output_dir="output"
            )
            
            home_file = page_generator.generate_home_page(all_trials_data)
            total_generated_files['home'] = home_file
            logger.info(f"✅ Generated: {home_file}")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 MULTI-TRIAL ANALYSIS COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Processed {len(all_trials_data)} trials")
        logger.info(f"✅ Generated {len(total_generated_files)} HTML files")
        
        logger.info("\n📊 Trials Summary:")
        for trial_name, builds_by_boss in all_trials_data.items():
            total_builds = sum(len(builds) for builds in builds_by_boss.values())
            logger.info(f"   {trial_name}: {len(builds_by_boss)} bosses, {total_builds} builds")
        
        logger.info("\n🌐 To view results:")
        logger.info("   open output/index.html")
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
