"""
Data models for ESO Build-O-Rama.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class Role(Enum):
    """Player roles in ESO."""
    TANK = "tank"
    HEALER = "healer"
    DPS = "dps"


class Difficulty(Enum):
    """Trial difficulty levels."""
    NORMAL = 1
    VETERAN = 2
    HARDMODE = 3


@dataclass
class GearPiece:
    """Represents a single piece of gear."""
    slot: str  # e.g., "head", "chest", "main_hand"
    item_id: Optional[int] = None
    item_name: str = ""
    set_id: Optional[int] = None
    set_name: str = ""
    trait: str = ""
    trait_id: Optional[int] = None  # Store the original trait ID from API
    enchantment: str = ""
    enchant_id: Optional[int] = None  # Store the original enchant ID from API
    quality: str = ""
    level: int = 0
    bar: int = 1  # Which bar this piece is equipped on (1 or 2)
    armor_weight: str = ""  # H, M, L for armor pieces (slots 0-6)


@dataclass
class Ability:
    """Represents an ability on the action bar."""
    ability_id: Optional[int] = None
    ability_name: str = ""
    slot: int = 0  # 0-11 for each bar
    bar: int = 1  # 1 or 2
    skill_line: str = ""
    ability_icon: str = ""  # Icon filename from ESO Logs (e.g., "ability_nightblade_005_b")
    morph: str = ""  # e.g., "Morph1", "Morph2"


@dataclass
class PlayerBuild:
    """Represents a player's complete build."""
    # Player info
    player_name: str = ""
    character_name: str = ""
    player_id: Optional[int] = None
    character_id: Optional[int] = None
    class_name: str = ""
    role: str = ""  # dps, healer, tank
    
    # Performance
    dps: float = 0.0
    dps_percentage: float = 0.0
    healing: float = 0.0
    healing_percentage: float = 0.0
    
    # Build components
    gear: List[GearPiece] = field(default_factory=list)
    abilities_bar1: List[Ability] = field(default_factory=list)
    abilities_bar2: List[Ability] = field(default_factory=list)
    
    # Analysis results
    subclasses: List[str] = field(default_factory=list)  # e.g., ["Ass", "Herald", "Ardent"]
    sets_equipped: Dict[str, int] = field(default_factory=dict)  # set_name -> count
    sets_bar1: Dict[str, int] = field(default_factory=dict)
    sets_bar2: Dict[str, int] = field(default_factory=dict)
    
    # Buffs and CP
    mundus: str = ""
    champion_points: List[str] = field(default_factory=list)  # Blue CP abilities
    
    # Metadata
    report_code: str = ""
    fight_id: int = 0
    fight_name: str = ""
    trial_name: str = ""
    boss_name: str = ""
    player_url: str = ""
    
    def get_build_slug(self) -> str:
        """Generate a build slug for identification."""
        # Sort subclasses alphabetically
        sorted_subclasses = sorted(self.subclasses) if self.subclasses else ["x", "x", "x"]
        subclass_slug = "-".join(sorted_subclasses).lower()
        
        # Get the two most common sets
        sorted_sets = sorted(self.sets_equipped.items(), key=lambda x: x[1], reverse=True)
        set_slugs = []
        for set_name, count in sorted_sets[:2]:
            if count >= 4:  # Only include if it's a meaningful set
                # Convert set name to slug format
                slug = set_name.lower().replace(" ", "-").replace("'", "")
                set_slugs.append(slug)
        
        # Sort set slugs alphabetically for consistent ordering
        set_slugs.sort()
        
        # Pad with empty strings if needed
        while len(set_slugs) < 2:
            set_slugs.append("unknown")
        
        return f"{subclass_slug}-{'-'.join(set_slugs)}"


@dataclass
class CommonBuild:
    """Represents a build that appears frequently."""
    build_slug: str = ""
    subclasses: List[str] = field(default_factory=list)
    sets: List[str] = field(default_factory=list)
    count: int = 0
    report_count: int = 0
    best_player: Optional[PlayerBuild] = None
    all_players: List[PlayerBuild] = field(default_factory=list)
    
    # Metadata
    trial_name: str = ""
    boss_name: str = ""
    fight_id: int = 0
    update_version: str = ""
    
    def get_display_name(self) -> str:
        """Get a human-readable name for the build."""
        subclass_names = {
            "animal": "Animal Companions",
            "ardent": "Ardent Flame",
            "ass": "Assassination",
            "bone": "Bone Tyrant",
            "curative": "Curative Runeforms",
            "daedric": "Daedric Summoning",
            "dark": "Dark Magic",
            "dawn": "Dawn's Wrath",
            "draconic": "Draconic Power",
            "earthen": "Earthen Heart",
            "grave": "Grave Lord",
            "green": "Green Balance",
            "herald": "Herald of the Tome",
            "living": "Living Death",
            "resto": "Restoring Light",
            "shadow": "Shadow",
            "siphon": "Siphoning",
            "soldier": "Soldier of Apocrypha",
            "spear": "Aedric Spear",
            "storm": "Storm Calling",
            "winter": "Winter's Embrace",
            "x": "Unknown"
        }
        
        full_subclasses = []
        for subclass in self.subclasses:
            full_subclasses.append(subclass_names.get(subclass.lower(), subclass.title()))
        
        # Sort subclasses alphabetically for consistent display
        full_subclasses.sort()
        
        # Role information is now shown via icon, not in parentheses
        return " / ".join(full_subclasses)
    
    def get_all_sets_used(self) -> List[str]:
        """Get a list of all unique sets used by players with this build."""
        all_sets = set()
        for player in self.all_players:
            if player.sets_equipped:
                all_sets.update(player.sets_equipped.keys())
        
        # Sort alphabetically and return as list
        return sorted(list(all_sets))
    
    def get_sorted_sets(self) -> List[str]:
        """Get the main sets for this build, sorted alphabetically."""
        return sorted(self.sets) if self.sets else []
    
    def meets_threshold(self) -> bool:
        """Check if this build meets the minimum occurrence threshold for its role."""
        if not self.best_player:
            return False
        
        role = self.best_player.role.lower()
        
        # Different thresholds based on role
        if role in ['tank', 'healer']:
            return self.count >= 3
        else:  # DPS or unknown
            return self.count >= 5


@dataclass
class TrialReport:
    """Represents a complete trial report analysis."""
    trial_name: str = ""
    boss_name: str = ""
    fight_id: int = 0
    report_code: str = ""
    date: str = ""
    update_version: str = ""
    total_reports_analyzed: int = 0  # Total number of reports analyzed for this trial/boss
    
    # All players in the fight
    all_players: List[PlayerBuild] = field(default_factory=list)
    
    # Common builds found
    common_builds: List[CommonBuild] = field(default_factory=list)
    
    # Statistics
    total_players: int = 0
    dps_players: int = 0
    healer_players: int = 0
    tank_players: int = 0
    
    def get_unique_builds(self) -> List[CommonBuild]:
        """Get builds that meet the role-based occurrence threshold (3+ for tank/healer, 5+ for DPS)."""
        return [build for build in self.common_builds if build.meets_threshold()]
