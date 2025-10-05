"""
Data Parser Module
Parses ESO Logs API responses to extract player build information.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import PlayerBuild, GearPiece, Ability, TrialReport

logger = logging.getLogger(__name__)


class DataParser:
    """Parses ESO Logs API data into structured build information."""
    
    def __init__(self):
        """Initialize the data parser."""
        pass
    
    def parse_report_data(
        self,
        report_data: Dict[str, Any],
        table_data: Dict[str, Any],
        fight_id: int
    ) -> List[PlayerBuild]:
        """
        Parse report and table data to extract player builds.
        
        Args:
            report_data: Report information from get_report()
            table_data: Table data from get_report_table() with includeCombatantInfo=True
            fight_id: Specific fight ID to analyze
            
        Returns:
            List of PlayerBuild objects
        """
        logger.info(f"Parsing report data for fight {fight_id}")
        
        # Extract fight information
        fight_info = self._get_fight_info(report_data, fight_id)
        if not fight_info:
            logger.error(f"Fight {fight_id} not found in report")
            return []
        
        # Extract player data from table
        players = []
        
        if 'data' in table_data:
            for player_data in table_data['data']:
                try:
                    player = self._parse_player_data(
                        player_data,
                        fight_info,
                        report_data.get('code', '')
                    )
                    if player:
                        players.append(player)
                except Exception as e:
                    logger.error(f"Error parsing player data: {e}")
                    continue
        
        logger.info(f"Parsed {len(players)} players from fight {fight_id}")
        return players
    
    def _get_fight_info(self, report_data: Dict[str, Any], fight_id: int) -> Optional[Dict[str, Any]]:
        """Extract information about a specific fight."""
        fights = report_data.get('fights', [])
        
        for fight in fights:
            if fight.get('id') == fight_id:
                return fight
        
        return None
    
    def _parse_player_data(
        self,
        player_data: Dict[str, Any],
        fight_info: Dict[str, Any],
        report_code: str
    ) -> Optional[PlayerBuild]:
        """Parse individual player data."""
        try:
            # Basic player info
            player_name = player_data.get('name', '')
            character_name = player_data.get('characterName', player_name)
            
            # Performance data
            dps = float(player_data.get('total', 0))
            dps_percentage = float(player_data.get('percent', 0))
            
            # Create player build object
            player = PlayerBuild(
                player_name=player_name,
                character_name=character_name,
                player_id=player_data.get('id'),
                character_id=player_data.get('characterID'),
                class_name=player_data.get('class', ''),
                dps=dps,
                dps_percentage=dps_percentage,
                report_code=report_code,
                fight_id=fight_info.get('id', 0),
                fight_name=fight_info.get('name', ''),
                trial_name=self._extract_trial_name(fight_info.get('name', '')),
                boss_name=self._extract_boss_name(fight_info.get('name', '')),
                player_url=f"https://www.esologs.com/character/{player_data.get('characterID', '')}"
            )
            
            # Parse combatant info if available
            if 'combatantInfo' in player_data:
                self._parse_combatant_info(player, player_data['combatantInfo'])
            
            # Parse gear if available
            if 'gear' in player_data:
                self._parse_gear_data(player, player_data['gear'])
            
            # Parse abilities if available
            if 'abilities' in player_data:
                self._parse_abilities_data(player, player_data['abilities'])
            
            return player
            
        except Exception as e:
            logger.error(f"Error parsing player {player_data.get('name', 'Unknown')}: {e}")
            return None
    
    def _parse_combatant_info(self, player: PlayerBuild, combatant_info: Dict[str, Any]) -> None:
        """Parse combatant info to extract gear and abilities."""
        # Parse gear
        if 'gear' in combatant_info:
            self._parse_gear_data(player, combatant_info['gear'])
        
        # Parse abilities
        if 'abilities' in combatant_info:
            self._parse_abilities_data(player, combatant_info['abilities'])
        
        # Parse buffs (for Mundus and CP)
        if 'buffs' in combatant_info:
            self._parse_buffs_data(player, combatant_info['buffs'])
    
    def _parse_gear_data(self, player: PlayerBuild, gear_data: List[Dict[str, Any]]) -> None:
        """Parse gear data."""
        for gear_item in gear_data:
            try:
                gear_piece = GearPiece(
                    slot=gear_item.get('slot', ''),
                    item_id=gear_item.get('itemID'),
                    item_name=gear_item.get('itemName', ''),
                    set_id=gear_item.get('setID'),
                    set_name=gear_item.get('setName', ''),
                    trait=gear_item.get('traitName', ''),
                    enchantment=gear_item.get('enchantName', ''),
                    quality=gear_item.get('quality', ''),
                    level=gear_item.get('itemLevel', 0),
                    bar=gear_item.get('bar', 1)
                )
                player.gear.append(gear_piece)
            except Exception as e:
                logger.error(f"Error parsing gear item: {e}")
                continue
    
    def _parse_abilities_data(self, player: PlayerBuild, abilities_data: Dict[str, Any]) -> None:
        """Parse abilities data for both bars."""
        # Parse bar 1 abilities
        if 'bar1' in abilities_data:
            bar1_abilities = abilities_data['bar1']
            for i, ability_data in enumerate(bar1_abilities):
                ability = Ability(
                    ability_id=ability_data.get('id'),
                    ability_name=ability_data.get('name', ''),
                    slot=i,
                    bar=1,
                    skill_line=ability_data.get('skillLine', ''),
                    morph=ability_data.get('morph', '')
                )
                player.abilities_bar1.append(ability)
        
        # Parse bar 2 abilities
        if 'bar2' in abilities_data:
            bar2_abilities = abilities_data['bar2']
            for i, ability_data in enumerate(bar2_abilities):
                ability = Ability(
                    ability_id=ability_data.get('id'),
                    ability_name=ability_data.get('name', ''),
                    slot=i,
                    bar=2,
                    skill_line=ability_data.get('skillLine', ''),
                    morph=ability_data.get('morph', '')
                )
                player.abilities_bar2.append(ability)
    
    def _parse_buffs_data(self, player: PlayerBuild, buffs_data: List[Dict[str, Any]]) -> None:
        """Parse buffs data to extract Mundus and Champion Points."""
        for buff in buffs_data:
            buff_name = buff.get('name', '').lower()
            
            # Check for Mundus stone
            if 'mundus' in buff_name or 'boon' in buff_name:
                player.mundus = buff.get('name', '')
            
            # Check for Champion Points (blue CP)
            # This is a simplified check - may need refinement
            if any(keyword in buff_name for keyword in ['champion', 'cp', 'blue']):
                if buff.get('name', '') not in player.champion_points:
                    player.champion_points.append(buff.get('name', ''))
    
    def _extract_trial_name(self, fight_name: str) -> str:
        """Extract trial name from fight name."""
        # This is a simplified extraction - may need refinement based on actual data
        if ' - ' in fight_name:
            return fight_name.split(' - ')[0]
        return fight_name
    
    def _extract_boss_name(self, fight_name: str) -> str:
        """Extract boss name from fight name."""
        # This is a simplified extraction - may need refinement based on actual data
        if ' - ' in fight_name:
            return fight_name.split(' - ')[1]
        return fight_name
    
    def create_trial_report(
        self,
        players: List[PlayerBuild],
        trial_name: str,
        boss_name: str,
        report_code: str,
        update_version: str = ""
    ) -> TrialReport:
        """Create a TrialReport from parsed player data."""
        trial_report = TrialReport(
            trial_name=trial_name,
            boss_name=boss_name,
            report_code=report_code,
            update_version=update_version,
            all_players=players
        )
        
        # Count players by role (simplified)
        for player in players:
            trial_report.total_players += 1
            # Simple role detection based on healing percentage
            if player.healing_percentage > 10:
                trial_report.healer_players += 1
            elif player.dps_percentage > 5:
                trial_report.dps_players += 1
            else:
                trial_report.tank_players += 1
        
        return trial_report
