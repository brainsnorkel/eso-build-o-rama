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
    
    def _find_best_fight_for_encounter(
        self,
        report_data: Dict[str, Any],
        encounter_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find the shortest fight for a specific encounter in a report.
        
        Args:
            report_data: Full report data
            encounter_name: Name of the encounter/boss to find
            
        Returns:
            Fight dict with the shortest duration, or None if no fights found
        """
        fights = report_data.get('fights', [])
        
        # Find all fights for this encounter (with difficulty, which indicates boss fights)
        matching_fights = []
        for fight in fights:
            fight_name = fight.get('name', '')
            difficulty = fight.get('difficulty')
            
            # Match by name and prefer fights with difficulty set (real boss attempts)
            if fight_name == encounter_name and difficulty:
                duration = fight.get('endTime', 0) - fight.get('startTime', 0)
                matching_fights.append({
                    'id': fight.get('id'),
                    'duration': duration,
                    'fight': fight
                })
        
        if not matching_fights:
            logger.debug(f"No fights with difficulty found for '{encounter_name}'")
            return None
        
        # Return the shortest fight (fastest clear)
        shortest = min(matching_fights, key=lambda x: x['duration'])
        logger.info(f"Found {len(matching_fights)} attempts for {encounter_name}, using fastest (fight {shortest['id']}, {shortest['duration']/1000:.1f}s)")
        return shortest['fight']
    
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
        
        # Store fight context in builds for later mundus queries (after consolidation)
        for build in trial_report.common_builds:
            build.report_code = report_code
            build.fight_start_time = fight_info.get('startTime')
            build.fight_end_time = fight_info.get('endTime')
        
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
                
                if not encounters:
                    logger.warning(f"No encounters found for {trial_name}")
                    continue
                
                # Step 1: Get top reports from FINAL BOSS only (represents full trial clears)
                final_boss = encounters[-1]  # Last encounter is the final boss
                final_boss_id = final_boss['id']
                final_boss_name = final_boss['name']
                
                logger.info(f"Getting top reports from final boss: {final_boss_name} (ID: {final_boss_id})")
                top_reports_list = await self.api_client.get_top_logs(
                    zone_id=trial_id,
                    encounter_id=final_boss_id,
                    limit=top_n
                )
                
                if not top_reports_list:
                    logger.warning(f"No rankings found for final boss {final_boss_name}")
                    continue
                
                logger.info(f"Found {len(top_reports_list)} top-ranked reports from {final_boss_name}")
                
                # Step 2: For each top report, extract ALL boss fights from the trial
                trial_reports = []
                for report_data in top_reports_list:
                    report_code = report_data.get('code')
                    
                    if not report_code:
                        continue
                    
                    try:
                        # Fetch full report once
                        full_report = await self.api_client.get_report(report_code)
                        if not full_report:
                            logger.error(f"Failed to fetch report {report_code}")
                            continue
                        
                        logger.info(f"Processing report {report_code} for all bosses")
                        
                        # Process each boss encounter from this report
                        for encounter in encounters:
                            enc_id = encounter['id']
                            enc_name = encounter['name']
                            
                            # Find the shortest/fastest kill for this boss in the report
                            best_fight = self._find_best_fight_for_encounter(
                                full_report,
                                enc_name
                            )
                            
                            if not best_fight:
                                logger.debug(f"No fights found for {enc_name} in report {report_code}")
                                continue
                            
                            # Process this boss fight
                            try:
                                trial_report = await self._process_single_fight(
                                    full_report,
                                    report_code,
                                    best_fight['id'],
                                    trial_name,
                                    enc_name
                                )
                                if trial_report:
                                    trial_reports.append(trial_report)
                            except Exception as e:
                                logger.error(f"Error processing {enc_name} (fight {best_fight['id']}) in report {report_code}: {e}")
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
    
    async def fetch_mundus_for_builds(
        self,
        builds: List[CommonBuild]
    ) -> None:
        """
        Fetch mundus stones for publishable builds only.
        This is much more efficient than querying for every build during fight processing.
        
        Args:
            builds: List of consolidated builds that meet publishing thresholds
        """
        if not builds:
            return
        
        logger.info(f"Fetching mundus data for {len(builds)} publishable builds (optimized)")
        
        # Track which characters we've already queried to avoid duplicates
        queried_characters = set()
        successful_queries = 0
        failed_queries = 0
        skipped_queries = 0
        
        for build in builds:
            if not build.best_player:
                continue
            
            # Skip if this player already has mundus (e.g., from previous consolidation)
            if build.best_player.mundus:
                skipped_queries += 1
                continue
            
            # Create unique key for this character in this report/fight
            character_key = (
                build.best_player.character_name,
                build.report_code,
                build.fight_id
            )
            
            # Skip if we've already queried this character
            if character_key in queried_characters:
                skipped_queries += 1
                continue
            
            queried_characters.add(character_key)
            
            try:
                character_name = build.best_player.character_name
                source_id = build.best_player.player_id
                
                logger.info(f"Querying mundus for {character_name} (source ID: {source_id})")
                
                mundus_stone = await self.api_client.get_player_buffs(
                    report_code=build.report_code,
                    fight_ids=[build.fight_id],
                    player_name=character_name,
                    start_time=build.fight_start_time,
                    end_time=build.fight_end_time,
                    source_id=source_id
                )
                
                build.best_player.mundus = mundus_stone or ""
                
                if mundus_stone:
                    logger.info(f"✓ Found mundus stone for {character_name}: {mundus_stone}")
                    successful_queries += 1
                else:
                    logger.warning(f"✗ No mundus stone found for {character_name}")
                    failed_queries += 1
                    
            except Exception as e:
                logger.warning(f"Failed to get mundus data for {build.best_player.character_name}: {e}")
                build.best_player.mundus = ""
                failed_queries += 1
        
        logger.info(
            f"Mundus fetch complete: {successful_queries} successful, "
            f"{failed_queries} failed, {skipped_queries} skipped (already had data)"
        )
    
    async def get_publishable_builds(
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
            
            # Preserve fight context from first build instance for mundus queries
            first_build = builds[0]
            
            # Create consolidated build
            consolidated = CommonBuild(
                build_slug=build_slug,
                subclasses=first_build.subclasses.copy(),
                sets=first_build.sets.copy(),
                count=len(all_players),
                report_count=len(unique_reports),
                best_player=best_player,
                all_players=all_players,
                trial_name=trial_name,
                boss_name=boss_name,
                fight_id=first_build.fight_id,
                update_version=first_build.update_version,
                report_code=first_build.report_code,
                fight_start_time=first_build.fight_start_time,
                fight_end_time=first_build.fight_end_time
            )
            
            # Only include if meets role-based threshold
            if consolidated.meets_threshold():
                consolidated_builds.append(consolidated)
        
        # Sort by count (most popular first)
        consolidated_builds.sort(key=lambda x: x.count, reverse=True)
        
        logger.info(f"Found {len(consolidated_builds)} publishable builds after consolidation")
        
        # Fetch mundus data for publishable builds only (optimized!)
        await self.fetch_mundus_for_builds(consolidated_builds)
        
        return consolidated_builds
    
    async def close(self):
        """Close the API client connection."""
        if self.api_client:
            await self.api_client.close()
