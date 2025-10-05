"""
Tests for build analysis functionality.
"""

import sys
import os
import pytest

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.eso_build_o_rama.models import PlayerBuild, GearPiece, Ability, TrialReport
from src.eso_build_o_rama.subclass_analyzer import ESOSubclassAnalyzer
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer


def test_subclass_analyzer():
    """Test the subclass analyzer with known abilities."""
    analyzer = ESOSubclassAnalyzer()
    
    # Test with Nightblade abilities
    abilities = [
        "Assassin's Blade",
        "Teleport Strike", 
        "Grim Focus",
        "Shadow Cloak",
        "Siphoning Strikes"
    ]
    
    subclasses = analyzer.analyze_subclasses(abilities)
    
    assert len(subclasses) == 3
    assert 'Ass' in subclasses  # Assassination
    assert 'Shadow' in subclasses  # Shadow
    assert 'Siphon' in subclasses  # Siphoning


def test_build_slug_generation():
    """Test build slug generation."""
    player = PlayerBuild(
        character_name="Test Player",
        subclasses=["Ass", "Shadow", "Siphon"],
        sets_equipped={
            "Relequen": 5,
            "Deadly Strike": 5,
            "Slimecraw": 1
        }
    )
    
    slug = player.get_build_slug()
    expected = "ass-shadow-siphon-deadly-strike-relequen"  # Sets sorted alphabetically
    
    assert slug == expected


def test_gear_set_analysis():
    """Test gear set analysis with 2H weapons."""
    analyzer = BuildAnalyzer()
    
    # Create a player with 2H weapon
    player = PlayerBuild(
        character_name="Test Player",
        gear=[
            GearPiece(slot="head", set_name="Relequen", bar=1),
            GearPiece(slot="chest", set_name="Relequen", bar=1),
            GearPiece(slot="hands", set_name="Relequen", bar=1),
            GearPiece(slot="legs", set_name="Relequen", bar=1),
            GearPiece(slot="main_hand", set_name="Relequen", item_name="Greatsword of Relequen", bar=1),
            GearPiece(slot="off_hand", set_name="Relequen", item_name="Dagger of Relequen", bar=1),
        ]
    )
    
    # Analyze gear sets
    analyzer._analyze_gear_sets(player)
    
    # 2H weapon should count as 2 pieces
    assert player.sets_bar1["Relequen"] == 7  # 5 regular + 2 for 2H weapon
    assert player.sets_equipped["Relequen"] == 7


def test_common_build_identification():
    """Test identification of common builds."""
    analyzer = BuildAnalyzer()
    
    # Create trial report with multiple players having same build
    players = []
    for i in range(6):  # 6 players with same build (above threshold of 5)
        player = PlayerBuild(
            character_name=f"Player {i}",
            subclasses=["Ass", "Shadow", "Siphon"],
            sets_equipped={"Relequen": 5, "Deadly Strike": 5},
            dps=100000 + i * 1000  # Different DPS values
        )
        # Manually set the sets_equipped since the analyzer isn't running
        player.sets_equipped = {"Relequen": 5, "Deadly Strike": 5}
        players.append(player)
    
    # Add one player with different build
    different_player = PlayerBuild(
        character_name="Different Player",
        subclasses=["Ardent", "Draconic", "Earthen"],
        sets_equipped={"Burning Spellweave": 5, "Mother's Sorrow": 5},
        dps=95000
    )
    # Manually set the sets_equipped since the analyzer isn't running
    different_player.sets_equipped = {"Burning Spellweave": 5, "Mother's Sorrow": 5}
    players.append(different_player)
    
    trial_report = TrialReport(
        trial_name="Test Trial",
        boss_name="Test Boss",
        all_players=players
    )
    
    # Analyze the trial
    result = analyzer.analyze_trial_report(trial_report)
    
    # Should find one common build (5+ occurrences)
    unique_builds = result.get_unique_builds()
    assert len(unique_builds) == 1
    common_build = unique_builds[0]
    
    assert common_build.count == 6
    assert common_build.best_player.character_name == "Player 5"  # Highest DPS
    assert common_build.build_slug == "ass-shadow-siphon-deadly-strike-relequen"


def test_build_statistics():
    """Test build statistics generation."""
    analyzer = BuildAnalyzer()
    
    # Create trial report
    players = [
        PlayerBuild(character_name="Player 1", subclasses=["Ass", "Shadow", "Siphon"], sets_equipped={"Relequen": 5}),
        PlayerBuild(character_name="Player 2", subclasses=["Ass", "Shadow", "Siphon"], sets_equipped={"Relequen": 5}),
        PlayerBuild(character_name="Player 3", subclasses=["Ardent", "Draconic", "Earthen"], sets_equipped={"Burning Spellweave": 5}),
    ]
    
    trial_report = TrialReport(
        trial_name="Test Trial",
        all_players=players
    )
    
    stats = analyzer.get_build_statistics(trial_report)
    
    assert stats['total_players'] == 3
    assert stats['unique_builds'] == 2  # Two different builds
    assert 'Ass/Shadow/Siphon' in stats['subclass_distribution']
    assert stats['subclass_distribution']['Ass/Shadow/Siphon'] == 2


if __name__ == "__main__":
    # Run a simple test
    print("Testing build analysis...")
    
    # Test subclass analyzer
    analyzer = ESOSubclassAnalyzer()
    abilities = ["Assassin's Blade", "Shadow Cloak", "Siphoning Strikes"]
    subclasses = analyzer.analyze_subclasses(abilities)
    print(f"Abilities: {abilities}")
    print(f"Detected subclasses: {subclasses}")
    
    # Test build analyzer
    build_analyzer = BuildAnalyzer()
    player = PlayerBuild(
        character_name="Test Player",
        abilities_bar1=[Ability(ability_name="Assassin's Blade")],
        abilities_bar2=[Ability(ability_name="Shadow Cloak")],
        gear=[GearPiece(slot="head", set_name="Relequen")]
    )
    
    build_analyzer._analyze_player_build(player)
    print(f"Player subclasses: {player.subclasses}")
    print(f"Build slug: {player.get_build_slug()}")
    
    print("✅ Build analysis tests complete!")
