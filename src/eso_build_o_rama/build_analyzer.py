"""
Build Analysis Module
Analyzes player builds to identify common builds and create build slugs.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter

from .models import PlayerBuild, CommonBuild, TrialReport
from .subclass_analyzer import ESOSubclassAnalyzer

logger = logging.getLogger(__name__)


class BuildAnalyzer:
    """Analyzes player builds to identify common patterns."""
    
    # Constants for build analysis
    MINIMUM_SET_PIECES = 4  # Minimum pieces for a meaningful set bonus
    MINIMUM_COMMON_BUILD_OCCURRENCES = 5  # Minimum occurrences for DPS builds
    MINIMUM_HEALER_TANK_BUILD_OCCURRENCES = 3  # Minimum occurrences for healer and tank builds
    MAX_SUBCLASSES = 3  # Maximum number of subclasses per character
    
    def __init__(self):
        """Initialize the build analyzer."""
        self.subclass_analyzer = ESOSubclassAnalyzer()
    
    def analyze_trial_report(self, trial_report: TrialReport) -> TrialReport:
        """
        Analyze a trial report to identify common builds.
        
        Args:
            trial_report: TrialReport object with all players
            
        Returns:
            Updated TrialReport with common builds identified
        """
        # Input validation
        if not isinstance(trial_report, TrialReport):
            raise TypeError("trial_report must be a TrialReport object")
        if not trial_report.all_players:
            raise ValueError("trial_report must contain players")
        logger.info(f"Analyzing {len(trial_report.all_players)} players for trial {trial_report.trial_name}")
        
        # Analyze each player's build
        for player in trial_report.all_players:
            self._analyze_player_build(player)
        
        # Group players by build slug
        build_groups = self._group_players_by_build(trial_report.all_players)
        
        # Create build objects for ALL builds, then filter by role-specific minimums
        all_builds = []
        for build_slug, players in build_groups.items():
            common_build = self._create_common_build(build_slug, players, trial_report)
            all_builds.append(common_build)
        
        # Sort by count (most common first)
        all_builds.sort(key=lambda x: x.count, reverse=True)
        
        # Return ALL builds without filtering
        # Filtering will be done after consolidation in get_publishable_builds()
        # This allows builds to accumulate across multiple reports before threshold check
        trial_report.common_builds = all_builds
        logger.info(f"Found {len(all_builds)} builds from this fight (pre-consolidation)")
        
        return trial_report
    
    def _analyze_player_build(self, player: PlayerBuild) -> None:
        """Analyze a single player's build."""
        # Debug: Check DPS before analysis
        dps_before = player.dps
        
        # Extract ability names for subclass analysis
        all_abilities = []
        for ability in player.abilities_bar1 + player.abilities_bar2:
            if ability.ability_name:
                all_abilities.append(ability.ability_name)
        
        # Determine subclasses (only if not already set)
        if not player.subclasses and all_abilities:
            player.subclasses = self.subclass_analyzer.analyze_subclasses(all_abilities)
        elif not player.subclasses:
            player.subclasses = ['x', 'x', 'x']
        
        # Analyze gear sets (only if not already analyzed)
        if not player.sets_equipped:
            self._analyze_gear_sets(player)
        
        # Generate build slug
        build_slug = player.get_build_slug()
        
        # Debug: Check if DPS changed
        if player.dps != dps_before:
            logger.warning(f"DPS CHANGED for {player.character_name}: {dps_before:,} -> {player.dps:,}")
        
        logger.debug(f"Player {player.character_name}: {build_slug} (DPS: {player.dps:,})")
    
    def _normalize_set_name(self, set_name: str) -> str:
        """
        Normalize set name for counting purposes.
        Treats 'Perfected {set name}' and '{set name}' as the same set.
        Returns the normalized name for counting and the original name for display.
        """
        if not set_name:
            return set_name
        
        # Remove 'Perfected ' prefix for counting purposes
        if set_name.startswith('Perfected '):
            return set_name[10:]  # Remove 'Perfected ' prefix
        return set_name
    
    def _get_preferred_set_name(self, set_names: List[str]) -> str:
        """
        Get the preferred set name for display.
        Prefers 'Perfected {set name}' over '{set name}' when both exist.
        """
        if not set_names:
            return ""
        
        # Check if any set name has 'Perfected' prefix
        perfected_names = [name for name in set_names if name.startswith('Perfected ')]
        if perfected_names:
            return perfected_names[0]  # Return first perfected name
        
        # Otherwise return the first name
        return set_names[0]
    
    def _analyze_gear_sets(self, player: PlayerBuild) -> None:
        """Analyze gear to determine set counts per bar."""
        # Count sets for each bar (using normalized names for counting)
        bar1_sets = defaultdict(int)
        bar2_sets = defaultdict(int)
        total_sets = defaultdict(int)
        
        # Track original set names for display purposes
        set_name_mapping = defaultdict(list)  # normalized_name -> [original_names]
        
        for gear in player.gear:
            if gear.set_name and gear.set_name.strip():
                original_set_name = gear.set_name.strip()
                normalized_set_name = self._normalize_set_name(original_set_name)
                
                # Track original names for this normalized set
                set_name_mapping[normalized_set_name].append(original_set_name)
                
                # Always add to total count (for "Sets Used" display)
                total_sets[normalized_set_name] += 1
                
                # Skip mythics and arena weapons from bar-specific set counts (they don't contribute to 5-piece bonuses)
                if self._is_mythic_item(gear.item_name) or self._is_arena_weapon(gear.item_name):
                    continue
                
                # Add to appropriate bar count
                if gear.bar == 1:
                    bar1_sets[normalized_set_name] += 1
                elif gear.bar == 2:
                    bar2_sets[normalized_set_name] += 1
                else:
                    # If bar is not specified, assume bar 1
                    bar1_sets[normalized_set_name] += 1
        
        # Handle 2H weapons and staves (count as 2 pieces)
        for gear in player.gear:
            if gear.slot in ['main_hand', 'backup_main_hand']:
                # Check if it's a 2H weapon or staff
                if self._is_two_handed_weapon(gear.item_name):
                    if gear.set_name and gear.set_name.strip():
                        original_set_name = gear.set_name.strip()
                        normalized_set_name = self._normalize_set_name(original_set_name)
                        
                        # Track original names for this normalized set
                        set_name_mapping[normalized_set_name].append(original_set_name)
                        
                        # Always add to total count (for "Sets Used" display)
                        total_sets[normalized_set_name] += 1
                        
                        # Skip arena weapons from bar-specific counts (they don't contribute to 5-piece bonuses)
                        if self._is_arena_weapon(gear.item_name):
                            continue
                        
                        # Add extra count for 2H weapons (they count as 2 pieces for set bonuses)
                        if gear.bar == 1 or gear.bar == 0:
                            bar1_sets[normalized_set_name] += 1  # Already counted 1, add 1 more
                        elif gear.bar == 2:
                            bar2_sets[normalized_set_name] += 1
        
        # Convert normalized counts back to preferred display names
        final_total_sets = {}
        final_bar1_sets = {}
        final_bar2_sets = {}
        
        for normalized_name, count in total_sets.items():
            preferred_name = self._get_preferred_set_name(set_name_mapping[normalized_name])
            final_total_sets[preferred_name] = count
        
        for normalized_name, count in bar1_sets.items():
            preferred_name = self._get_preferred_set_name(set_name_mapping[normalized_name])
            final_bar1_sets[preferred_name] = count
        
        for normalized_name, count in bar2_sets.items():
            preferred_name = self._get_preferred_set_name(set_name_mapping[normalized_name])
            final_bar2_sets[preferred_name] = count
        
        player.sets_equipped = final_total_sets
        player.sets_bar1 = final_bar1_sets
        player.sets_bar2 = final_bar2_sets
        
        logger.debug(f"Sets for {player.character_name}: {final_total_sets}")
    
    def _is_two_handed_weapon(self, item_name: str) -> bool:
        """Check if an item is a 2H weapon or staff."""
        if not item_name:
            return False
        
        two_handed_keywords = [
            'greatsword', 'battleaxe', 'warhammer', 'bow', 'staff',
            'inferno staff', 'ice staff', 'lightning staff', 'restoration staff'
        ]
        
        item_lower = item_name.lower()
        return any(keyword in item_lower for keyword in two_handed_keywords)
    
    def _is_mythic_item(self, item_name: str) -> bool:
        """Check if an item is a mythic item."""
        if not item_name:
            return False
        
        mythic_keywords = [
            'oakensoul', 'death dealer\'s fete', 'pale order', 'wild hunt',
            'gaze of sithis', 'malacath\'s band', 'mythic', 'ring of',
            'band of', 'amulet of', 'necklace of', 'huntsman\'s warmask'
        ]
        
        item_lower = item_name.lower()
        return any(keyword in item_lower for keyword in mythic_keywords)
    
    def _is_arena_weapon(self, item_name: str) -> bool:
        """Check if an item is an arena weapon."""
        if not item_name:
            return False
        
        arena_keywords = [
            'maelstrom\'s', 'vateshran\'s', 'dragonstar arena',
            'brp', 'blackrose prison', 'imperial city prison',
            'vateshran hollows', 'maelstrom arena'
        ]
        
        item_lower = item_name.lower()
        return any(keyword in item_lower for keyword in arena_keywords)
    
    def _group_players_by_build(self, players: List[PlayerBuild]) -> Dict[str, List[PlayerBuild]]:
        """Group players by their build slug."""
        build_groups = defaultdict(list)
        
        for player in players:
            build_slug = player.get_build_slug()
            build_groups[build_slug].append(player)
        
        return dict(build_groups)
    
    def _create_common_build(self, build_slug: str, players: List[PlayerBuild], trial_report: TrialReport) -> CommonBuild:
        """Create a CommonBuild object from a group of players."""
        # Debug: Check DPS values before selecting best
        logger.debug(f"Creating common build for {build_slug} with {len(players)} players")
        for p in players[:3]:
            logger.debug(f"  {p.character_name}: DPS={p.dps:,}")
        
        # Find the highest DPS player
        best_player = max(players, key=lambda p: p.dps)
        logger.debug(f"Selected best player: {best_player.character_name} with DPS={best_player.dps:,}")
        
        # Extract build components from the best player
        subclasses = best_player.subclasses.copy()
        sets = []
        
        # Get the two most common sets
        sorted_sets = sorted(best_player.sets_equipped.items(), key=lambda x: x[1], reverse=True)
        for set_name, count in sorted_sets[:2]:
            if count >= self.MINIMUM_SET_PIECES:  # Only include if it's a meaningful set
                sets.append(set_name)
        
        # Count unique reports
        unique_reports = set(player.report_code for player in players if player.report_code)
        
        # Create common build
        common_build = CommonBuild(
            build_slug=build_slug,
            subclasses=subclasses,
            sets=sets,
            count=len(players),
            report_count=len(unique_reports),
            best_player=best_player,
            all_players=players.copy(),
            trial_name=trial_report.trial_name,
            boss_name=trial_report.boss_name,
            fight_id=trial_report.fight_id,
            update_version=trial_report.update_version
        )
        
        return common_build
    
    def get_build_statistics(self, trial_report: TrialReport) -> Dict[str, Any]:
        """Get statistics about builds in the trial report."""
        stats = {
            'total_players': len(trial_report.all_players),
            'common_builds_count': len(trial_report.common_builds),
            'unique_builds': len(set(player.get_build_slug() for player in trial_report.all_players)),
            'subclass_distribution': self._get_subclass_distribution(trial_report.all_players),
            'set_distribution': self._get_set_distribution(trial_report.all_players)
        }
        
        return stats
    
    def _get_subclass_distribution(self, players: List[PlayerBuild]) -> Dict[str, int]:
        """Get distribution of subclass combinations."""
        subclass_counts = Counter()
        
        for player in players:
            if player.subclasses:
                subclass_combo = '/'.join(player.subclasses)
                subclass_counts[subclass_combo] += 1
        
        return dict(subclass_counts)
    
    def _get_set_distribution(self, players: List[PlayerBuild]) -> Dict[str, int]:
        """Get distribution of sets across all players."""
        set_counts = Counter()
        
        for player in players:
            for set_name, count in player.sets_equipped.items():
                if count >= self.MINIMUM_SET_PIECES:  # Only count meaningful sets
                    set_counts[set_name] += count
        
        return dict(set_counts)
    
    def aggregate_builds_across_trials(self, all_builds: List[CommonBuild]) -> Dict[str, List[CommonBuild]]:
        """
        Aggregate builds across all trials by role and build signature.
        Returns up to 5 most common builds per role, plus trash builds.
        
        Args:
            all_builds: List of all CommonBuild objects from all trials
            
        Returns:
            Dictionary mapping role names to lists of aggregated builds
        """
        logger.info(f"Aggregating {len(all_builds)} builds across all trials")
        
        # Separate trash builds from boss builds
        boss_builds = []
        trash_builds = []
        
        for build in all_builds:
            if build.boss_name == "Trash Builds":
                trash_builds.append(build)
            else:
                boss_builds.append(build)
        
        logger.info(f"Found {len(boss_builds)} boss builds and {len(trash_builds)} trash builds")
        
        # Group boss builds by role and build signature
        role_builds = defaultdict(lambda: defaultdict(list))
        
        for build in boss_builds:
            if not build.best_player:
                continue
                
            role = build.best_player.role.lower()
            build_slug = build.build_slug
            
            # Group by role and build signature
            role_builds[role][build_slug].append(build)
        
        # Aggregate boss builds for each role
        aggregated_by_role = {}
        
        for role, builds_by_slug in role_builds.items():
            aggregated_builds = []
            
            for build_slug, builds in builds_by_slug.items():
                # Aggregate data across trials
                total_players = sum(build.count for build in builds)
                total_reports = sum(build.report_count for build in builds)
                
                # Collect all trials where this build appears
                trials_appeared = list(set(build.trial_name for build in builds))
                
                # Find the highest metric player across all trials
                best_player = None
                best_metric = 0
                best_player_build = None
                
                for build in builds:
                    if build.best_player:
                        metric = build.best_player.get_primary_metric()
                        if metric > best_metric:
                            best_metric = metric
                            best_player = build.best_player
                            best_player_build = build
                
                if best_player and best_player_build:
                    # Create aggregated build with original trial/boss info for linking
                    aggregated_build = CommonBuild(
                        build_slug=build_slug,
                        subclasses=builds[0].subclasses.copy(),
                        sets=builds[0].sets.copy(),
                        count=total_players,
                        report_count=total_reports,
                        best_player=best_player,
                        all_players=[],  # Not needed for aggregated builds
                        trial_name=best_player_build.trial_name,  # Use original trial name for linking
                        boss_name=best_player_build.boss_name,    # Use original boss name for linking
                        fight_id=best_player_build.fight_id,      # Use original fight ID for linking
                        update_version=builds[0].update_version,
                        trials_appeared_in=trials_appeared,
                        is_aggregated=True
                    )
                    aggregated_builds.append(aggregated_build)
            
            # Sort by total player count (descending) and take top 5
            aggregated_builds.sort(key=lambda x: x.count, reverse=True)
            aggregated_by_role[role] = aggregated_builds[:5]
        
        # Aggregate trash builds separately
        if trash_builds:
            logger.info(f"Aggregating {len(trash_builds)} trash builds")
            trash_role_builds = defaultdict(lambda: defaultdict(list))
            
            for build in trash_builds:
                if not build.best_player:
                    continue
                    
                role = build.best_player.role.lower()
                build_slug = build.build_slug
                
                # Group by role and build signature
                trash_role_builds[role][build_slug].append(build)
            
            # Aggregate trash builds for each role
            for role, builds_by_slug in trash_role_builds.items():
                aggregated_trash_builds = []
                
                for build_slug, builds in builds_by_slug.items():
                    # Aggregate data across trials
                    total_players = sum(build.count for build in builds)
                    total_reports = sum(build.report_count for build in builds)
                    
                    # Collect all trials where this build appears
                    trials_appeared = list(set(build.trial_name for build in builds))
                    
                    # Find the highest metric player across all trials
                    best_player = None
                    best_metric = 0
                    best_player_build = None
                    
                    for build in builds:
                        if build.best_player:
                            metric = build.best_player.get_primary_metric()
                            if metric > best_metric:
                                best_metric = metric
                                best_player = build.best_player
                                best_player_build = build
                    
                    if best_player and best_player_build:
                        # Create aggregated build with original trial/boss info for linking
                        aggregated_build = CommonBuild(
                            build_slug=build_slug,
                            subclasses=builds[0].subclasses.copy(),
                            sets=builds[0].sets.copy(),
                            count=total_players,
                            report_count=total_reports,
                            best_player=best_player,
                            all_players=[],  # Not needed for aggregated builds
                            trial_name=best_player_build.trial_name,  # Use original trial name for linking
                            boss_name="Trash Builds",  # Keep as trash builds
                            fight_id=best_player_build.fight_id,      # Use original fight ID for linking
                            update_version=builds[0].update_version,
                            trials_appeared_in=trials_appeared,
                            is_aggregated=True
                        )
                        aggregated_trash_builds.append(aggregated_build)
                
                # Sort by total player count (descending) and take top 5
                aggregated_trash_builds.sort(key=lambda x: x.count, reverse=True)
                
                # Store trash builds separately for consolidated section
                if aggregated_trash_builds:
                    if 'trash' not in aggregated_by_role:
                        aggregated_by_role['trash'] = []
                    aggregated_by_role['trash'].extend(aggregated_trash_builds[:5])
        
        logger.info(f"Aggregated builds by role: {[(role, len(builds)) for role, builds in aggregated_by_role.items()]}")
        return aggregated_by_role