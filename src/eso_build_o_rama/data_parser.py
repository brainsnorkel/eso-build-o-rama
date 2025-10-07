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
    1: "chest",
    2: "shoulders",
    3: "belt",
    4: "hands",
    5: "legs",
    6: "feet",
    7: "neck",
    8: "ring1",
    9: "ring2",
    10: "main_hand",
    11: "off_hand",
    12: "backup_main_hand",
    13: "backup_off_hand",
}

# Armor weight mapping (from ESO Logs API)
# Based on the type field in gear items
ARMOR_WEIGHT_NAMES = {
    0: "L",  # Light Armor
    1: "L",  # Light Armor (alternate)
    2: "M",  # Medium Armor
    3: "H",  # Heavy Armor
}

# Trait name mapping (from ESO Logs API)
# Trait names from @sheumais's authoritative list (https://github.com/sheumais/logs)
# IDs are from ESO Logs API observation and may be context-specific (armor/jewelry/weapon)
# Note: Some IDs map to same trait name but different slot types (e.g., Infused, Training, Nirnhoned)
TRAIT_NAMES = {
    # Armor traits (IDs 1-10)
    1: "Divines",           # Increases Mundus Stone effects
    2: "Impenetrable",      # Increases Critical Resistance
    3: "Infused",           # Increases enchantment effectiveness (armor)
    4: "Reinforced",        # Increases Armor value
    5: "Sturdy",            # Reduces block cost
    6: "Training",          # Increases experience gained (armor)
    7: "Well-Fitted",       # Reduces sprinting and roll dodge cost
    8: "Nirnhoned",         # Increases Physical and Spell Resistance (armor)
    9: "Intricate",         # Increases inspiration gained when deconstructing (armor)
    10: "Invigorating",     # Increases Health, Magicka, and Stamina Recovery (formerly Prosperous)
    
    # Jewelry traits (IDs 11-20)
    11: "Arcane",           # Increases Maximum Magicka
    12: "Healthy",          # Increases Maximum Health
    13: "Robust",           # Increases Maximum Stamina
    14: "Bloodthirsty",     # Increases damage against low health enemies
    15: "Harmony",          # Increases Synergy effectiveness
    16: "Infused",          # Increases enchantment effectiveness (jewelry)
    17: "Protective",       # Increases Physical and Spell Resistance (jewelry)
    18: "Swift",            # Increases movement speed
    19: "Triune",           # Increases Health, Magicka, and Stamina
    20: "Intricate",        # Increases inspiration gained when deconstructing (jewelry)
    
    # Weapon traits (IDs 21-30)
    21: "Powered",          # Increases healing done
    22: "Charged",          # Increases chance to apply status effects
    23: "Precise",          # Increases Weapon and Spell Critical
    24: "Infused",          # Increases enchantment effectiveness (weapon)
    25: "Defending",        # Increases Physical and Spell Resistance (weapon)
    26: "Training",         # Increases experience gained (weapon)
    27: "Sharpened",        # Increases Physical and Spell Penetration
    28: "Decisive",         # Increases Ultimate generation
    29: "Nirnhoned",        # Increases Weapon and Spell Damage (weapon)
    30: "Intricate",        # Increases inspiration gained when deconstructing (weapon)
}

