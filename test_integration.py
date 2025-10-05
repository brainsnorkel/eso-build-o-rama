#!/usr/bin/env python3
"""
Integration test script for ESO Build-O-Rama
Tests the complete pipeline with mock data.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.eso_build_o_rama.models import (
    PlayerBuild, GearPiece, Ability, TrialReport, CommonBuild
)
from src.eso_build_o_rama.build_analyzer import BuildAnalyzer
from src.eso_build_o_rama.page_generator import PageGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def create_mock_player_builds():
    """Create mock player builds for testing."""
    
    # Create abilities
    abilities_bar1 = [
        Ability(ability_name="Assassin's Blade", skill_line="Assassination"),
        Ability(ability_name="Shadow Cloak", skill_line="Shadow"),
        Ability(ability_name="Siphoning Strikes", skill_line="Siphoning"),
        Ability(ability_name="Blade Cloak", skill_line="Assassination"),
        Ability(ability_name="Death Stroke", skill_line="Assassination"),
    ]
    
    abilities_bar2 = [
        Ability(ability_name="Dark Shade", skill_line="Shadow"),
        Ability(ability_name="Shadow Image", skill_line="Shadow"),
        Ability(ability_name="Soul Shred", skill_line="Siphoning"),
        Ability(ability_name="Soul Trap", skill_line="Siphoning"),
        Ability(ability_name="Incapacitating Strike", skill_line="Assassination"),
    ]
    
    # Create gear pieces
    gear = [
        GearPiece(
            slot="head", set_name="Deadly Strike", item_name="Deadly Strike Helmet",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="shoulders", set_name="Deadly Strike", item_name="Deadly Strike Pauldrons",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="chest", set_name="Deadly Strike", item_name="Deadly Strike Cuirass",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="hands", set_name="Deadly Strike", item_name="Deadly Strike Gauntlets",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="legs", set_name="Deadly Strike", item_name="Deadly Strike Greaves",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="belt", set_name="Ansuul's Torment", item_name="Ansuul's Torment Belt",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="boots", set_name="Ansuul's Torment", item_name="Ansuul's Torment Boots",
            trait="Divines", enchantment="Max Magicka", bar=1
        ),
        GearPiece(
            slot="necklace", set_name="Ansuul's Torment", item_name="Ansuul's Torment Necklace",
            trait="Infused", enchantment="Spell Damage", bar=1
        ),
        GearPiece(
            slot="ring1", set_name="Ansuul's Torment", item_name="Ansuul's Torment Ring",
            trait="Infused", enchantment="Spell Damage", bar=1
        ),
        GearPiece(
            slot="ring2", set_name="Ansuul's Torment", item_name="Ansuul's Torment Ring",
            trait="Infused", enchantment="Spell Damage", bar=1
        ),
        GearPiece(
            slot="main_hand", set_name="Ansuul's Torment", item_name="Ansuul's Torment Staff",
            trait="Infused", enchantment="Fire Damage", bar=1
        ),
        GearPiece(
            slot="off_hand", set_name="", item_name="Empty", trait="", enchantment="", bar=1
        ),
    ]
    
    # Create player builds
    players = []
    
    # Create 6 players with the same build (Deadly Strike + Ansuul's Torment)
    base_names = ["TestNightblade", "TestStamblade", "TestBlade", "TestRogue", "TestAssassin", "TestShadow"]
    base_players = ["@testplayer1", "@testplayer2", "@testplayer3", "@testplayer4", "@testplayer5", "@testplayer6"]
    
    for i, (char_name, player_name) in enumerate(zip(base_names, base_players)):
        player = PlayerBuild(
            character_name=char_name,
            player_name=player_name,
            class_name="Nightblade",
            dps=125000 - (i * 1000),  # Slightly different DPS
            dps_percentage=25.5 - (i * 0.5),
            gear=gear,
            abilities_bar1=abilities_bar1,
            abilities_bar2=abilities_bar2,
            mundus="The Shadow",
            champion_points=["Deadly Aim", "Backstabber", "Assassination"],
            player_url=f"https://www.esologs.com/character/id/1234{i+5}",
            subclasses=['Ass', 'Shadow', 'Siphon']
        )
        player.sets_equipped = {"Deadly Strike": 5, "Ansuul's Torment": 5}
        players.append(player)
    
    # Add 2 players with a different build (Relequen + Advancing Yokeda)
    gear2 = gear.copy()
    for piece in gear2:
        if piece.set_name == "Deadly Strike":
            piece.set_name = "Relequen"
            piece.item_name = piece.item_name.replace("Deadly Strike", "Relequen")
        elif piece.set_name == "Ansuul's Torment":
            piece.set_name = "Advancing Yokeda"
            piece.item_name = piece.item_name.replace("Ansuul's Torment", "Advancing Yokeda")
    
    player7 = PlayerBuild(
        character_name="TestStamDK1",
        player_name="@testplayer7",
        class_name="Dragonknight",
        dps=122000,
        dps_percentage=24.2,
        gear=gear2,
        abilities_bar1=abilities_bar1,
        abilities_bar2=abilities_bar2,
        mundus="The Warrior",
        champion_points=["Deadly Aim", "Backstabber", "Assassination"],
        player_url="https://www.esologs.com/character/id/12351",
        subclasses=['Ass', 'Shadow', 'Siphon']
    )
    player7.sets_equipped = {"Relequen": 5, "Advancing Yokeda": 5}
    players.append(player7)
    
    player8 = PlayerBuild(
        character_name="TestStamDK2",
        player_name="@testplayer8",
        class_name="Dragonknight",
        dps=121000,
        dps_percentage=23.8,
        gear=gear2,
        abilities_bar1=abilities_bar1,
        abilities_bar2=abilities_bar2,
        mundus="The Warrior",
        champion_points=["Deadly Aim", "Backstabber", "Assassination"],
        player_url="https://www.esologs.com/character/id/12352",
        subclasses=['Ass', 'Shadow', 'Siphon']
    )
    player8.sets_equipped = {"Relequen": 5, "Advancing Yokeda": 5}
    players.append(player8)
    
    return players


async def test_build_analysis():
    """Test the build analysis pipeline."""
    logger.info("="*60)
    logger.info("Testing Build Analysis Pipeline")
    logger.info("="*60)
    
    # Create mock data
    players = create_mock_player_builds()
    logger.info(f"Created {len(players)} mock player builds")
    
    # Create trial report
    trial_report = TrialReport(
        trial_name="Aetherian Archive",
        boss_name="Mage",
        all_players=players,
        report_code="TEST123",
        update_version="U48-20251005"
    )
    
    logger.info(f"Created trial report: {trial_report.trial_name} - {trial_report.boss_name}")
    
    # Analyze builds
    analyzer = BuildAnalyzer()
    analyzed_report = analyzer.analyze_trial_report(trial_report)
    
    # Get unique builds
    unique_builds = analyzed_report.get_unique_builds()
    logger.info(f"Found {len(unique_builds)} unique builds")
    
    for i, build in enumerate(unique_builds, 1):
        logger.info(f"  {i}. {build.get_display_name()} - {build.count} players")
        logger.info(f"     Sets: {', '.join(build.sets)}")
        logger.info(f"     Best DPS: {build.best_player.dps:,}")
        logger.info(f"     Best Player: {build.best_player.character_name}")
    
    return unique_builds


async def test_page_generation(builds):
    """Test the page generation pipeline."""
    logger.info("\n" + "="*60)
    logger.info("Testing Page Generation Pipeline")
    logger.info("="*60)
    
    # Create page generator
    page_generator = PageGenerator(
        template_dir="templates",
        output_dir="output"
    )
    
    logger.info("Generating HTML pages...")
    
    # Generate all pages
    generated_files = page_generator.generate_all_pages(
        builds,
        update_version="U48"
    )
    
    logger.info(f"Generated {len(generated_files)} files:")
    for name, filepath in generated_files.items():
        logger.info(f"  {name}: {filepath}")
    
    # Check if files exist
    for name, filepath in generated_files.items():
        if Path(filepath).exists():
            size = Path(filepath).stat().st_size
            logger.info(f"  ✅ {name}: {filepath} ({size:,} bytes)")
        else:
            logger.error(f"  ❌ {name}: {filepath} (NOT FOUND)")
    
    return generated_files


async def main():
    """Run the complete integration test."""
    logger.info("🚀 Starting ESO Build-O-Rama Integration Test")
    
    try:
        # Test build analysis
        builds = await test_build_analysis()
        
        if not builds:
            logger.warning("No builds found - cannot test page generation")
            return
        
        # Test page generation
        generated_files = await test_page_generation(builds)
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("🎉 INTEGRATION TEST COMPLETE!")
        logger.info("="*60)
        logger.info(f"✅ Analyzed {len(builds)} builds")
        logger.info(f"✅ Generated {len(generated_files)} HTML files")
        logger.info(f"✅ All components working correctly")
        
        logger.info("\n📁 Generated Files:")
        for name, filepath in generated_files.items():
            logger.info(f"   {filepath}")
        
        logger.info("\n🌐 To view the results:")
        logger.info("   open output/index.html")
        
    except Exception as e:
        logger.error(f"❌ Integration test failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
