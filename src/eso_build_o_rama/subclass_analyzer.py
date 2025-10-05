#!/usr/bin/env python3
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
            'Radiant Destruction', 'Radiant Glory', 'Radiant Oppression'
        ],
        
        'Restoring Light': [
            # Ultimate
            'Rite of Passage', 'Practiced Incantation', 'Remembrance',
            # Active Skills
            'Rushed Ceremony', 'Breath of Life', 'Honor the Dead',
            'Healing Ritual', 'Ritual of Rebirth', 'Hasty Prayer',
            'Restoring Aura', 'Radiant Aura', 'Repentance',
            'Cleansing Ritual', 'Purifying Ritual', 'Extended Ritual',
            'Rune Focus', 'Channeled Focus', 'Restoring Focus'
        ],
        
        # Warden Skill Lines
        'Animal Companions': [
            # Ultimate
            'Feral Guardian', 'Eternal Guardian', 'Wild Guardian',
            # Active Skills
            'Dive', 'Cutting Dive', 'Screaming Cliff Racer',
            'Scorch', 'Subterranean Assault', 'Deep Fissure',
            'Swarm', 'Fetcher Infection', 'Growing Swarm',
            'Betty Netch', 'Blue Betty', 'Bull Netch',
            'Falcon\'s Swiftness', 'Deceptive Predator', 'Bird of Prey'
        ],
        
        'Green Balance': [
            # Ultimate
            'Secluded Grove', 'Enchanted Forest', 'Healing Thicket',
            # Active Skills
            'Fungal Growth', 'Enchanted Growth', 'Soothing Spores',
            'Healing Seed', 'Budding Seeds', 'Corrupting Pollen',
            'Living Vines', 'Leeching Vines', 'Nature\'s Grasp',
            'Lotus Flower', 'Green Lotus', 'Lotus Blossom',
            'Nature\'s Gift', 'Nature\'s Embrace', 'Emerald Moss'
        ],
        
        'Winter\'s Embrace': [
            # Ultimate
            'Sleet Storm', 'Northern Storm', 'Permafrost',
            # Active Skills
            'Frost Cloak', 'Expansive Frost Cloak', 'Ice Cloak',
            'Impaling Shards', 'Gripping Shards', 'Winter\'s Revenge',
            'Arctic Wind', 'Arctic Blast', 'Polar Wind',
            'Crystallized Shield', 'Crystallized Slab', 'Shimmering Shield',
            'Frozen Gate', 'Frozen Device', 'Frozen Retreat'
        ],
        
        # Necromancer Skill Lines
        'Grave Lord': [
            # Ultimate
            'Frozen Colossus', 'Pestilent Colossus', 'Glacial Colossus',
            # Active Skills
            'Flame Skull', 'Ricochet Skull', 'Venom Skull',
            'Sacrificial Bones', 'Blighted Blastbones', 'Grave Lord\'s Sacrifice',
            'Boneyard', 'Unnerving Boneyard', 'Avid Boneyard',
            'Skeletal Mage', 'Skeletal Archer', 'Skeletal Arcanist',
            'Shocking Siphon', 'Detonating Siphon', 'Mystic Siphon'
        ],
        
        'Bone Tyrant': [
            # Ultimate
            'Bone Goliath Transformation', 'Pummeling Goliath', 'Ravenous Goliath',
            # Active Skills
            'Death Scythe', 'Ruinous Scythe', 'Hungry Scythe',
            'Bone Armor', 'Beckoning Armor', 'Summoner\'s Armor',
            'Bitter Harvest', 'Deaden Pain', 'Necrotic Potency',
            'Bone Totem', 'Remote Totem', 'Agony Totem',
            'Grave Grasp', 'Ghostly Embrace', 'Empowering Grasp'
        ],
        
        'Living Death': [
            # Ultimate
            'Reanimate', 'Renewing Animation', 'Animate Blastbones',
            # Active Skills
            'Render Flesh', 'Resistant Flesh', 'Blood Sacrifice',
            'Life amid Death', 'Enduring Undeath', 'Renewing Undeath',
            'Spirit Mender', 'Spirit Guardian', 'Intensive Mender',
            'Restoring Tether', 'Braided Tether', 'Mortal Coil',
            'Expunge', 'Expunge and Modify', 'Hexproof'
        ],
        
        # Arcanist Skill Lines
        'Herald of the Tome': [
            # Ultimate
            'The Tide King\'s Gaze', 'The Languid Eye', 'The Unblinking Eye',
            # Active Skills
            'Runeblades', 'Writhing Runeblades', 'Escalating Runeblades',
            'Fatecarver', 'Pragmatic Fatecarver', 'Exhausting Fatecarver',
            'Abyssal Impact', 'Tentacular Dread', 'Cephaliarch\'s Flail',
            'Tome-Bearer\'s Inspiration', 'Inspired Scholarship', 'Recuperative Treatise',
            'The Imperfect Ring', 'Rune of Displacement', 'Fulminating Rune'
        ],
        
        'Curative Runeforms': [
            # Ultimate
            'Vitalizing Glyphic', 'Glyphic of the Tides', 'Resonating Glyphic',
            # Active Skills
            'Runemend', 'Evolving Runemend', 'Audacious Runemend',
            'Remedy Cascade', 'Cascading Fortune', 'Curative Surge',
            'Chakram of Destiny', 'Chakram\'s Havoc', 'Kinetic Aegis',
            'Arcanist\'s Domain', 'Reconstructive Domain', 'Zenas\' Empowering Disc',
            'Apocryphal Gate', 'Fleet-footed Gate', 'Passage Between Worlds'
        ],
        
        'Soldier of Apocrypha': [
            # Ultimate
            'Gibbering Shield', 'Sanctum of the Abyssal Sea', 'Gibbering Shelter',
            # Active Skills
            'Runic Jolt', 'Runic Sunder', 'Runic Embrace',
            'Runespite Ward', 'Spiteward of the Lucid Mind', 'Impervious Runeward',
            'Fatewoven Armor', 'Cruxweaver Armor', 'Unbreakable Fate',
            'Runic Defense', 'Runeguard of Still Waters', 'Runeguard of Freedom',
            'Rune of Eldritch Horror', 'Rune of Uncanny Adoration', 'Rune of the Colorless Pool'
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
        # Convert to set for the analyze_subclass method
        abilities_set = set(abilities)
        
        # Use the proper analyze_subclass method
        result = self.analyze_subclass(abilities_set)
        skill_lines = result.get('skill_lines', [])
        
        # Convert to abbreviations
        subclasses = []
        for skill_line in skill_lines[:3]:  # Take top 3
            abbreviation = self._get_skill_line_abbreviation(skill_line)
            subclasses.append(abbreviation)
        
        # Pad with 'x' if we don't have 3 subclasses
        while len(subclasses) < 3:
            subclasses.append('x')
        
        logger.debug(f"Analyzed {len(abilities)} abilities -> subclasses: {subclasses}")
        return subclasses

    def analyze_subclass(self, abilities: Set[str]) -> Dict[str, any]:
        """Analyze abilities to infer skill lines."""
        if not abilities:
            return {'skill_lines': [], 'confidence': 0.0, 'role': 'unknown'}

        # Clean ability names for better matching
        clean_abilities = {self._clean_ability_name(ability) for ability in abilities}
        logger.debug(f"Analyzing abilities: {clean_abilities}")

        # Find skill lines that have at least one matching ability
        detected_skill_lines = []
        for skill_line, skill_abilities in self.SKILL_LINE_ABILITIES.items():
            if any(self._ability_matches(ability, clean_ability) 
                   for ability in skill_abilities 
                   for clean_ability in clean_abilities):
                detected_skill_lines.append(skill_line)

        # Create a list of unique skill lines (preserving order)
        seen = set()
        unique_skill_lines = []
        for skill_line in detected_skill_lines:
            if skill_line not in seen:
                unique_skill_lines.append(skill_line)
                seen.add(skill_line)
        top_skill_lines = unique_skill_lines

        # Simple confidence: 1.0 if we found skill lines, 0.0 if not
        confidence = 1.0 if top_skill_lines else 0.0

        logger.debug(f"Detected skill lines: {top_skill_lines} (confidence: {confidence})")

        return {
            'skill_lines': top_skill_lines,
            'confidence': confidence,
            'role': self._infer_role_from_skill_lines(top_skill_lines, abilities)
        }
    
    def _infer_role_from_skill_lines(self, skill_lines: List[str], abilities: Set[str]) -> str:
        """Infer role from detected skill lines and abilities."""
        # Role detection based on skill lines and abilities
        if not skill_lines:
            return 'unknown'
        
        # Check for healing abilities
        healing_abilities = {
            'Breath of Life', 'Honor the Dead', 'Healing Ritual', 'Combat Prayer', 
            'Rapid Regeneration', 'Healing Springs', 'Radiating Regeneration',
            'Restoring Aura', 'Radiant Aura', 'Repentance', 'Rushed Ceremony',
            'Ritual of Rebirth', 'Hasty Prayer', 'Cleansing Ritual', 'Purifying Ritual',
            'Extended Ritual', 'Rune Focus', 'Channeled Focus', 'Restoring Focus',
            'Runemend', 'Evolving Runemend', 'Audacious Runemend', 'Remedy Cascade',
            'Cascading Fortune', 'Curative Surge', 'Healing Seed', 'Budding Seeds',
            'Corrupting Pollen', 'Living Vines', 'Leeching Vines', 'Nature\'s Grasp',
            'Lotus Flower', 'Green Lotus', 'Lotus Blossom', 'Nature\'s Gift',
            'Nature\'s Embrace', 'Emerald Moss', 'Fungal Growth', 'Enchanted Growth',
            'Soothing Spores'
        }
        if any(ability in abilities for ability in healing_abilities):
            return 'healer'
        
        # Check for tank abilities
        tank_abilities = {
            'Pierce Armor', 'Inner Rage', 'Heroic Slash', 'Defensive Posture', 
            'Absorb Magic', 'Puncture', 'Ransack', 'Stone Giant', 'Obsidian Shard',
            'Molten Weapons', 'Igneous Weapons', 'Molten Armaments', 'Obsidian Shield',
            'Igneous Shield', 'Fragmented Shield', 'Spiked Armor', 'Hardened Armor',
            'Volatile Armor', 'Dark Talons', 'Burning Talons', 'Choking Talons',
            'Dragon Blood', 'Green Dragon Blood', 'Coagulating Blood', 'Reflective Scale',
            'Dragon Fire Scale', 'Reflective Plate', 'Bone Armor', 'Beckoning Armor',
            'Summoner\'s Armor', 'Runespite Ward', 'Spiteward of the Lucid Mind',
            'Impervious Runeward', 'Fatewoven Armor', 'Cruxweaver Armor', 'Unbreakable Fate',
            'Runic Defense', 'Runeguard of Still Waters', 'Runeguard of Freedom'
        }
        if any(ability in abilities for ability in tank_abilities):
            return 'tank'
        
        # Check for DPS abilities
        dps_abilities = {
            'Crystal Fragments', 'Force Pulse', 'Wrecking Blow', 'Biting Jabs', 
            'Scorched Earth', 'Lava Whip', 'Molten Whip', 'Flame Lash',
            'Searing Strike', 'Venomous Claw', 'Burning Embers', 'Fiery Breath',
            'Noxious Breath', 'Engulfing Flames', 'Inferno', 'Flames of Oblivion',
            'Cauterize', 'Mages\' Fury', 'Mages\' Wrath', 'Endless Fury',
            'Lightning Splash', 'Liquid Lightning', 'Lightning Flood', 'Surge',
            'Power Surge', 'Critical Surge', 'Assassin\'s Blade', 'Killer\'s Blade',
            'Impale', 'Teleport Strike', 'Ambush', 'Lotus Fan', 'Veiled Strike',
            'Surprise Attack', 'Concealed Weapon', 'Puncturing Strikes', 'Puncturing Sweep',
            'Piercing Javelin', 'Aurora Javelin', 'Binding Javelin', 'Focused Charge',
            'Explosive Charge', 'Toppling Charge', 'Spear Shards', 'Luminous Shards',
            'Blazing Spear', 'Sun Fire', 'Vampire\'s Bane', 'Reflective Light',
            'Solar Flare', 'Dark Flare', 'Solar Barrage', 'Backlash', 'Purifying Light',
            'Power of the Light', 'Radiant Destruction', 'Radiant Glory', 'Radiant Oppression',
            'Dive', 'Cutting Dive', 'Screaming Cliff Racer', 'Scorch', 'Subterranean Assault',
            'Deep Fissure', 'Swarm', 'Fetcher Infection', 'Growing Swarm',
            'Flame Skull', 'Ricochet Skull', 'Venom Skull', 'Blastbones',
            'Blighted Blastbones', 'Stalking Blastbones', 'Boneyard', 'Unnerving Boneyard',
            'Avid Boneyard', 'Skeletal Mage', 'Skeletal Archer', 'Skeletal Arcanist',
            'Death Scythe', 'Ruinous Scythe', 'Hungry Scythe', 'Runeblades',
            'Writhing Runeblades', 'Escalating Runeblades', 'Fatecarver', 'Pragmatic Fatecarver',
            'Exhausting Fatecarver', 'Abyssal Impact', 'Tentacular Dread', 'Cephaliarch\'s Flail'
        }
        if any(ability in abilities for ability in dps_abilities):
            return 'dps'
        
        # Default role based on skill lines
        if 'Restoring Light' in skill_lines or 'Curative Runeforms' in skill_lines or 'Green Balance' in skill_lines:
            return 'healer'
        elif 'Aedric Spear' in skill_lines or 'Dawn\'s Wrath' in skill_lines or 'Ardent Flame' in skill_lines or 'Storm Calling' in skill_lines or 'Dark Magic' in skill_lines or 'Assassination' in skill_lines or 'Shadow' in skill_lines or 'Siphoning' in skill_lines or 'Animal Companions' in skill_lines or 'Grave Lord' in skill_lines or 'Living Death' in skill_lines or 'Herald of the Tome' in skill_lines or 'Soldier of Apocrypha' in skill_lines:
            return 'dps'
        else:
            return 'dps'  # Default to DPS

    def _clean_ability_name(self, ability: str) -> str:
        """Clean ability name for better matching."""
        # Remove common prefixes/suffixes
        cleaned = ability.replace('Heavy Attack', '').replace('Light Attack', '')
        cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)  # Remove parenthetical content
        return cleaned.strip()

    def _ability_matches(self, pattern: str, ability: str) -> bool:
        """Check if an ability matches a pattern."""
        pattern_lower = pattern.lower()
        ability_lower = ability.lower()
        return pattern_lower in ability_lower or ability_lower in pattern_lower

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