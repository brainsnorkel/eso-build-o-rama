"""
Data Parser Module
Parses ESO Logs API responses to extract player build information.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import PlayerBuild, GearPiece, Ability, TrialReport

logger = logging.getLogger(__name__)

# Slot ID mapping (from ESO Logs API)
SLOT_NAMES = {
    0: "head",
    1: "shoulders",
    2: "chest",
    3: "belt",
    4: "legs",
    5: "boots",
    6: "hands",
    13: "necklace",
    14: "ring1",
    15: "ring2",
    16: "main_hand",
    17: "off_hand",
    18: "backup_main_hand",
    19: "backup_off_hand"
}

# Trait ID mapping (common ESO traits)
TRAIT_NAMES = {
    1: "Divines",
    2: "Infused",
    3: "Impenetrable",
    4: "Reinforced",
    5: "Sturdy",
    6: "Training",
    7: "Well-Fitted",
    11: "Arcane",
    12: "Healthy",
    13: "Robust",
    16: "Bloodthirsty",
    17: "Harmony",
    18: "Protective",
    19: "Swift",
    20: "Triune",
    21: "Charged",
    22: "Decisive",
    23: "Defending",
    24: "Nirnhoned",
    25: "Powered",
    26: "Precise",
    27: "Sharpened",
    28: "Training"
}

# Enchantment type mapping
ENCHANT_NAMES = {
    35: "Max Health",
    36: "Max Magicka",
    37: "Max Stamina",
    38: "Magicka Recovery",
    39: "Stamina Recovery",
    40: "Health Recovery",
    41: "Spell Damage",
    42: "Weapon Damage",
    43: "Spell Critical",
    44: "Weapon Critical",
    45: "Spell Resist",
    46: "Physical Resist",
    47: "Reduce Spell Cost",
    48: "Reduce Feat Cost"
}


class DataParser:
    """Parses ESO Logs API data into structured build information."""
    
    def __init__(self):
        """Initialize the data parser."""
        pass
    
    def parse_report_data(
        self,
        report_data: Dict[str, Any],
        table_data: Any,
        fight_id: int
    ) -> List[PlayerBuild]:
        """
        Parse report and table data to extract player builds.
        
        Args:
            report_data: Report information from get_report()
            table_data: Table data object from get_report_table() with includeCombatantInfo=True
            fight_id: Specific fight ID to analyze
            
        Returns:
            List of PlayerBuild objects
        """
        logger.info(f"Parsing report data for fight {fight_id}")
        
        try:
            # Extract table dict from the API response object
            if hasattr(table_data, 'report_data') and hasattr(table_data.report_data, 'report'):
                table = table_data.report_data.report.table
                data = table['data']
            else:
                logger.error("Invalid table data structure")
                return []
            
            # Get player details
            player_details = data.get('playerDetails', {})
            dps_players = player_details.get('dps', [])
            healer_players = player_details.get('healers', [])
            
            all_players_data = dps_players + healer_players
            
            logger.info(f"Found {len(dps_players)} DPS and {len(healer_players)} healers")
            
            if not all_players_data:
                logger.warning("No player data found in table")
                return []
            
            # Parse each player
            players = []
            for player_data in all_players_data:
                try:
                    player_build = self._parse_player(player_data, report_data, fight_id)
                    if player_build:
                        players.append(player_build)
                except Exception as e:
                    logger.error(f"Error parsing player {player_data.get('name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Parsed {len(players)} players from fight {fight_id}")
            return players
            
        except Exception as e:
            logger.error(f"Error parsing report data: {e}")
            return []
    
    def _parse_player(
        self,
        player_data: Dict[str, Any],
        report_data: Dict[str, Any],
        fight_id: int
    ) -> Optional[PlayerBuild]:
        """Parse a single player's data."""
        
        try:
            # Basic info
            character_name = player_data.get('name', 'Unknown')
            player_name = player_data.get('displayName', '@Unknown')
            class_name = player_data.get('type', 'Unknown')
            player_id = player_data.get('id', 0)
            
            # Get combatant info
            combatant_info = player_data.get('combatantInfo', {})
            if not combatant_info:
                logger.debug(f"No combatant info for {character_name}")
                return None
            
            # Parse gear
            gear = self._parse_gear(combatant_info.get('gear', []))
            
            # Parse abilities
            talents = combatant_info.get('talents', [])
            abilities_bar1, abilities_bar2 = self._parse_abilities(talents)
            
            # Get DPS and stats (placeholder - would need to extract from damage done)
            dps = 0  # TODO: Extract from damageDone array
            dps_percentage = 0  # TODO: Calculate from total damage
            
            # Create player build
            player_build = PlayerBuild(
                character_name=character_name,
                player_name=player_name,
                class_name=class_name,
                dps=dps,
                dps_percentage=dps_percentage,
                gear=gear,
                abilities_bar1=abilities_bar1,
                abilities_bar2=abilities_bar2,
                mundus="",  # TODO: Extract from buffs
                champion_points=[],  # TODO: Extract from buffs
                player_url=f"https://www.esologs.com/character/id/{player_id}",
                subclasses=[],  # Will be determined by analyzer
                report_code=report_data.get('code', ''),
                fight_id=fight_id
            )
            
            return player_build
            
        except Exception as e:
            logger.error(f"Error parsing player: {e}")
            return None
    
    def _parse_gear(self, gear_data: List[Dict[str, Any]]) -> List[GearPiece]:
        """Parse gear pieces from combatant info."""
        
        gear_pieces = []
        
        for item in gear_data:
            try:
                slot_id = item.get('slot', -1)
                slot_name = SLOT_NAMES.get(slot_id, f"slot_{slot_id}")
                
                # Determine which bar this gear is on
                bar = 1
                if slot_id in [18, 19]:  # Backup weapons
                    bar = 2
                
                gear_piece = GearPiece(
                    slot=slot_name,
                    set_name=item.get('setName', ''),
                    item_name=item.get('name', ''),
                    trait=TRAIT_NAMES.get(item.get('trait', 0), 'Unknown'),
                    enchantment=ENCHANT_NAMES.get(item.get('enchantType', 0), 'Unknown'),
                    bar=bar
                )
                
                gear_pieces.append(gear_piece)
                
            except Exception as e:
                logger.debug(f"Error parsing gear piece: {e}")
                continue
        
        return gear_pieces
    
    def _parse_abilities(
        self,
        talents: List[Dict[str, Any]]
    ) -> tuple[List[Ability], List[Ability]]:
        """
        Parse abilities from talents list.
        
        ESO has 2 bars with 6 abilities each (5 regular + 1 ultimate).
        Talents are ordered: Bar 1 (abilities 1-5, ultimate), Bar 2 (abilities 1-5, ultimate)
        
        Args:
            talents: List of talent dicts from combatantInfo
            
        Returns:
            Tuple of (bar1_abilities, bar2_abilities)
        """
        
        abilities_bar1 = []
        abilities_bar2 = []
        
        # Talents should have 12 total (6 per bar)
        # Type 8 appears to be ultimate abilities
        # flags=1 seems to indicate active abilities
        
        for i, talent in enumerate(talents):
            try:
                ability = Ability(
                    ability_name=talent.get('name', ''),
                    skill_line='',  # TODO: Map from ability ID to skill line
                    ability_id=talent.get('guid', 0)
                )
                
                # First 6 abilities go to bar 1, next 6 to bar 2
                if i < 6:
                    abilities_bar1.append(ability)
                elif i < 12:
                    abilities_bar2.append(ability)
                    
            except Exception as e:
                logger.debug(f"Error parsing ability: {e}")
                continue
        
        return abilities_bar1, abilities_bar2
    
    def create_trial_report(
        self,
        players: List[PlayerBuild],
        trial_name: str,
        boss_name: str,
        report_code: str,
        update_version: str
    ) -> TrialReport:
        """
        Create a TrialReport from parsed player builds.
        
        Args:
            players: List of PlayerBuild objects
            trial_name: Name of the trial
            boss_name: Name of the boss
            report_code: ESO Logs report code
            update_version: Game update version
            
        Returns:
            TrialReport object
        """
        trial_report = TrialReport(
            trial_name=trial_name,
            boss_name=boss_name,
            all_players=players,
            report_code=report_code,
            update_version=update_version,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        
        return trial_report
    
    def _get_fight_info(
        self,
        report_data: Dict[str, Any],
        fight_id: int
    ) -> Optional[Dict[str, Any]]:
        """Get fight information from report data."""
        
        for fight in report_data.get('fights', []):
            if fight.get('id') == fight_id:
                return fight
        
        return None