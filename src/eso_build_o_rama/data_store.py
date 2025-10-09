"""
Data persistence module for storing trial build data incrementally.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import CommonBuild, PlayerBuild

logger = logging.getLogger(__name__)


class DataStore:
    """Handles persistence of trial build data to JSON file."""
    
    def __init__(self, builds_file: str = "output/builds.json"):
        """
        Initialize the data store.
        
        Args:
            builds_file: Path to the JSON file storing all trial builds
        """
        self.builds_file = Path(builds_file)
        self.builds_file.parent.mkdir(parents=True, exist_ok=True)
    
    def load_builds_data(self) -> Dict[str, Any]:
        """
        Load existing builds data from JSON file.
        
        Returns:
            Dictionary with trial data structure or empty structure if file doesn't exist
        """
        if not self.builds_file.exists():
            logger.info(f"Builds file doesn't exist, creating empty structure: {self.builds_file}")
            return {
                "trials": {},
                "last_full_update": None
            }
        
        try:
            with open(self.builds_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"Loaded builds data from {self.builds_file}")
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error loading builds file {self.builds_file}: {e}")
            return {
                "trials": {},
                "last_full_update": None
            }
    
    def save_trial_builds(
        self, 
        trial_name: str, 
        builds: List[CommonBuild], 
        update_version: str,
        cache_stats: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save builds for a specific trial, updating the JSON file.
        
        Args:
            trial_name: Name of the trial
            builds: List of CommonBuild objects to save
            update_version: Game update version (e.g., 'U48')
            cache_stats: Optional cache statistics from the scan
        """
        # Load existing data
        data = self.load_builds_data()
        
        # Serialize builds
        serialized_builds = [self._serialize_build(build) for build in builds]
        
        # Update trial data
        data["trials"][trial_name] = {
            "builds": serialized_builds,
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "update_version": update_version,
            "cache_stats": cache_stats
        }
        
        # Update last full update timestamp
        data["last_full_update"] = datetime.now(timezone.utc).isoformat()
        
        # Save to file
        try:
            with open(self.builds_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved {len(builds)} builds for trial '{trial_name}' to {self.builds_file}")
        except IOError as e:
            logger.error(f"Error saving builds file {self.builds_file}: {e}")
            raise
    
    def get_all_builds(self) -> List[CommonBuild]:
        """
        Get all builds from all trials, deserialized.
        
        Returns:
            List of all CommonBuild objects from all trials
        """
        data = self.load_builds_data()
        all_builds = []
        
        for trial_name, trial_data in data["trials"].items():
            builds_data = trial_data.get("builds", [])
            for build_data in builds_data:
                build = self._deserialize_build(build_data)
                if build:
                    all_builds.append(build)
        
        logger.info(f"Loaded {len(all_builds)} total builds from {len(data['trials'])} trials")
        return all_builds
    
    def get_trials_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metadata about all trials (last updated times, versions).
        
        Returns:
            Dictionary mapping trial names to their metadata
        """
        data = self.load_builds_data()
        metadata = {}
        
        for trial_name, trial_data in data["trials"].items():
            metadata[trial_name] = {
                "last_updated": trial_data.get("last_updated"),
                "update_version": trial_data.get("update_version"),
                "build_count": len(trial_data.get("builds", [])),
                "cache_stats": trial_data.get("cache_stats")
            }
        
        return metadata
    
    def _serialize_build(self, build: CommonBuild) -> Dict[str, Any]:
        """
        Serialize a CommonBuild object to a dictionary.
        
        Args:
            build: CommonBuild object to serialize
            
        Returns:
            Dictionary representation of the build
        """
        return {
            "build_slug": build.build_slug,
            "subclasses": build.subclasses,
            "sets": build.sets,
            "count": build.count,
            "report_count": build.report_count,
            "trial_name": build.trial_name,
            "boss_name": build.boss_name,
            "fight_id": build.fight_id,
            "update_version": build.update_version,
            "best_player": self._serialize_player(build.best_player) if build.best_player else None,
            "all_players": [self._serialize_player(p) for p in build.all_players]
        }
    
    def _deserialize_build(self, data: Dict[str, Any]) -> Optional[CommonBuild]:
        """
        Deserialize a dictionary back to a CommonBuild object.
        
        Args:
            data: Dictionary representation of the build
            
        Returns:
            CommonBuild object or None if deserialization fails
        """
        try:
            best_player = None
            if data.get("best_player"):
                best_player = self._deserialize_player(data["best_player"])
            
            all_players = []
            for player_data in data.get("all_players", []):
                player = self._deserialize_player(player_data)
                if player:
                    all_players.append(player)
            
            return CommonBuild(
                build_slug=data.get("build_slug", ""),
                subclasses=data.get("subclasses", []),
                sets=data.get("sets", []),
                count=data.get("count", 0),
                report_count=data.get("report_count", 0),
                trial_name=data.get("trial_name", ""),
                boss_name=data.get("boss_name", ""),
                fight_id=data.get("fight_id", 0),
                update_version=data.get("update_version", ""),
                best_player=best_player,
                all_players=all_players
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Error deserializing build: {e}")
            return None
    
    def _serialize_player(self, player: PlayerBuild) -> Dict[str, Any]:
        """
        Serialize a PlayerBuild object to a dictionary.
        
        Args:
            player: PlayerBuild object to serialize
            
        Returns:
            Dictionary representation of the player
        """
        return {
            "player_name": player.player_name,
            "character_name": player.character_name,
            "player_id": player.player_id,
            "character_id": player.character_id,
            "class_name": player.class_name,
            "role": player.role,
            "dps": player.dps,
            "dps_percentage": player.dps_percentage,
            "healing": player.healing,
            "healing_percentage": player.healing_percentage,
            "crowd_control": player.crowd_control,
            "gear": [self._serialize_gear_piece(gear) for gear in player.gear],
            "abilities_bar1": [self._serialize_ability(ability) for ability in player.abilities_bar1],
            "abilities_bar2": [self._serialize_ability(ability) for ability in player.abilities_bar2],
            "subclasses": player.subclasses,
            "sets_equipped": player.sets_equipped,
            "mundus": player.mundus,
            "champion_points": player.champion_points,
            "report_code": player.report_code,
            "fight_id": player.fight_id,
            "fight_name": player.fight_name,
            "trial_name": player.trial_name,
            "boss_name": player.boss_name,
            "player_url": player.player_url
        }
    
    def _deserialize_player(self, data: Dict[str, Any]) -> Optional[PlayerBuild]:
        """
        Deserialize a dictionary back to a PlayerBuild object.
        
        Args:
            data: Dictionary representation of the player
            
        Returns:
            PlayerBuild object or None if deserialization fails
        """
        try:
            # Deserialize gear
            gear_data = data.get("gear", [])
            gear = [self._deserialize_gear_piece(gear_dict) for gear_dict in gear_data]
            
            # Deserialize abilities
            abilities_bar1_data = data.get("abilities_bar1", [])
            abilities_bar1 = [self._deserialize_ability(ability_dict) for ability_dict in abilities_bar1_data]
            
            abilities_bar2_data = data.get("abilities_bar2", [])
            abilities_bar2 = [self._deserialize_ability(ability_dict) for ability_dict in abilities_bar2_data]
            
            return PlayerBuild(
                player_name=data.get("player_name", ""),
                character_name=data.get("character_name", ""),
                player_id=data.get("player_id"),
                character_id=data.get("character_id"),
                class_name=data.get("class_name", ""),
                role=data.get("role", ""),
                dps=data.get("dps", 0.0),
                dps_percentage=data.get("dps_percentage", 0.0),
                healing=data.get("healing", 0.0),
                healing_percentage=data.get("healing_percentage", 0.0),
                crowd_control=data.get("crowd_control", 0.0),
                gear=gear,
                abilities_bar1=abilities_bar1,
                abilities_bar2=abilities_bar2,
                subclasses=data.get("subclasses", []),
                sets_equipped=data.get("sets_equipped", {}),
                mundus=data.get("mundus", ""),
                champion_points=data.get("champion_points", []),
                report_code=data.get("report_code", ""),
                fight_id=data.get("fight_id", 0),
                fight_name=data.get("fight_name", ""),
                trial_name=data.get("trial_name", ""),
                boss_name=data.get("boss_name", ""),
                player_url=data.get("player_url", "")
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.warning(f"Error deserializing player: {e}")
            return None
    
    def _serialize_gear_piece(self, gear: 'GearPiece') -> Dict[str, Any]:
        """Serialize a GearPiece object to a dictionary."""
        from .models import GearPiece
        return {
            "slot": gear.slot,
            "item_id": gear.item_id,
            "item_name": gear.item_name,
            "set_id": gear.set_id,
            "set_name": gear.set_name,
            "trait": gear.trait,
            "trait_id": gear.trait_id,
            "enchantment": gear.enchantment,
            "enchant_id": gear.enchant_id,
            "quality": gear.quality,
            "level": gear.level,
            "bar": gear.bar,
            "armor_weight": gear.armor_weight
        }
    
    def _deserialize_gear_piece(self, data: Dict[str, Any]) -> 'GearPiece':
        """Deserialize a dictionary back to a GearPiece object."""
        from .models import GearPiece
        return GearPiece(
            slot=data.get("slot", ""),
            item_id=data.get("item_id"),
            item_name=data.get("item_name", ""),
            set_id=data.get("set_id"),
            set_name=data.get("set_name", ""),
            trait=data.get("trait", ""),
            trait_id=data.get("trait_id"),
            enchantment=data.get("enchantment", ""),
            enchant_id=data.get("enchant_id"),
            quality=data.get("quality", ""),
            level=data.get("level", 0),
            bar=data.get("bar", 1),
            armor_weight=data.get("armor_weight", "")
        )
    
    def _serialize_ability(self, ability: 'Ability') -> Dict[str, Any]:
        """Serialize an Ability object to a dictionary."""
        from .models import Ability
        return {
            "ability_name": ability.ability_name,
            "skill_line": ability.skill_line,
            "ability_id": ability.ability_id,
            "ability_icon": ability.ability_icon,
            "morph": ability.morph
        }
    
    def _deserialize_ability(self, data: Dict[str, Any]) -> 'Ability':
        """Deserialize a dictionary back to an Ability object."""
        from .models import Ability
        return Ability(
            ability_name=data.get("ability_name", ""),
            skill_line=data.get("skill_line", ""),
            ability_id=data.get("ability_id", 0),
            ability_icon=data.get("ability_icon", ""),
            morph=data.get("morph", "")
        )
