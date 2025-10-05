"""
Build Analysis Module
Analyzes player builds to identify common builds and create build slugs.
"""

import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter

from .models import PlayerBuild, CommonBuild, TrialReport
from .subclass_analyzer import ESOSubclassAnalyzer

logger = logging.getLogger(__name__)


class BuildAnalyzer:
    """Analyzes player builds to identify common patterns."""
    
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
        logger.info(f"Analyzing {len(trial_report.all_players)} players for trial {trial_report.trial_name}")
        
        # Analyze each player's build
        for player in trial_report.all_players:
            self._analyze_player_build(player)
        
        # Group players by build slug
        build_groups = self._group_players_by_build(trial_report.all_players)
        
        # Create build objects for ALL builds (not just 5+)
        all_builds = []
        for build_slug, players in build_groups.items():
            common_build = self._create_common_build(build_slug, players, trial_report)
            all_builds.append(common_build)
        
        # Sort by count (most common first)
        all_builds.sort(key=lambda x: x.count, reverse=True)
        
        # Store ALL builds for debugging
        common_builds = all_builds
        
        trial_report.common_builds = common_builds
        logger.info(f"Found {len(common_builds)} common builds")
        
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
    
    def _analyze_gear_sets(self, player: PlayerBuild) -> None:
        """Analyze gear to determine set counts per bar."""
        # Count sets for each bar
        bar1_sets = defaultdict(int)
        bar2_sets = defaultdict(int)
        total_sets = defaultdict(int)
        
        for gear in player.gear:
            if gear.set_name and gear.set_name.strip():
                set_name = gear.set_name.strip()
                
                # Always add to total count (for "Sets Used" display)
                total_sets[set_name] += 1
                
                # Skip mythics and arena weapons from bar-specific set counts (they don't contribute to 5-piece bonuses)
                if self._is_mythic_item(gear.item_name) or self._is_arena_weapon(gear.item_name):
                    continue
                
                # Add to appropriate bar count
                if gear.bar == 1:
                    bar1_sets[set_name] += 1
                elif gear.bar == 2:
                    bar2_sets[set_name] += 1
                else:
                    # If bar is not specified, assume bar 1
                    bar1_sets[set_name] += 1
        
        # Handle 2H weapons and staves (count as 2 pieces)
        for gear in player.gear:
            if gear.slot in ['main_hand', 'backup_main_hand']:
                # Check if it's a 2H weapon or staff
                if self._is_two_handed_weapon(gear.item_name):
                    if gear.set_name and gear.set_name.strip():
                        set_name = gear.set_name.strip()
                        
                        # Always add to total count (for "Sets Used" display)
                        total_sets[set_name] += 1
                        
                        # Skip arena weapons from bar-specific counts (they don't contribute to 5-piece bonuses)
                        if self._is_arena_weapon(gear.item_name):
                            continue
                        
                        # Add extra count for 2H weapons (they count as 2 pieces for set bonuses)
                        if gear.bar == 1 or gear.bar == 0:
                            bar1_sets[set_name] += 1  # Already counted 1, add 1 more
                        elif gear.bar == 2:
                            bar2_sets[set_name] += 1
        
        player.sets_equipped = dict(total_sets)
        player.sets_bar1 = dict(bar1_sets)
        player.sets_bar2 = dict(bar2_sets)
        
        logger.debug(f"Sets for {player.character_name}: {dict(total_sets)}")
    
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
            'band of', 'amulet of', 'necklace of'
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
            if count >= 4:  # Only include if it's a meaningful set
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
    
    def get_build_statistics(self, trial_report: TrialReport) -> Dict[str, any]:
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
                if count >= 4:  # Only count meaningful sets
                    set_counts[set_name] += count
        
        return dict(set_counts)
