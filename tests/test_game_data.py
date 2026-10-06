"""
Skill-line detection and ESO-Hub links against the imported game data bundle.

The fixture docs/handoff/referenced-abilities-u49-u50.json lists every ability
slotted by top players in the site's U49 and U50 data; the bundle under
data/game/u51 must resolve all of it (see docs/GAME_ASSET_BUNDLE.md section 1).
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.eso_build_o_rama.game_data import GameData, ESO_HUB_BASE  # noqa: E402
from src.eso_build_o_rama.models import Ability, CommonBuild, PlayerBuild  # noqa: E402
from src.eso_build_o_rama.subclass_analyzer import ESOSubclassAnalyzer  # noqa: E402
from src.eso_build_o_rama.data_store import DataStore  # noqa: E402
from src.eso_build_o_rama.page_generator import PageGenerator  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "docs" / "handoff" / "referenced-abilities-u49-u50.json"

CLASS_FAMILIES = (
    "ability_dragonknight", "ability_sorcerer", "ability_nightblade", "ability_templar",
    "ability_warden", "ability_necromancer", "ability_arcanist",
)
# Skills renamed in the 2026 class rework that the legacy name table does not know.
RENAMED = {
    28311: "Vibrant Shroud", 34727: "Healthy Offering", 186209: "Tidal Chakram",
    32785: "Heart of Flame", 20328: "Earthshield Mantle", 20496: "Chains of Dominance",
    31816: "Magma Fist", 20917: "Dragonfire Breath", 22259: "Ritual of Retribution",
    86130: "Ice Fortress",
}


@pytest.fixture(scope="module")
def game_data():
    data = GameData.load("u51")
    if data is None or data.update != "u51":
        pytest.skip("data/game/u51 bundle not imported")
    return data


@pytest.fixture(scope="module")
def fixture_rows():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))["abilities"]


def test_bundle_has_the_21_class_lines(game_data):
    assert len(game_data.class_lines) == 21
    assert game_data.class_lines["Herald of the Tome"] == "Arcanist"
    assert game_data.native_lines("DragonKnight") == ["Ardent Flame", "Draconic Power", "Earthen Heart"]
    assert not any(name.startswith("Class Mastery") for name in game_data.class_lines)


def test_every_fixture_row_resolves(game_data, fixture_rows):
    # Resolved means the id is in the table (even with no skill line, as for a
    # mythic's granted skill such as Crypt Transfer) or the grimoire icon is known.
    unresolved = [
        (row["ability_id"], row["name"]) for row in fixture_rows
        if game_data.ability(row["ability_id"]) is None
        and game_data.skill_line_for(row["ability_id"], row["icon"]) is None
    ]
    assert unresolved == []


def test_class_icon_rows_map_to_class_lines(game_data, fixture_rows):
    misses = [
        (row["ability_id"], row["name"]) for row in fixture_rows
        if row["icon"].startswith(CLASS_FAMILIES)
        and not game_data.is_class_line(game_data.skill_line_for(row["ability_id"], row["icon"]))
    ]
    assert misses == []


def test_renamed_skills_resolve_to_class_lines(game_data):
    for ability_id, name in RENAMED.items():
        entry = game_data.ability(ability_id)
        assert entry is not None and entry["name"] == name, (ability_id, name)
        assert game_data.is_class_line(entry["skill_line"]), (name, entry["skill_line"])


def test_substring_false_positives_are_not_class_lines(game_data):
    assert game_data.skill_line_for(38745) == "Two Handed"      # Carve, not Herald (Fatecarver)
    assert game_data.skill_line_for(85187) == "Dual Wield"      # Rend, not Living Death (Render Flesh)
    assert game_data.skill_line_for(42176) == "Undaunted"       # Bone Surge, not Storm Calling (Surge)


def test_scribed_pseudo_ids_resolve_by_grimoire_icon(game_data, fixture_rows):
    scribed = [row for row in fixture_rows if row["icon"].startswith("ability_grimoire_")]
    assert scribed, "fixture should contain scribed skills"
    for row in scribed:
        line = game_data.skill_line_for(row["ability_id"], row["icon"])
        assert line is not None and not game_data.is_class_line(line), row


def test_analyze_player_pads_from_class(game_data):
    analyzer = ESOSubclassAnalyzer(game_data=game_data)
    bars = [Ability(ability_id=183006, ability_name="Cephaliarch's Flail", ability_icon="ability_arcanist_003_a"),
            Ability(ability_id=38745, ability_name="Carve", ability_icon="ability_2handed_002_a")]
    subclasses, padded = analyzer.analyze_player(bars, "Arcanist")
    assert sorted(subclasses) == ["Curative", "Herald", "Soldier"]
    assert sorted(padded) == ["Curative", "Soldier"]


def test_analyze_player_cross_class_pads_only_the_missing_line(game_data, fixture_rows):
    dawn = next(row for row in fixture_rows
                if game_data.skill_line_for(row["ability_id"], row["icon"]) == "Dawn's Wrath")
    analyzer = ESOSubclassAnalyzer(game_data=game_data)
    bars = [Ability(ability_id=183006, ability_name="Cephaliarch's Flail", ability_icon="ability_arcanist_003_a"),
            Ability(ability_id=dawn["ability_id"], ability_name=dawn["name"], ability_icon=dawn["icon"])]
    subclasses, padded = analyzer.analyze_player(bars, "Arcanist")
    assert "Dawn" in subclasses and "Herald" in subclasses
    assert len(subclasses) == 3 and len(padded) == 1 and padded[0] in ("Curative", "Soldier")


def test_analyze_player_without_evidence_stays_x(game_data):
    # Empty or unreadable bars must not become an invented three-line class build.
    analyzer = ESOSubclassAnalyzer(game_data=game_data)
    bars = [Ability(ability_id=0, ability_name="Empty", ability_icon=""),
            Ability(ability_id=None, ability_name="", ability_icon="")]
    assert analyzer.analyze_player(bars, "Arcanist") == (["x", "x", "x"], [])


def test_analyze_player_weapon_only_bars_pad_from_class(game_data):
    # Real abilities but no class skill: the class is known, so its lines are padded.
    analyzer = ESOSubclassAnalyzer(game_data=game_data)
    subclasses, padded = analyzer.analyze_player(
        [Ability(ability_id=38745, ability_name="Carve", ability_icon="ability_2handed_002_a")], "Dragonknight")
    assert sorted(subclasses) == ["Ardent", "Draconic", "Earthen"] and sorted(padded) == sorted(subclasses)


def test_publish_path_keeps_padded_lines_from_best_player(game_data):
    import asyncio
    from src.eso_build_o_rama.models import TrialReport
    from src.eso_build_o_rama.trial_scanner import TrialScanner

    def player(name, dps, padded):
        return PlayerBuild(character_name=name, class_name="Arcanist", role="dps", dps=dps, report_code=f"r{dps}",
                           subclasses=["Herald", "Curative", "Soldier"], subclasses_padded=padded,
                           sets_equipped={"Deadly Strike": 5, "Ansuul's Torment": 5})

    weak, strong = player("A", 1000, ["Curative", "Soldier"]), player("B", 2000, ["Soldier"])
    report = TrialReport(trial_name="Aetherian Archive", boss_name="The Mage", fight_id=3, report_code="r1",
                         update_version="u51")
    report.common_builds = [
        CommonBuild(build_slug="curative-herald-soldier-x-y", subclasses=weak.subclasses,
                    subclasses_padded=weak.subclasses_padded, best_player=weak, all_players=[weak],
                    trial_name=report.trial_name, boss_name=report.boss_name),
        CommonBuild(build_slug="curative-herald-soldier-x-y", subclasses=strong.subclasses,
                    subclasses_padded=strong.subclasses_padded, best_player=strong, all_players=[strong],
                    trial_name=report.trial_name, boss_name=report.boss_name),
    ]
    scanner = TrialScanner(api_client=object())
    published = asyncio.run(scanner.get_publishable_builds({"Aetherian Archive": [report]}))
    assert len(published) == 1
    assert published[0].best_player.character_name == "B"
    assert published[0].subclasses_padded == ["Soldier"]
    fallback = scanner._create_fallback_build(weak, report)
    assert fallback.subclasses_padded == ["Curative", "Soldier"]


def test_analyze_player_unknown_class_pads_with_x(game_data):
    analyzer = ESOSubclassAnalyzer(game_data=game_data)
    subclasses, padded = analyzer.analyze_player(
        [Ability(ability_id=183006, ability_name="Cephaliarch's Flail", ability_icon="ability_arcanist_003_a")], "")
    assert subclasses == ["Herald", "x", "x"] and padded == []


def test_legacy_name_path_without_game_data():
    analyzer = ESOSubclassAnalyzer(game_data=None, load_game_data=False)
    subclasses, padded = analyzer.analyze_player(
        [Ability(ability_id=0, ability_name="Lava Whip", ability_icon="")], "DragonKnight")
    assert "Ardent" in subclasses and sorted(padded) == ["Draconic", "Earthen"]
    # The old name-list entry point still works for callers that have names only.
    assert "Ardent" in analyzer.analyze_subclasses(["Lava Whip"])


def test_display_parts_mark_padded_lines():
    build = CommonBuild(
        subclasses=["Herald", "Curative", "Soldier"], subclasses_padded=["Curative", "Soldier"],
        best_player=PlayerBuild(class_name="Arcanist"),
    )
    parts = build.get_display_parts(abbreviated=True)
    assert parts == [("Curative", True, True), ("Herald", True, False), ("Soldier", True, True)]


def test_display_parts_fall_back_to_best_player_padding():
    # Consolidation paths construct the build from players; the player's list must count.
    build = CommonBuild(
        subclasses=["Herald", "Curative", "Soldier"],
        best_player=PlayerBuild(class_name="Arcanist", subclasses_padded=["Curative", "Soldier"]),
    )
    assert build.get_padded_subclasses() == ["Curative", "Soldier"]
    assert [p for p in build.get_display_parts(abbreviated=True) if p[2]] == [("Curative", True, True), ("Soldier", True, True)]


def test_data_store_round_trips_padded_lines(tmp_path):
    store = DataStore(builds_file=str(tmp_path / "builds.json"))
    player = PlayerBuild(character_name="A", class_name="Arcanist",
                         subclasses=["Herald", "Curative", "Soldier"], subclasses_padded=["Curative", "Soldier"])
    build = CommonBuild(build_slug="curative-herald-soldier-a-b", subclasses=player.subclasses,
                        subclasses_padded=player.subclasses_padded, best_player=player, all_players=[player])
    data = store._serialize_build(build)
    back = store._deserialize_build(data)
    assert back.subclasses_padded == ["Curative", "Soldier"]
    assert back.best_player.subclasses_padded == ["Curative", "Soldier"]
    # builds.json written before this field existed deserialises to no padding.
    del data["subclasses_padded"]
    del data["best_player"]["subclasses_padded"]
    old = store._deserialize_build(data)
    assert old.subclasses_padded == [] and old.best_player.subclasses_padded == []


def test_esohub_urls_from_game_data(game_data):
    assert game_data.set_esohub_url("Slimecraw") == f"{ESO_HUB_BASE}/en/sets/slimecraw"
    assert game_data.set_esohub_url(set_id=270) == f"{ESO_HUB_BASE}/en/sets/slimecraw"
    assert game_data.set_esohub_url("No Such Set") is None
    assert game_data.mundus_esohub_url("The Warrior") == f"{ESO_HUB_BASE}/en/mundus-stones/the-warrior"


def test_page_generator_link_filters(game_data):
    generator = PageGenerator.__new__(PageGenerator)
    generator.game_data = game_data
    assert generator._eso_hub_mundus_url("The Thief") == f"{ESO_HUB_BASE}/en/mundus-stones/the-thief"
    assert generator._eso_hub_set_url("Perfected Ansuul's Torment").startswith(f"{ESO_HUB_BASE}/en/sets/")
    generator.game_data = None
    assert generator._eso_hub_mundus_url("The Thief") == f"{ESO_HUB_BASE}/en/mundus-stones/the-thief"
    assert generator._eso_hub_set_url("Deadly Strike") == f"{ESO_HUB_BASE}/en/sets/deadly-strike"
    assert generator._eso_hub_mundus_url("") == "#"
