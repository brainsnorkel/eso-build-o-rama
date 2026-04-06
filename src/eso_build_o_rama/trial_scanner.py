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
    
    def __init__(self, api_client: Optional[ESOLogsAPIClient] = None):
        """
        Initialize the trial scanner.
        
        Args:
            api_client: Optional API client instance
        """
        self.api_client = api_client or ESOLogsAPIClient()
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
            kill = fight.get('kill', False)
            
            # Match by name (exact or prefix to handle combined names like "Z'Maja / Shade of Z'Maja"),
            # has difficulty set, and is a successful kill (not a wipe)
            name_matches = (fight_name == encounter_name
                            or fight_name.startswith(encounter_name + " /")
                            or fight_name.endswith("/ " + encounter_name))
            if name_matches and difficulty and kill:
                duration = fight.get('endTime', 0) - fight.get('startTime', 0)
                matching_fights.append({
                    'id': fight.get('id'),
                    'duration': duration,
                    'fight': fight
                })
        
        if not matching_fights:
            logger.debug(f"No successful kills found for '{encounter_name}'")
            return None
        
        # Return the shortest fight (fastest successful kill)
        shortest = min(matching_fights, key=lambda x: x['duration'])
        logger.info(f"Found {len(matching_fights)} successful kills for {encounter_name}, using fastest (fight {shortest['id']}, {shortest['duration']/1000:.1f}s)")
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
        name_valid = (fight_name == expected_encounter_name
                      or fight_name.startswith(expected_encounter_name + " /")
                      or fight_name.endswith("/ " + expected_encounter_name))
        if expected_encounter_name and not name_valid:
            logger.warning(f"Fight {fight_id} is '{fight_name}', expected '{expected_encounter_name}' - skipping")
            return None
        
        logger.info(f"✓ Processing {fight_name} (fight {fight_id})")
        
        # Special case: Xoryn fight in Lucent Citadel
        # The API lists "Xoryn" as a separate fight, but the real encounter is "Defense Prism"
        # which is a longer fight (trash + mini-bosses + Xoryn boss) at fight_id - 1
        override_boss_name = None
        if trial_name == "Lucent Citadel" and expected_encounter_name == "Xoryn":
            adjusted_fight_id = fight_id - 1
            logger.info(f"⚠️  Xoryn detected - adjusting fight ID from {fight_id} to {adjusted_fight_id} for Defense Prism encounter")

            # Find the adjusted fight
            adjusted_fight_info = None
            for fight in report_data.get('fights', []):
                if fight.get('id') == adjusted_fight_id:
                    adjusted_fight_info = fight
                    break

            if adjusted_fight_info:
                fight_id = adjusted_fight_id
                fight_info = adjusted_fight_info
                override_boss_name = "Defense Prism"
                logger.info(f"✓ Using adjusted fight: {adjusted_fight_info.get('name', 'Unknown')} (fight {adjusted_fight_id})")
            else:
                logger.warning(f"Could not find adjusted fight {adjusted_fight_id} for Xoryn - using original fight {fight_id}")
        
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
        
        # Fetch healing data for HPS calculation
        healing_data = await self.api_client.get_report_table(
            report_code=report_code,
            start_time=fight_info.get('startTime'),
            end_time=fight_info.get('endTime'),
            data_type="Healing",
            include_combatant_info=False
        )
        
        if healing_data:
            logger.info(f"✓ Fetched healing data for {report_code}")
        else:
            logger.warning(f"No healing data available for {report_code}")
        
        # Fetch casts data for CPS calculation
        casts_data = await self.api_client.get_report_table(
            report_code=report_code,
            start_time=fight_info.get('startTime'),
            end_time=fight_info.get('endTime'),
            data_type="Casts",
            include_combatant_info=False
        )
        
        if casts_data:
            logger.info(f"✓ Fetched casts data for {report_code}")
        else:
            logger.warning(f"No casts data available for {report_code}")
        
        # Parse player builds (use damage_data for performance, summary_data for account names/roles)
        players = self.data_parser.parse_report_data(
                report_data,
                damage_data,
                fight_id,
                player_details_data=summary_data,
                healing_data=healing_data,
                casts_data=casts_data
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
        # Use the canonical encounter name when available (fight names can vary,
        # e.g. "Z'Maja / Shade of Z'Maja" vs just "Z'Maja")
        boss_name = override_boss_name if override_boss_name else (
            expected_encounter_name or fight_info.get('name', 'Unknown Boss')
        )
        trial_report = self.data_parser.create_trial_report(
            valid_players,
            trial_name,
            boss_name,
            report_code,
            update_version=self._get_update_version(report_data),
            fight_id=fight_id
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
        
        # Load trial_bosses.json for authoritative boss list
        from pathlib import Path
        import json
        bosses_file = Path(__file__).parent.parent.parent / "data" / "trial_bosses.json"
        with open(bosses_file, 'r') as f:
            trial_bosses_data = json.load(f)
        
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
                        
                        # Track which bosses we've processed
                        processed_bosses = set()
                        
                        # Step 2a: Process each boss encounter from API
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
                                    processed_bosses.add(enc_name)
                            except Exception as e:
                                logger.error(f"Error processing {enc_name} (fight {best_fight['id']}) in report {report_code}: {e}")
                                continue
                        
                        # Step 2b: Process missing bosses from trial_bosses.json
                        # This catches intermediate bosses like Spiral Descender that aren't in API encounters
                        valid_bosses = set(trial_bosses_data.get('trial_bosses', {}).get(trial_name, []))
                        missing_bosses = valid_bosses - processed_bosses
                        
                        if missing_bosses:
                            logger.info(f"Scanning for {len(missing_bosses)} additional boss(es) not in API encounters: {missing_bosses}")
                            
                            for boss_name in missing_bosses:
                                # Find best fight for this boss
                                best_fight = self._find_best_fight_for_encounter(
                                    full_report,
                                    boss_name
                                )
                                
                                if not best_fight:
                                    logger.debug(f"No fights found for {boss_name} in report {report_code}")
                                    continue
                                
                                # Process this boss fight
                                try:
                                    trial_report = await self._process_single_fight(
                                        full_report,
                                        report_code,
                                        best_fight['id'],
                                        trial_name,
                                        boss_name
                                    )
                                    if trial_report:
                                        trial_reports.append(trial_report)
                                        logger.info(f"✓ Processed additional boss: {boss_name}")
                                except Exception as e:
                                    logger.error(f"Error processing {boss_name} (fight {best_fight['id']}) in report {report_code}: {e}")
                                    continue
                        
                        # Step 2c: Process trash fights from this report
                        logger.info(f"Processing trash fights from report {report_code}")
                        trash_fights = self._get_trash_fights(full_report, trial_name)
                        
                        if trash_fights:
                            logger.info(f"Found {len(trash_fights)} trash fights in report {report_code}")
                            
                            # Select representative trash fights (median and longest)
                            selected_trash_fights = self._select_representative_trash_fights(trash_fights)
                            
                            # Process each selected trash fight with boss_name="Trash Builds"
                            for trash_fight in selected_trash_fights:
                                try:
                                    # Process this trash fight (skip name validation)
                                    trial_report = await self._process_single_fight(
                                        full_report,
                                        report_code,
                                        trash_fight['id'],
                                        trial_name,
                                        None  # Skip name validation for trash fights
                                    )
                                    if trial_report:
                                        # Override boss name to consolidate all trash
                                        trial_report.boss_name = "Trash Builds"
                                        # Also update boss names of individual builds
                                        for build in trial_report.common_builds:
                                            build.boss_name = "Trash Builds"
                                        trial_reports.append(trial_report)
                                        logger.info(f"✓ Processed trash fight: Trash Builds (duration: {trash_fight['duration']/1000:.1f}s)")
                                except Exception as e:
                                    logger.error(f"Error processing trash fight {trash_fight['id']} in report {report_code}: {e}")
                                    continue
                        else:
                            logger.info(f"No trash fights found in report {report_code}")
                                
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
        
        # Track mundus for each character to avoid duplicate queries and share results
        # Use character name only (not fight-specific) since mundus is character-wide
        character_mundus_map = {}  # character_name -> mundus_stone
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
            
            character_name = build.best_player.character_name
            
            # If we've already queried this character, use their mundus
            if character_name in character_mundus_map:
                build.best_player.mundus = character_mundus_map[character_name]
                logger.info(f"→ Copied mundus '{character_mundus_map[character_name]}' to {character_name} for {build.boss_name}")
                skipped_queries += 1
                continue
            
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
                    # Only store successful mundus results (not empty strings)
                    character_mundus_map[character_name] = mundus_stone
                    logger.info(f"✓ Found mundus stone for {character_name}: {mundus_stone}")
                    logger.debug(f"  Set mundus '{mundus_stone}' on best_player object id={id(build.best_player)}")
                    successful_queries += 1
                else:
                    # Don't store empty results - let other boss fights try
                    logger.warning(f"✗ No mundus stone found for {character_name} in this fight (will try other bosses)")
                    failed_queries += 1
                    
            except Exception as e:
                logger.warning(f"Failed to get mundus data for {character_name}: {e}")
                build.best_player.mundus = ""
                # Don't store exception results - let other boss fights try
                failed_queries += 1
        
        # Second pass: Copy successful mundus to builds that failed
        # This handles cases where a character fails on one boss but succeeds on another
        backfill_count = 0
        for build in builds:
            if not build.best_player:
                continue
            
            character_name = build.best_player.character_name
            
            # If this build doesn't have mundus but we found it for this character elsewhere
            if not build.best_player.mundus and character_name in character_mundus_map:
                build.best_player.mundus = character_mundus_map[character_name]
                logger.info(f"→ Backfilled mundus '{character_mundus_map[character_name]}' to {character_name} for {build.boss_name}")
                backfill_count += 1
        
        logger.info(
            f"Mundus fetch complete: {successful_queries} successful, "
            f"{failed_queries} failed, {skipped_queries} skipped (already had data), "
            f"{backfill_count} backfilled"
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
                    # For trash builds, consolidate across all fights by using a special key
                    if build.boss_name == "Trash Builds":
                        key = (build.trial_name, "Trash Builds", build.build_slug)
                    else:
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
            
            # Add all consolidated builds (we'll filter by threshold later with DPS fallback)
            consolidated_builds.append(consolidated)
        
        # Sort by count (most popular first)
        consolidated_builds.sort(key=lambda x: x.count, reverse=True)
        
        # Apply threshold filtering with DPS fallback logic
        consolidated_builds = self._apply_threshold_with_dps_fallback(consolidated_builds)
        
        logger.info(f"Found {len(consolidated_builds)} publishable builds after consolidation")
        
        # Apply fallback mechanism for roles with insufficient representation
        consolidated_builds = await self._apply_role_fallback(all_reports, consolidated_builds)
        
        # Filter trash builds to only include DPS
        filtered_builds = []
        for build in consolidated_builds:
            if build.boss_name == "Trash Builds":
                # Only include DPS builds for trash
                if build.best_player and build.best_player.role.lower() == 'dps':
                    filtered_builds.append(build)
            else:
                # Include all roles for boss fights
                filtered_builds.append(build)
        
        consolidated_builds = filtered_builds
        
        # Fetch mundus data for publishable builds only (optimized!)
        await self.fetch_mundus_for_builds(consolidated_builds)
        
        return consolidated_builds
    
    def _apply_threshold_with_dps_fallback(self, builds: List[CommonBuild]) -> List[CommonBuild]:
        """
        Apply threshold filtering with DPS fallback logic.
        
        For DPS builds: If no builds meet the 5+ threshold for a trial/boss,
        include all builds with the highest occurrence count available.
        
        For tank/healer builds: Keep standard threshold (2+ occurrences).
        """
        from collections import defaultdict
        
        # Group builds by (trial_name, boss_name) to apply logic per fight
        builds_by_fight = defaultdict(list)
        for build in builds:
            key = (build.trial_name, build.boss_name)
            builds_by_fight[key].append(build)
        
        publishable_builds = []
        
        for (trial_name, boss_name), fight_builds in builds_by_fight.items():
            # Separate builds by role
            dps_builds = []
            other_builds = []
            
            for build in fight_builds:
                if not build.best_player:
                    continue
                    
                role = build.best_player.role.lower()
                if role == 'dps':
                    dps_builds.append(build)
                else:  # tank, healer, or unknown
                    other_builds.append(build)
            
            # Process DPS builds with fallback logic
            if dps_builds:
                # Check if any DPS builds meet the 5+ threshold
                threshold_meeting_dps = [b for b in dps_builds if b.count >= 5]
                
                if threshold_meeting_dps:
                    # Include all builds that meet threshold
                    publishable_builds.extend(threshold_meeting_dps)
                    logger.debug(f"{trial_name} - {boss_name}: Found {len(threshold_meeting_dps)} DPS builds meeting 5+ threshold")
                else:
                    # No builds meet threshold - find max occurrence count and include all with that count
                    max_count = max((b.count for b in dps_builds), default=0)
                    if max_count > 0:
                        max_count_builds = [b for b in dps_builds if b.count == max_count]
                        publishable_builds.extend(max_count_builds)
                        logger.info(f"{trial_name} - {boss_name}: No DPS builds meet 5+ threshold, using {len(max_count_builds)} build(s) with max occurrence count ({max_count})")
            
            # Process other builds (tank/healer) with standard threshold
            for build in other_builds:
                if build.meets_threshold():
                    publishable_builds.append(build)
        
        return publishable_builds
    
    async def _apply_role_fallback(
        self,
        all_reports: Dict[str, List[TrialReport]],
        consolidated_builds: List[CommonBuild]
    ) -> List[CommonBuild]:
        """
        Apply fallback mechanism for roles with insufficient representation.
        If a fight has < 2 players of a specific role, grab example characters
        from the highest-ranked report for that fight.
        """
        from collections import defaultdict
        
        # Group builds by (trial_name, boss_name) to check role representation per fight
        builds_by_fight = defaultdict(list)
        for build in consolidated_builds:
            key = (build.trial_name, build.boss_name)
            builds_by_fight[key].append(build)
        
        # Check each fight for role representation
        fallback_builds = []
        for (trial_name, boss_name), builds in builds_by_fight.items():
            # Count roles in this fight
            role_counts = defaultdict(int)
            for build in builds:
                if build.best_player:
                    role = build.best_player.role.lower()
                    role_counts[role] += build.count
            
            # Check if we need fallback for healers or tanks
            for role in ['healer', 'tank']:
                if role_counts[role] < 2:
                    logger.info(f"Fight {trial_name} - {boss_name} has only {role_counts[role]} {role}s, applying fallback")
                    
                    # Find the highest-ranked report for this fight
                    highest_ranked_report = None
                    if trial_name in all_reports:
                        # Sort reports by some ranking criteria (e.g., report code or date)
                        sorted_reports = sorted(
                            all_reports[trial_name],
                            key=lambda r: r.report_code,
                            reverse=True
                        )
                        
                        # Find the first report that has this boss
                        for report in sorted_reports:
                            if report.boss_name == boss_name:
                                highest_ranked_report = report
                                break
                    
                    if highest_ranked_report:
                        # Get all players of the missing role from the highest-ranked report
                        role_players = [
                            player for player in highest_ranked_report.all_players
                            if player.role.lower() == role
                        ]
                        
                        if role_players:
                            # Create fallback builds for these players
                            for player in role_players[:2]:  # Limit to 2 examples
                                fallback_build = self._create_fallback_build(player, highest_ranked_report)
                                if fallback_build:
                                    fallback_builds.append(fallback_build)
                                    logger.info(f"Added fallback {role} build: {player.character_name}")
        
        # Combine original builds with fallback builds
        all_builds = consolidated_builds + fallback_builds
        
        # Sort by count (most popular first), with fallback builds at the end
        all_builds.sort(key=lambda x: (x.count, x.trial_name, x.boss_name), reverse=True)
        
        logger.info(f"Added {len(fallback_builds)} fallback builds, total: {len(all_builds)}")
        return all_builds
    
    def _create_fallback_build(self, player: 'PlayerBuild', report: 'TrialReport') -> Optional['CommonBuild']:
        """Create a fallback CommonBuild from a single player."""
        try:
            # Generate build slug for this player
            build_slug = player.get_build_slug()
            
            # Convert sets_equipped dict to list format for CommonBuild
            sets_list = []
            if player.sets_equipped:
                # Get the two most common sets (same logic as in _create_common_build)
                sorted_sets = sorted(player.sets_equipped.items(), key=lambda x: x[1], reverse=True)
                for set_name, count in sorted_sets[:2]:
                    if count >= 2:  # MINIMUM_SET_PIECES from BuildAnalyzer
                        sets_list.append(set_name)
            
            # Create a CommonBuild with count=1 to indicate it's a fallback
            fallback_build = CommonBuild(
                build_slug=build_slug,
                subclasses=player.subclasses.copy(),
                sets=sets_list,
                count=1,  # Mark as fallback
                report_count=1,
                best_player=player,
                all_players=[player],
                trial_name=report.trial_name,
                boss_name=report.boss_name,
                fight_id=report.fight_id,
                update_version=report.update_version,
                report_code=report.report_code
            )
            
            return fallback_build
        except Exception as e:
            logger.error(f"Error creating fallback build for {player.character_name}: {e}")
            return None
    
    def _get_trash_fights(self, report_data: Dict[str, Any], trial_name: str) -> List[Dict[str, Any]]:
        """
        Get trash fights between first and last known boss for the trial.
        Returns list of fight dicts sorted by duration.
        """
        # Skip trials with insignificant/no trash
        if trial_name in ['Asylum Sanctorium', 'Cloudrest']:
            return []
        
        fights = report_data.get('fights', [])
        
        # Load boss order from trial_bosses.json
        import json
        import os
        
        # Get the path to trial_bosses.json
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        bosses_file = os.path.join(current_dir, 'data', 'trial_bosses.json')
        
        try:
            with open(bosses_file, 'r') as f:
                bosses_data = json.load(f)
                trial_bosses = bosses_data.get('trial_bosses', {}).get(trial_name, [])
        except (FileNotFoundError, KeyError):
            logger.warning(f"Could not load boss data for {trial_name}, skipping trash filtering")
            return []
        
        if not trial_bosses:
            logger.warning(f"No boss data found for {trial_name}, skipping trash filtering")
            return []
        
        # Find first and last boss fight IDs in this report
        first_boss_name = trial_bosses[0]
        last_boss_name = trial_bosses[-1]
        
        first_boss_fight_id = None
        last_boss_fight_id = None
        
        for fight in fights:
            fight_name = fight.get('name', '')
            if fight_name == first_boss_name and fight.get('difficulty'):
                first_boss_fight_id = fight.get('id')
            elif fight_name == last_boss_name and fight.get('difficulty'):
                last_boss_fight_id = fight.get('id')
        
        if first_boss_fight_id is None or last_boss_fight_id is None:
            logger.warning(f"Could not find boss bounds for {trial_name} (first: {first_boss_name}, last: {last_boss_name}), skipping trash filtering")
            return []
        
        # Filter trash fights to only those between first and last boss
        trash_fights = []
        for fight in fights:
            fight_id = fight.get('id')
            # Trash fights don't have difficulty field and should be kills
            # AND must be between first and last boss fight IDs
            if (not fight.get('difficulty') and 
                fight.get('kill') is not False and
                first_boss_fight_id <= fight_id <= last_boss_fight_id):
                duration = fight.get('endTime', 0) - fight.get('startTime', 0)
                trash_fights.append({
                    'id': fight_id,
                    'name': fight.get('name', 'Trash'),
                    'duration': duration,
                    'fight': fight
                })
        
        logger.info(f"Found {len(trash_fights)} trash fights between {first_boss_name} and {last_boss_name} for {trial_name}")
        return sorted(trash_fights, key=lambda x: x['duration'])
    
    def _select_representative_trash_fights(
        self, 
        trash_fights: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Select median and longest trash fights for analysis.
        Returns up to 2 fights (median and longest).
        """
        if not trash_fights:
            return []
        
        if len(trash_fights) == 1:
            return [trash_fights[0]]
        
        # Get median (middle fight by duration)
        median_idx = len(trash_fights) // 2
        median_fight = trash_fights[median_idx]
        
        # Get longest
        longest_fight = trash_fights[-1]
        
        # Return both if different, otherwise just one
        if median_fight['id'] != longest_fight['id']:
            return [median_fight, longest_fight]
        return [median_fight]
    
    async def close(self):
        """Close the API client connection."""
        if self.api_client:
            await self.api_client.close()
