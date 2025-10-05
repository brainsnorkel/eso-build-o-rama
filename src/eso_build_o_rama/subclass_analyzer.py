"""
ESO Subclass Analysis Module
Analyzes equipped abilities to infer player subclass/build information.
"""

import re
import logging
from typing import Dict, List, Set, Optional, Tuple
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class ESOSubclassAnalyzer:
    """Analyzes abilities to infer player subclass/build."""

    SKILL_LINE_ALIASES = { 
        'Assassination': 'Ass',
        'Dawn\'s Wrath': 'Dawn',
        'Herald': 'Herald',
        'Bone': 'BoneTyrant',
        'Living': 'LivingDeath',
        'Winter\'s': 'Winter'
    }

    # Complete ESO Class Skill Line Abilities - Updated for 2025
    SKILL_LINE_ABILITIES = {
        # Dragonknight Skill Lines
        'Ardent Flame': [
            # Ultimate
            'Dragonknight Standard', 'Shifting Standard', 'Standard of Might',
            # Active Skills
            'Lava Whip', 'Molten Whip', 'Flame Lash',
            'Searing Strike', 'Venomous Claw', 'Burning Embers',
            'Fiery Breath', 'Noxious Breath', 'Engulfing Flames',
            'Fiery Grip', 'Empowering Chains', 'Unrelenting Grip',
            'Inferno', 'Flames of Oblivion', 'Cauterize'
        ],
        
        'Draconic Power': [
            # Ultimate
            'Dragon Leap', 'Ferocious Leap', 'Take Flight',
            # Active Skills
            'Spiked Armor', 'Hardened Armor', 'Volatile Armor',
            'Dark Talons', 'Burning Talons', 'Choking Talons',
            'Dragon Blood', 'Green Dragon Blood', 'Coagulating Blood',
            'Reflective Scale', 'Dragon Fire Scale', 'Reflective Plate',
            'Inhale', 'Deep Breath', 'Draw Essence'
        ],
        
        'Earthen Heart': [
            # Ultimate
            'Magma Armor', 'Magma Shell', 'Corrosive Armor',
            # Active Skills
            'Stonefist', 'Stone Giant', 'Obsidian Shard',
            'Molten Weapons', 'Igneous Weapons', 'Molten Armaments',
            'Obsidian Shield', 'Igneous Shield', 'Fragmented Shield',
            'Petrify', 'Fossilize', 'Shattering Rocks',
            'Ash Cloud', 'Cinder Storm', 'Eruption'
        ],
        
        # Sorcerer Skill Lines
        'Dark Magic': [
            # Ultimate
            'Negate Magic', 'Suppression Field', 'Absorption Field',
            # Active Skills
            'Crystal Shard', 'Crystal Fragments', 'Crystal Weapon',
            'Encase', 'Shattering Prison', 'Restraining Prison',
            'Rune Prison', 'Rune Cage', 'Defensive Rune',
            'Dark Exchange', 'Dark Deal', 'Dark Conversion',
            'Daedric Mines', 'Daedric Tomb', 'Daedric Minefield'
        ],
        
        'Daedric Summoning': [
            # Ultimate
            'Summon Storm Atronach', 'Greater Storm Atronach', 'Summon Charged Atronach',
            # Active Skills
            'Summon Unstable Familiar', 'Summon Unstable Clannfear', 'Summon Volatile Familiar',
            'Daedric Curse', 'Daedric Prey', 'Haunting Curse',
            'Summon Winged Twilight', 'Summon Twilight Tormentor', 'Summon Twilight Matriarch',
            'Conjured Ward', 'Hardened Ward', 'Empowered Ward',
            'Bound Armor', 'Bound Armaments', 'Bound Aegis'
        ],
        
        'Storm Calling': [
            # Ultimate
            'Overload', 'Power Overload', 'Energy Overload',
            # Active Skills
            'Mages\' Fury', 'Mages\' Wrath', 'Endless Fury',
            'Lightning Form', 'Hurricane', 'Boundless Storm',
            'Lightning Splash', 'Liquid Lightning', 'Lightning Flood',
            'Surge', 'Power Surge', 'Critical Surge',
            'Bolt Escape', 'Streak', 'Ball of Lightning'
        ],
        
        # Nightblade Skill Lines
        'Assassination': [
            # Ultimate
            'Death Stroke', 'Incapacitating Strike', 'Soul Harvest',
            # Active Skills
            'Assassin\'s Blade', 'Killer\'s Blade', 'Impale',
            'Teleport Strike', 'Ambush', 'Lotus Fan',
            'Veiled Strike', 'Surprise Attack', 'Concealed Weapon',
            'Mark Target', 'Piercing Mark', 'Reaper\'s Mark',
            'Grim Focus', 'Relentless Focus', 'Merciless Resolve'
        ],
        
        'Shadow': [
            # Ultimate
            'Consuming Darkness', 'Bolstering Darkness', 'Veil of Blades',
            # Active Skills
            'Shadow Cloak', 'Shadowy Disguise', 'Dark Cloak',
            'Blur', 'Mirage', 'Phantasmal Escape',
            'Path of Darkness', 'Twisting Path', 'Refreshing Path',
            'Aspect of Terror', 'Mass Hysteria', 'Manifestation of Terror',
            'Summon Shade', 'Dark Shade', 'Shadow Image'
        ],
        
        'Siphoning': [
            # Ultimate
            'Soul Shred', 'Soul Siphon', 'Soul Tether',
            # Active Skills
            'Strife', 'Funnel Health', 'Swallow Soul',
            'Agony', 'Prolonged Suffering', 'Malefic Wreath',
            'Cripple', 'Debilitate', 'Crippling Grasp',
            'Siphoning Strikes', 'Leeching Strikes', 'Siphoning Attacks',
            'Drain Power', 'Power Extraction', 'Sap Essence'
        ],
        
        # Templar Skill Lines
        'Aedric Spear': [
            # Ultimate
            'Radial Sweep', 'Crescent Sweep', 'Everlasting Sweep',
            # Active Skills
            'Puncturing Strikes', 'Biting Jabs', 'Puncturing Sweep',
            'Piercing Javelin', 'Aurora Javelin', 'Binding Javelin',
            'Focused Charge', 'Explosive Charge', 'Toppling Charge',
            'Spear Shards', 'Luminous Shards', 'Blazing Spear',
            'Sun Shield', 'Radiant Ward', 'Blazing Shield'
        ],
        
        'Dawn\'s Wrath': [
            # Ultimate
            'Nova', 'Solar Prison', 'Solar Disturbance',
            # Active Skills
            'Sun Fire', 'Vampire\'s Bane', 'Reflective Light',
            'Solar Flare', 'Dark Flare', 'Solar Barrage',
            'Backlash', 'Purifying Light', 'Power of the Light',
            'Eclipse', 'Total Dark', 'Unstable Core',
            'Solar Prison', 'Radiant Oppression', 'Solar Disturbance'
        ],
        
        'Restoring Light': [
            # Ultimate
            'Rite of Passage', 'Practiced Incantation', 'Remembrance',
            # Active Skills
            'Healing Hands', 'Breath of Life', 'Combat Prayer',
            'Rushed Ceremony', 'Honor the Dead', 'Ritual of Retribution',
            'Cleansing Ritual', 'Purify', 'Cleanse',
            'Restoring Aura', 'Repentance', 'Restoring Spirit',
            'Radiant Ward', 'Blazing Shield', 'Sun Shield'
        ],
        
        # Warden Skill Lines
        'Animal Companions': [
            # Ultimate
            'Feral Guardian', 'Eternal Guardian', 'Soul Shriven Guardian',
            # Active Skills
            'Cutting Dive', 'Screaming Cliff Racer', 'Dive',
            'Falcon\'s Swiftness', 'Bird of Prey', 'Falcon\'s Blessing',
            'Fletcher Infection', 'Deep Fissure', 'Subterranean Assault',
            'Betty Netch', 'Blue Betty', 'Green Lotus',
            'Swarm', 'Fetcher Infection', 'Leeching Vines'
        ],
        
        'Green Balance': [
            # Ultimate
            'Secluded Grove', 'Healing Thicket', 'Enchanted Grove',
            # Active Skills
            'Living Vines', 'Living Trellis', 'Living Vines',
            'Leeching Vines', 'Fetcher Infection', 'Swarm',
            'Healing Seed', 'Budding Seeds', 'Living Seeds',
            'Lotus Blossom', 'Living Trellis', 'Living Vines',
            'Enchanted Growth', 'Living Vines', 'Living Trellis'
        ],
        
        'Winter\'s Embrace': [
            # Ultimate
            'Sleet Storm', 'Northern Storm', 'Permafrost',
            # Active Skills
            'Impaling Shards', 'Winter\'s Revenge', 'Impaling Shards',
            'Frozen Device', 'Frozen Gate', 'Frozen Device',
            'Frozen Gate', 'Frozen Device', 'Frozen Gate',
            'Expansive Frost Cloak', 'Expansive Frost Cloak', 'Expansive Frost Cloak',
            'Expansive Frost Cloak', 'Expansive Frost Cloak', 'Expansive Frost Cloak'
        ],
        
        # Necromancer Skill Lines
        'Bone Tyrant': [
            # Ultimate
            'Bone Goliath Transformation', 'Pummeling Goliath', 'Ravenous Goliath',
            # Active Skills
            'Bone Armor', 'Beckoning Armor', 'Bone Prison',
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest',
            'Bone Prison', 'Beckoning Armor', 'Bone Armor',
            'Bone Prison', 'Beckoning Armor', 'Bone Armor',
            'Bone Prison', 'Beckoning Armor', 'Bone Armor'
        ],
        
        'Grave Lord': [
            # Ultimate
            'Pummeling Goliath', 'Ravenous Goliath', 'Bone Goliath Transformation',
            # Active Skills
            'Blastbones', 'Blastbones', 'Blastbones',
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest',
            'Blastbones', 'Blastbones', 'Blastbones',
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest',
            'Blastbones', 'Blastbones', 'Blastbones'
        ],
        
        'Living Death': [
            # Ultimate
            'Ravenous Goliath', 'Bone Goliath Transformation', 'Pummeling Goliath',
            # Active Skills
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest',
            'Blastbones', 'Blastbones', 'Blastbones',
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest',
            'Blastbones', 'Blastbones', 'Blastbones',
            'Bitter Harvest', 'Bitter Harvest', 'Bitter Harvest'
        ],
        
        # Arcanist Skill Lines
        'Herald of the Tome': [
            # Ultimate
            'The Unfathomable Darkness', 'The Unfathomable Darkness', 'The Unfathomable Darkness',
            # Active Skills
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver'
        ],
        
        'Soldier of Apocrypha': [
            # Ultimate
            'The Unfathomable Darkness', 'The Unfathomable Darkness', 'The Unfathomable Darkness',
            # Active Skills
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail'
        ],
        
        'Curative Runeforms': [
            # Ultimate
            'The Unfathomable Darkness', 'The Unfathomable Darkness', 'The Unfathomable Darkness',
            # Active Skills
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver',
            'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail', 'Cephaliarch\'s Flail',
            'Fatecarver', 'Fatecarver', 'Fatecarver'
        ]
    }

    def __init__(self):
        """Initialize the subclass analyzer."""
        # Create reverse mapping from ability name to skill line
        self.ability_to_skill_line = {}
        for skill_line, abilities in self.SKILL_LINE_ABILITIES.items():
            for ability in abilities:
                self.ability_to_skill_line[ability.lower()] = skill_line

    def analyze_subclasses(self, abilities: List[str]) -> List[str]:
        """
        Analyze a list of ability names to determine the player's subclasses.
        
        Args:
            abilities: List of ability names
            
        Returns:
            List of 3 subclass abbreviations (e.g., ['Ass', 'Herald', 'Ardent'])
        """
        skill_line_counts = defaultdict(int)
        
        # Count abilities from each skill line
        for ability in abilities:
            ability_lower = ability.lower().strip()
            
            # Direct match
            if ability_lower in self.ability_to_skill_line:
                skill_line = self.ability_to_skill_line[ability_lower]
                skill_line_counts[skill_line] += 1
                continue
            
            # Partial match (for morphed abilities)
            for known_ability, skill_line in self.ability_to_skill_line.items():
                if ability_lower in known_ability or known_ability in ability_lower:
                    skill_line_counts[skill_line] += 1
                    break
        
        # Get top 3 skill lines
        sorted_skill_lines = sorted(skill_line_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Convert to abbreviations
        subclasses = []
        for skill_line, count in sorted_skill_lines[:3]:
            abbreviation = self._get_skill_line_abbreviation(skill_line)
            subclasses.append(abbreviation)
        
        # Pad with 'x' if we don't have 3 subclasses
        while len(subclasses) < 3:
            subclasses.append('x')
        
        logger.debug(f"Analyzed {len(abilities)} abilities -> subclasses: {subclasses}")
        return subclasses

    def _get_skill_line_abbreviation(self, skill_line: str) -> str:
        """Get abbreviation for a skill line."""
        # Check aliases first
        if skill_line in self.SKILL_LINE_ALIASES:
            return self.SKILL_LINE_ALIASES[skill_line]
        
        # Generate abbreviation from skill line name
        if skill_line == 'Ardent Flame':
            return 'Ardent'
        elif skill_line == 'Draconic Power':
            return 'Draconic'
        elif skill_line == 'Earthen Heart':
            return 'Earthen'
        elif skill_line == 'Dark Magic':
            return 'Dark'
        elif skill_line == 'Daedric Summoning':
            return 'Daedric'
        elif skill_line == 'Storm Calling':
            return 'Storm'
        elif skill_line == 'Assassination':
            return 'Ass'
        elif skill_line == 'Shadow':
            return 'Shadow'
        elif skill_line == 'Siphoning':
            return 'Siphon'
        elif skill_line == 'Aedric Spear':
            return 'Spear'
        elif skill_line == 'Dawn\'s Wrath':
            return 'Dawn'
        elif skill_line == 'Restoring Light':
            return 'Resto'
        elif skill_line == 'Animal Companions':
            return 'Animal'
        elif skill_line == 'Green Balance':
            return 'Green'
        elif skill_line == 'Winter\'s Embrace':
            return 'Winter'
        elif skill_line == 'Bone Tyrant':
            return 'Bone'
        elif skill_line == 'Grave Lord':
            return 'Grave'
        elif skill_line == 'Living Death':
            return 'Living'
        elif skill_line == 'Herald of the Tome':
            return 'Herald'
        elif skill_line == 'Soldier of Apocrypha':
            return 'Soldier'
        elif skill_line == 'Curative Runeforms':
            return 'Curative'
        else:
            # Fallback: take first word and truncate
            words = skill_line.split()
            if words:
                return words[0][:6]
            return 'x'

    def get_skill_line_for_ability(self, ability_name: str) -> Optional[str]:
        """Get the skill line for a given ability name."""
        ability_lower = ability_name.lower().strip()
        
        # Direct match
        if ability_lower in self.ability_to_skill_line:
            return self.ability_to_skill_line[ability_lower]
        
        # Partial match
        for known_ability, skill_line in self.ability_to_skill_line.items():
            if ability_lower in known_ability or known_ability in ability_lower:
                return skill_line
        
        return None