# Enchantment type mapping (from ESO Logs API)
# IDs 0-36: Authoritative list from @sheumais (https://github.com/sheumais/logs)
# IDs 37+: Extended ESO Logs API IDs from empirical observation
ENCHANT_NAMES = {
    # Base enchants (IDs 0-36 from @sheumais's authoritative list)
    0: "None",
    1: "Absorb Health",
    2: "Absorb Magicka",
    3: "Absorb Stamina",
    4: "Befouled Weapon",
    5: "Berserker",
    6: "Charged Weapon",
    7: "Damage Health",
    8: "Damage Shield",
    9: "Decrease Physical Damage",
    10: "Decrease Spell Damage",
    11: "Disease Resistant",
    12: "Fiery Weapon",
    13: "Fire Resistant",
    14: "Frost Resistant",
    15: "Frozen Weapon",
    16: "Health",
    17: "Health Regen",
    18: "Increase Bash Damage",
    19: "Increase Physical Damage",
    20: "Increase Potion Effectiveness",
    21: "Increase Spell Damage",
    22: "Magicka",
    23: "Magicka Regen",
    24: "Poisoned Weapon",
    25: "Poison Resistant",
    26: "Prismatic Defense",
    27: "Prismatic Onslaught",
    28: "Reduce Armor",
    29: "Reduce Block and Bash",
    30: "Reduce Feat Cost",
    31: "Reduce Potion Cooldown",
    32: "Reduce Power",
    33: "Reduce Spell Cost",
    34: "Shock Resistant",
    35: "Stamina",
    36: "Stamina Regen",
    
    # Extended ESO Logs API IDs (observed in actual game data)
    37: "Health",                   # Alternate Health enchant ID
    38: "Magicka Recovery",         # Glyph of Magicka Recovery
    39: "Stamina Recovery",         # Glyph of Stamina Recovery
    40: "Health Recovery",          # Glyph of Health Recovery
    41: "Increase Magical Harm",    # Spell Damage enchant
    43: "Spell Critical",           # Glyph of Spell Critical
    44: "Weapon Critical",          # Glyph of Weapon Critical
    45: "Spell Resist",             # Glyph of Spell Resist
    46: "Physical Resist",          # Glyph of Physical Resist
    47: "Reduce Spell Cost",        # Glyph of Reduce Spell Cost (alternate ID)
    48: "Reduce Feat Cost",         # Glyph of Reduce Feat Cost (alternate ID)
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
        fight_id: int,
        player_details_data: Any = None
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
            
            # Get both playerDetails (for account names) and entries (for performance data)
            player_details_lookup = {}
            all_players_data = []
            
            # First, extract account names from playerDetails format (either from same data or separate call)
            player_details_source = data if 'playerDetails' in data else None
            if player_details_data and hasattr(player_details_data, 'report_data'):
                player_details_source = player_details_data.report_data.report.table['data']
            
            if player_details_source and 'playerDetails' in player_details_source and player_details_source.get('playerDetails'):
                player_details = player_details_source.get('playerDetails', {})
                dps_players = player_details.get('dps', [])
                healer_players = player_details.get('healers', [])
                tank_players = player_details.get('tanks', [])
                
                # Create lookup table: character_name -> account_name
                for player in dps_players + healer_players + tank_players:
                    char_name = player.get('name', '')
                    account_name = player.get('displayName', '')
                    if char_name and account_name:
                        player_details_lookup[char_name] = account_name
                
                logger.info(f"Created account name lookup for {len(player_details_lookup)} players")
            
            # Get performance data from entries format if available
            if 'entries' in data:
                # Entries format has actual performance data (total damage, active time) for all players
                all_players_data = data.get('entries', [])
                logger.info(f"Found {len(all_players_data)} players (entries format with performance data)")
            elif 'playerDetails' in data and data.get('playerDetails'):
                # Fall back to playerDetails format if entries not available
                player_details = data.get('playerDetails', {})
                dps_players = player_details.get('dps', [])
                healer_players = player_details.get('healers', [])
                tank_players = player_details.get('tanks', [])
                if dps_players or healer_players or tank_players:
                    all_players_data = dps_players + healer_players + tank_players
                    logger.info(f"Found {len(dps_players)} DPS, {len(healer_players)} healers, {len(tank_players)} tanks (playerDetails format)")
            
            if not all_players_data:
                logger.warning("No player data found in table")
                return []
            
            # Parse each player
            players = []
            for player_data in all_players_data:
                try:
                    # Determine role - use playerDetails lookup if available, otherwise infer
                    role = "unknown"
                    character_name = player_data.get('name', '')
                    
                    # First try to get role from playerDetails lookup
                    if character_name in player_details_lookup:
                        # We have playerDetails data, determine role from original classification
                        player_details = player_details_source.get('playerDetails', {})
                        dps_players = player_details.get('dps', [])
                        healer_players = player_details.get('healers', [])
                        tank_players = player_details.get('tanks', [])
                        
                        # Find this player in the original lists
                        for player in dps_players:
                            if player.get('name') == character_name:
                                role = "dps"
                                break
                        if role == "unknown":
                            for player in healer_players:
                                if player.get('name') == character_name:
                                    role = "healer"
                                    break
                        if role == "unknown":
                            for player in tank_players:
                                if player.get('name') == character_name:
                                    role = "tank"
                                    break
                    else:
                        # Fallback: infer role from performance data
                        total_damage = player_data.get('total', 0)
                        total_healing = player_data.get('overheal', 0)
                        
                        # Simple heuristic: if they have significant healing, they're a healer
                        # Otherwise, they're DPS (including tanks who also do damage)
                        if total_healing > total_damage * 0.5:  # More healing than damage
                            role = "healer"
                        else:
                            role = "dps"  # Includes tanks and DPS
                    
                    player_build = self._parse_player(player_data, report_data, fight_id, role, player_details_lookup)
                    if player_build:
                        players.append(player_build)
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Error parsing player {player_data.get('name', 'Unknown')}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Unexpected error parsing player {player_data.get('name', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Parsed {len(players)} players from fight {fight_id}")
            
            # Deduplicate players - keep only highest DPS for each player/character combo
            players = self._deduplicate_players(players)
            logger.info(f"After deduplication: {len(players)} unique players")
            
            return players
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing report data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error parsing report data: {e}")
            return []
    
    def _parse_player(
        self,
        player_data: Dict[str, Any],
        report_data: Dict[str, Any],
        fight_id: int,
        role: str = "unknown",
        player_details_lookup: Dict[str, str] = None
    ) -> Optional[PlayerBuild]:
        """Parse a single player's data."""
        
        try:
            # Basic info
            character_name = player_data.get('name', 'Unknown')
            
            # Get account name from lookup table or fallback to character name
            if player_details_lookup and character_name in player_details_lookup:
                player_name = player_details_lookup[character_name]
            else:
                # Fallback: use character name with @ prefix
                player_name = f"@{character_name}"
            class_name = player_data.get('type', 'Unknown')
            player_id = player_data.get('id', 0)
            
            # Handle both data formats:
            # 1. playerDetails format (newer, for kills): has combatantInfo nested
            # 2. entries format (older, for non-kills): has gear/talents at top level
            combatant_info = player_data.get('combatantInfo', {})
            
            if combatant_info:
                # PlayerDetails format
                gear_data = combatant_info.get('gear', [])
                talents = combatant_info.get('talents', [])
            else:
                # Entries format - gear and talents are at top level
                gear_data = player_data.get('gear', [])
                talents = player_data.get('talents', [])
                
                if not gear_data and not talents:
                    logger.debug(f"No gear or talents for {character_name}")
                    return None
            
            # Parse gear
            gear = self._parse_gear(gear_data)
            
            # Parse abilities
            abilities_bar1, abilities_bar2 = self._parse_abilities(talents)
            
            # Get DPS and stats
            # In entries format, 'total' is total damage, we can calculate DPS
            if 'total' in player_data and 'activeTime' in player_data:
                total_damage = player_data.get('total', 0)
                active_time_ms = player_data.get('activeTime', 1)
                dps = (total_damage / active_time_ms) * 1000 if active_time_ms > 0 else 0
            else:
                dps = player_data.get('dps', 0)
            
            dps_percentage = 0  # TODO: Calculate from total damage
            
            # Create player URL in the correct format
            # Format: https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={player_id}
            report_code = report_data.get('code', '')
            player_url = f"https://www.esologs.com/reports/{report_code}?fight={fight_id}&type=summary&source={player_id}"
            
            # Create player build
            player_build = PlayerBuild(
                character_name=character_name,
                player_name=player_name,
                player_id=player_id,  # Source ID for API queries
                class_name=class_name,
                role=role,
                dps=dps,
                dps_percentage=dps_percentage,
                gear=gear,
                abilities_bar1=abilities_bar1,
                abilities_bar2=abilities_bar2,
                mundus="",  # Will be fetched separately via Buffs table
                champion_points=[],  # TODO: Extract from buffs
                player_url=player_url,
                subclasses=[],  # Will be determined by analyzer
                report_code=report_code,
                fight_id=fight_id
            )
            
            return player_build
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing player data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing player: {e}")
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
                if slot_id in [12, 13, 14, 15, 16]:  # Backup slots (main_hand, off_hand, necklace, ring1, ring2)
                    bar = 2
                
                # Extract trait and enchantment IDs
                trait_id = item.get('trait', 0)
                enchant_id = item.get('enchantType', 0)
                
                # Extract armor weight for armor slots (0-6)
                armor_weight = ""
                if slot_id in [0, 1, 2, 3, 4, 5, 6]:  # Armor slots
                    armor_type_id = item.get('type', -1)
                    armor_weight = ARMOR_WEIGHT_NAMES.get(armor_type_id, '')
                
                # Debug: Log unknown IDs to help build complete lookup tables
                if trait_id and trait_id not in TRAIT_NAMES:
                    logger.debug(f"Unknown trait ID {trait_id} on {item.get('name', 'Unknown item')}")
                if enchant_id and enchant_id not in ENCHANT_NAMES:
                    logger.debug(f"Unknown enchant ID {enchant_id} on {item.get('name', 'Unknown item')}")
                
                gear_piece = GearPiece(
                    slot=slot_name,
                    item_id=item.get('id'),  # Store item ID from API
                    item_name=item.get('name', ''),
                    set_id=item.get('setID'),  # Store set ID from API
                    set_name=item.get('setName', ''),
                    trait=TRAIT_NAMES.get(trait_id, 'Unknown' if trait_id else ''),
                    trait_id=trait_id if trait_id else None,  # Store original trait ID
                    enchantment=ENCHANT_NAMES.get(enchant_id, 'Unknown' if enchant_id else ''),
                    enchant_id=enchant_id if enchant_id else None,  # Store original enchant ID
                    quality=item.get('quality', ''),  # Store quality from API
                    level=item.get('championPoints', 0),  # Store champion points from API
                    bar=bar,
                    armor_weight=armor_weight
                )
                
                gear_pieces.append(gear_piece)
                
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Error parsing gear piece data: {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error parsing gear piece: {e}")
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
                    ability_id=talent.get('guid', 0),
                    ability_icon=talent.get('abilityIcon', '')  # Icon filename for display
                )
                
                # First 6 abilities go to bar 1, next 6 to bar 2
                if i < 6:
                    abilities_bar1.append(ability)
                elif i < 12:
                    abilities_bar2.append(ability)
                    
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Error parsing ability data: {e}")
                continue
            except Exception as e:
                logger.debug(f"Unexpected error parsing ability: {e}")
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
    
    def _deduplicate_players(self, players: List[PlayerBuild]) -> List[PlayerBuild]:
        """
        Deduplicate players by player_name + character_name combination.
        Keep only the highest DPS instance for each unique player/character.
        
        Args:
            players: List of PlayerBuild objects (may contain duplicates)
            
        Returns:
            List of deduplicated PlayerBuild objects
        """
        # Group by player_name + character_name
        player_map = {}
        
        for player in players:
            key = f"{player.player_name}|{player.character_name}"
            
            if key not in player_map:
                player_map[key] = player
            else:
                # Keep the one with higher DPS
                if player.dps > player_map[key].dps:
                    player_map[key] = player
        
        deduplicated = list(player_map.values())
        
        if len(deduplicated) < len(players):
            logger.info(f"Removed {len(players) - len(deduplicated)} duplicate player entries")
        
        return deduplicated
    
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