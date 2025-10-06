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
    
    async def scan_trial(
        self,
        trial_zone_id: int,
        trial_name: str,
        encounter_id: Optional[int] = None,
        top_n: int = 5
    ) -> List[TrialReport]:
        """
        Scan a specific trial and analyze builds.
        
        Args:
            trial_zone_id: Zone ID for the trial
            trial_name: Name of the trial
            encounter_id: Optional specific encounter/boss ID
            top_n: Number of top logs to fetch (default: 5)
            
        Returns:
            List of TrialReport objects, one per boss fight
        """
        logger.info(f"Scanning trial: {trial_name} (Zone ID: {trial_zone_id})")
        
        try:
            # Get top logs for this trial
            rankings = await self.api_client.get_top_logs(
                zone_id=trial_zone_id,
                encounter_id=encounter_id,
                limit=top_n
            )
            
            if not rankings:
                logger.warning(f"No rankings found for {trial_name}")
                return []
            
            # Process each log
            trial_reports = []
            for ranking in rankings:
                report_code = ranking.get('report', {}).get('code')
                fight_id = ranking.get('report', {}).get('fightID')
                
                if not report_code or not fight_id:
                    continue
                
                try:
                    report = await self._process_report(
                        report_code,
                        fight_id,
                        trial_name
                    )
                    if report:
                        trial_reports.append(report)
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Error processing report {report_code}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error processing report {report_code}: {e}")
                    continue
            
            logger.info(f"Processed {len(trial_reports)} reports for {trial_name}")
            return trial_reports
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error scanning trial {trial_name}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error scanning trial {trial_name}: {e}")
            return []
    
    async def _process_report(
        self,
        report_code: str,
        fight_id: int,
        trial_name: str
    ) -> Optional[TrialReport]:
        """Process a single report to extract builds."""
        logger.info(f"Processing report {report_code}, fight {fight_id}")
        
        # Fetch report data
        report_data = await self.api_client.get_report(report_code)
        if not report_data:
            logger.error(f"Failed to fetch report {report_code}")
            return None
        
        # Get fight info
        fight_info = None
        for fight in report_data.get('fights', []):
            if fight.get('id') == fight_id:
                fight_info = fight
                break
        
        if not fight_info:
            logger.error(f"Fight {fight_id} not found in report")
            return None
        
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
                
                # Scan each encounter
                trial_reports = []
                for encounter in encounters:
                    enc_id = encounter['id']
                    enc_name = encounter['name']
                    
                    logger.info(f"Scanning encounter: {enc_name} (ID: {enc_id})")
                    reports = await self.scan_trial(
                        trial_zone_id=trial_id,
                        trial_name=trial_name,
                        encounter_id=enc_id,
                        top_n=top_n
                    )
                    
                    if reports:
                        trial_reports.extend(reports)
                
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
