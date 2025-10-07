"""
Trial Scanner Module
Orchestrates scanning of ESO Logs trials and building analysis.
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime

from .api_client import ESOLogsAPIClient
from .data_parser import DataParser
from .build_analyzer import BuildAnalyzer
from .models import TrialReport, PlayerBuild, CommonBuild

logger = logging.getLogger(__name__)


class TrialScanner:
    """Scans ESO Logs trials to identify top-performing builds."""
    
    def __init__(self, api_client: Optional[ESOLogsAPIClient] = None, cache_manager=None):
        """
        Initialize the trial scanner.
        
        Args:
            api_client: Optional API client instance
            cache_manager: Optional cache manager instance
        """
        self.api_client = api_client or ESOLogsAPIClient(cache_manager=cache_manager)
        self.data_parser = DataParser()
        self.build_analyzer = BuildAnalyzer()
    
    async def _process_single_fight(
        self,
        report_data: Dict[str, Any],
        report_code: str,
        fight_id: int,
        trial_name: str,
        expected_encounter_name: Optional[str] = None
    ) -> Optional[TrialReport]:
        """
        Process a single fight from an already-fetched report.
        
        Args:
            report_data: Already-fetched report data
            report_code: Report code
            fight_id: Fight ID to process
            trial_name: Name of the trial
            expected_encounter_name: Expected encounter name for validation
            
        Returns:
            TrialReport or None
        """
        logger.info(f"Processing fight {fight_id} from report {report_code}")
        
        # Get fight info
        fight_info = None
        for fight in report_data.get('fights', []):
            if fight.get('id') == fight_id:
                fight_info = fight
                break
        
        if not fight_info:
            logger.error(f"Fight {fight_id} not found in report {report_code}")
            return None
        
        # Validate fight is for the expected encounter
        fight_name = fight_info.get('name', '')
        if expected_encounter_name and fight_name != expected_encounter_name:
            logger.warning(f"Fight {fight_id} is '{fight_name}', expected '{expected_encounter_name}' - skipping")
            return None
        
        logger.info(f"✓ Processing {fight_name} (fight {fight_id})")
        
        # Fetch table data with combatant info - get both Summary (for account names/roles) and DamageDone (for performance)
        summary_data = await self.api_client.get_report_table(
            report_code=report_code,
            start_time=fight_info.get('startTime'),
            end_time=fight_info.get('endTime'),
            data_type="Summary",
            include_combatant_info=True
        )
        
        damage_data = await self.api_client.get_report_table(
            report_code=report_code,
            start_time=fight_info.get('startTime'),
            end_time=fight_info.get('endTime'),
            data_type="DamageDone",
            include_combatant_info=True
        )
        
        if not damage_data:
            logger.error(f"Failed to fetch damage data for report {report_code}")
            return None
        
        # Parse player builds (use damage_data for performance, summary_data for account names/roles)
        players = self.data_parser.parse_report_data(
            report_data,
            damage_data,
            fight_id,
            player_details_data=summary_data
        )
        
        if not players:
            logger.warning(f"No players found in report {report_code}")
            return None
        
        # Filter out players with missing gear or abilities
        valid_players = [
            p for p in players 
            if (p.gear and (p.abilities_bar1 or p.abilities_bar2))
        ]
        
        logger.info(f"Found {len(valid_players)}/{len(players)} valid players")
        
        if not valid_players:
            return None
        
        # Create trial report
        boss_name = fight_info.get('name', 'Unknown Boss')
        trial_report = self.data_parser.create_trial_report(
            valid_players,
            trial_name,
            boss_name,
            report_code,
            update_version=self._get_update_version(report_data)
        )
        
        # Analyze builds
        trial_report = self.build_analyzer.analyze_trial_report(trial_report)
        
        # Fetch mundus data only for best players in each build (much more efficient!)
        logger.info(f"Fetching mundus data for {len(trial_report.common_builds)} build leaders")
        for build in trial_report.common_builds:
            if build.best_player:
                try:
                    # Use character name and player ID for buff queries
                    character_name = build.best_player.character_name
                    source_id = build.best_player.player_id
                    logger.info(f"Querying mundus for character: {character_name} (source ID: {source_id})")
                    
                    mundus_stone = await self.api_client.get_player_buffs(
                        report_code=report_code,
                        fight_ids=[fight_id],
                        player_name=character_name,
                        start_time=fight_info.get('startTime'),
                        end_time=fight_info.get('endTime'),
                        source_id=source_id  # Pass source ID for player-specific filtering
                    )
                    build.best_player.mundus = mundus_stone or ""
                    if mundus_stone:
                        logger.info(f"✓ Found mundus stone for {character_name}: {mundus_stone}")
                    else:
                        logger.warning(f"✗ No mundus stone found for {character_name}")
                except Exception as e:
                    logger.warning(f"Failed to get mundus data for {build.best_player.character_name}: {e}")
                    build.best_player.mundus = ""
        
        return trial_report
    
    def _get_update_version(self, report_data: Dict[str, Any]) -> str:
        """Extract game update version from report data."""
        # Get game version from ESO Logs (e.g., "10.2.5", "10.3.0")
        game_version = report_data.get('gameVersion')
        
        if game_version:
            # ESO game versions are like "10.2.5" (major.minor.patch)
            # Extract major.minor for update number
            try:
                parts = game_version.split('.')
                if len(parts) >= 2:
                    major = int(parts[0])
                    minor = int(parts[1])
                    # ESO updates roughly: major version 10 = Update 40+
                    # Each minor version increment = 1 update
                    # Approximate mapping: 10.x.x -> U(40+x)
                    if major == 10:
                        update_num = 40 + minor
                        return f"u{update_num}"
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse game version {game_version}: {e}")
        
        # Fallback: use date-based estimation
        start_time = report_data.get('startTime', 0)
        if start_time:
            date = datetime.fromtimestamp(start_time / 1000)
            # Return a date-based version if we can't determine the update number
            return f"unknown-{date.strftime('%Y%m%d')}"
        
        return "unknown"
    
    async def scan_all_trials(
        self,
        trial_list: List[Dict[str, Any]],
        top_n: int = 5
    ) -> Dict[str, List[TrialReport]]:
        """
        Scan all trials from a list.
        
        Args:
            trial_list: List of trial dicts with 'id', 'name', 'encounters'
            top_n: Number of top logs per trial
            
        Returns:
            Dictionary mapping trial names to their reports
        """
        logger.info(f"Scanning {len(trial_list)} trials")
        
        # Get zones with encounters first
        logger.info("Fetching zone and encounter data...")
        zones = await self.api_client.get_zones()
        
        all_reports = {}
        
        for trial in trial_list:
            trial_id = trial.get('id')
            trial_name = trial.get('name')
            
            if not trial_id or not trial_name:
                continue
            
            try:
                # Find this trial's zone and get its encounters
                trial_zone = None
                for zone in zones:
                    if zone['id'] == trial_id:
                        trial_zone = zone
                        break
                
                if not trial_zone or not trial_zone.get('encounters'):
                    logger.warning(f"No encounters found for {trial_name}")
                    continue
                
                encounters = trial_zone['encounters']
                logger.info(f"Found {len(encounters)} encounters for {trial_name}")
                
                # Collect top reports for all encounters, then process each report once
                # This is more efficient than fetching the same report multiple times
                logger.info(f"Collecting top reports for {len(encounters)} encounters...")
                
                # Step 1: Get top reports for each encounter
                encounter_reports = {}  # {encounter_id: [(report_code, fight_id, encounter_name), ...]}
                unique_reports = {}  # {report_code: set of (fight_id, encounter_id, encounter_name)}
                
                for encounter in encounters:
                    enc_id = encounter['id']
                    enc_name = encounter['name']
                    
                    logger.info(f"Fetching rankings for: {enc_name} (ID: {enc_id})")
                    top_reports_list = await self.api_client.get_top_logs(
                        zone_id=trial_id,
                        encounter_id=enc_id,
                        limit=top_n
                    )
                    
                    if not top_reports_list:
                        logger.warning(f"No rankings found for {enc_name}")
                        continue
                    
                    # Track reports for this encounter and deduplicate
                    for report_data in top_reports_list:
                        report_code = report_data.get('code')
                        fight_id = report_data.get('fightID')
                        
                        if not report_code or not fight_id:
                            continue
                        
                        # Add to unique reports mapping
                        if report_code not in unique_reports:
                            unique_reports[report_code] = set()
                        unique_reports[report_code].add((fight_id, enc_id, enc_name))
                
                logger.info(f"Found {len(unique_reports)} unique reports across all encounters")
                
                # Step 2: Process each unique report once, extracting all relevant boss fights
                trial_reports = []
                for report_code, fights_set in unique_reports.items():
                    try:
                        # Fetch report once
                        report_data = await self.api_client.get_report(report_code)
                        if not report_data:
                            logger.error(f"Failed to fetch report {report_code}")
                            continue
                        
                        # Process all relevant fights from this report
                        for fight_id, enc_id, enc_name in fights_set:
                            try:
                                report = await self._process_single_fight(
                                    report_data,
                                    report_code,
                                    fight_id,
                                    trial_name,
                                    enc_name
                                )
                                if report:
                                    trial_reports.append(report)
                            except Exception as e:
                                logger.error(f"Error processing fight {fight_id} in report {report_code}: {e}")
                                continue
                    except Exception as e:
                        logger.error(f"Error processing report {report_code}: {e}")
                        continue
                
                if trial_reports:
                    all_reports[trial_name] = trial_reports
                    
            except (KeyError, ValueError, TypeError) as e:
                logger.error(f"Error scanning {trial_name}: {e}")
                continue
            except Exception as e:
                logger.error(f"Unexpected error scanning {trial_name}: {e}")
                continue
        
        logger.info(f"Completed scanning {len(all_reports)} trials")
        return all_reports
    
    def get_publishable_builds(
        self,
        all_reports: Dict[str, List[TrialReport]]
    ) -> List[CommonBuild]:
        """
        Get all publishable builds (common builds that meet role-based thresholds).
        Consolidates builds with the same build_slug across multiple reports.
        
        Args:
            all_reports: Dictionary of trial reports
            
        Returns:
            List of common builds ready to publish
        """
        from collections import defaultdict
        
        # Group builds by (trial_name, boss_name, build_slug) to consolidate duplicates
        build_groups = defaultdict(list)
        
        for trial_name, reports in all_reports.items():
            for report in reports:
                # Get all common builds from this report (not filtered by threshold yet)
                for build in report.common_builds:
                    key = (build.trial_name, build.boss_name, build.build_slug)
                    build_groups[key].append(build)
        
        # Consolidate builds with the same key
        consolidated_builds = []
        for (trial_name, boss_name, build_slug), builds in build_groups.items():
            # Merge all players from all builds with this slug
            all_players = []
            for build in builds:
                all_players.extend(build.all_players)
            
            # Find the best player across all instances
            best_player = max(all_players, key=lambda p: p.dps)
            
            # Preserve mundus from any instance of the same character if available
            if not best_player.mundus:
                for player in all_players:
                    if player.character_name == best_player.character_name and player.mundus:
                        best_player.mundus = player.mundus
                        logger.debug(f"Copied mundus '{player.mundus}' to consolidated best player {best_player.character_name}")
                        break
            
            # Count unique reports
            unique_reports = set(player.report_code for player in all_players if player.report_code)
            
            # Create consolidated build
            consolidated = CommonBuild(
                build_slug=build_slug,
                subclasses=builds[0].subclasses.copy(),
                sets=builds[0].sets.copy(),
                count=len(all_players),
                report_count=len(unique_reports),
                best_player=best_player,
                all_players=all_players,
                trial_name=trial_name,
                boss_name=boss_name,
                fight_id=builds[0].fight_id,
                update_version=builds[0].update_version
            )
            
            # Only include if meets role-based threshold
            if consolidated.meets_threshold():
                consolidated_builds.append(consolidated)
        
        # Sort by count (most popular first)
        consolidated_builds.sort(key=lambda x: x.count, reverse=True)
        
        logger.info(f"Found {len(consolidated_builds)} publishable builds after consolidation")
        return consolidated_builds
    
    async def close(self):
        """Close the API client connection."""
        if self.api_client:
            await self.api_client.close()
