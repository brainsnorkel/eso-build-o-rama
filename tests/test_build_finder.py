"""
Tests for the Build Finder page (beads issue eso-build-o-rama-dp3).

Run from the project root: PageGenerator loads data files relative to it.
"""

import json
import os
import re
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.eso_build_o_rama.models import (
    CommonBuild,
    PlayerBuild,
    normalize_class_name,
)
from src.eso_build_o_rama.page_generator import PageGenerator

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = PROJECT_ROOT / "templates"
TRASH = "Trash Builds"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from deployment_check import DeploymentChecker  # noqa: E402


def make_build(
    trial,
    boss,
    role="dps",
    class_name="Nightblade",
    metric=100000.0,
    slug="ass-herald-ardent-deadly-strike-perfected-ansuuls-torment",
    player_url="",
    subclasses=("Ass", "Herald", "Ardent"),
    sets=("Deadly Strike", "Perfected Ansuul's Torment"),
    player_name="@Player",
):
    """Build a CommonBuild with a best_player suitable for rendering."""
    metrics = {"dps": "dps", "healer": "healing", "tank": "crowd_control"}
    player = PlayerBuild(
        player_name=player_name,
        character_name="Char",
        class_name=class_name,
        role=role,
        report_code="ABC123",
        fight_id=7,
        trial_name=trial,
        boss_name=boss,
        player_url=player_url,
        subclasses=list(subclasses),
        sets_equipped={s: 5 for s in sets},
        mundus="The Lady",
    )
    setattr(player, metrics[role], metric)
    return CommonBuild(
        build_slug=slug,
        subclasses=list(subclasses),
        sets=list(sets),
        count=6,
        report_count=5,
        best_player=player,
        all_players=[player],
        trial_name=trial,
        boss_name=boss,
        fight_id=7,
        report_code="ABC123",
    )


@pytest.fixture
def gen(tmp_path):
    return PageGenerator(template_dir=str(TEMPLATE_DIR), output_dir=str(tmp_path))


@pytest.fixture
def sample_builds():
    return [
        make_build("Rockgrove", "Oaxiltso", "dps", "DragonKnight", 120000, slug="a-b-c-s1-s2"),
        make_build("Aetherian Archive", "The Mage", "healer", "Templar", 9000, slug="d-e-f-s3-s4"),
        make_build("Kyne's Aegis", "Yandir the Butcher", "tank", "Warden", 55, slug="g-h-i-s5-s6"),
        make_build("Rockgrove", TRASH, "dps", "Arcanist", 80000, slug="j-k-l-s7-s8"),
    ]


# 1. normalize_class_name

@pytest.mark.parametrize(
    "raw,expected",
    [
        ("DragonKnight", "Dragonknight"),
        ("arcanist", "Arcanist"),
        ("Templar", "Templar"),
        ("", "Unknown"),
        (None, "Unknown"),
        ("some thing", "Some Thing"),
    ],
)
def test_normalize_class_name(raw, expected):
    assert normalize_class_name(raw) == expected


# 2. get_display_parts

def test_display_parts_marks_base_class_for_api_casing():
    build = CommonBuild(
        subclasses=["Ardent", "Draconic", "Herald"],
        best_player=PlayerBuild(class_name="DragonKnight"),
    )
    parts = {name: is_base for name, is_base, _padded in build.get_display_parts(abbreviated=True)}
    assert parts == {"Ardent": True, "Draconic": True, "Herald": False}


def test_display_parts_not_all_false_for_api_casing():
    build = CommonBuild(
        subclasses=["Ardent", "Draconic", "Herald"],
        best_player=PlayerBuild(class_name="DragonKnight"),
    )
    assert any(is_base for _, is_base, _padded in build.get_display_parts(abbreviated=True))


# 3. build_page_filename

EXPECTED_KA_FILENAME = (
    "kynes-aegis-lord-falgravn-and-co---test-ass-herald-x-deadly-strike-unknown.html"
)


def test_build_page_filename_matches_legacy_expression():
    build = make_build(
        "Kyne's Aegis", "Lord Falgravn & Co / Test", slug="ass-herald-x-deadly-strike-unknown"
    )
    legacy_trial = build.trial_name.lower().replace(" ", "-").replace("'", "")
    legacy_boss = (
        build.boss_name.lower().replace(" ", "-").replace("'", "")
        .replace("&", "and").replace("/", "-")
    )
    legacy = f"{legacy_trial}-{legacy_boss}-{build.build_slug}.html"
    assert legacy == EXPECTED_KA_FILENAME
    assert PageGenerator.build_page_filename(build) == EXPECTED_KA_FILENAME


def test_generate_build_page_writes_file_named_by_build_page_filename(gen, tmp_path):
    build = make_build(
        "Kyne's Aegis", "Lord Falgravn & Co / Test", slug="ass-herald-x-deadly-strike-unknown"
    )
    path = gen.generate_build_page(build, "U50")
    assert Path(path).name == EXPECTED_KA_FILENAME
    assert (tmp_path / EXPECTED_KA_FILENAME).exists()


# 4. _build_finder_rows

def test_rows_skip_builds_without_best_player(gen):
    build = make_build("Rockgrove", "Oaxiltso")
    build.best_player = None
    assert gen._build_finder_rows([build]) == []


def test_rows_skip_aggregated_builds(gen):
    build = make_build("Rockgrove", "Oaxiltso")
    build.is_aggregated = True
    assert gen._build_finder_rows([build]) == []


def test_rows_esologs_url_uses_player_url_when_set(gen):
    build = make_build("Rockgrove", "Oaxiltso", player_url="https://www.esologs.com/character/1")
    assert gen._build_finder_rows([build])[0]["esologs_url"] == "https://www.esologs.com/character/1"


def test_rows_esologs_url_falls_back_to_report_link(gen):
    build = make_build("Rockgrove", "Oaxiltso", player_url="")
    assert (
        gen._build_finder_rows([build])[0]["esologs_url"]
        == "https://www.esologs.com/reports/ABC123?fight=7"
    )


def test_rows_class_name_is_normalized(gen):
    row = gen._build_finder_rows([make_build("Rockgrove", "Oaxiltso", class_name="DragonKnight")])[0]
    assert row["class_name"] == "Dragonknight"


def test_rows_class_slug_is_lowercase_normalized(gen):
    row = gen._build_finder_rows([make_build("Rockgrove", "Oaxiltso", class_name="DragonKnight")])[0]
    assert row["class_slug"] == "dragonknight"


def test_rows_role_is_lowercased(gen):
    build = make_build("Rockgrove", "Oaxiltso", role="dps")
    build.best_player.role = "DPS"
    assert gen._build_finder_rows([build])[0]["role"] == "dps"


def test_rows_trial_slug_keeps_apostrophes(gen):
    row = gen._build_finder_rows([make_build("Kyne's Aegis", "Yandir the Butcher")])[0]
    assert row["trial_slug"] == "kyne's-aegis"


def test_rows_build_url_strips_apostrophes(gen):
    row = gen._build_finder_rows([make_build("Kyne's Aegis", "Yandir the Butcher")])[0]
    assert "'" not in row["build_url"]
    assert row["build_url"].startswith("kynes-aegis-")


def test_rows_is_trash_true_for_trash_builds_boss(gen):
    row = gen._build_finder_rows([make_build("Rockgrove", TRASH)])[0]
    assert row["is_trash"] is True


def test_rows_is_trash_false_for_regular_boss(gen):
    row = gen._build_finder_rows([make_build("Rockgrove", "Oaxiltso")])[0]
    assert row["is_trash"] is False


def test_rows_sorted_by_trial_boss_role_then_metric(gen):
    trials = {
        t["name"]: t["id"]
        for t in json.loads((PROJECT_ROOT / "data/trials.json").read_text())["trials"]
    }
    bosses = json.loads((PROJECT_ROOT / "data/trial_bosses.json").read_text())["trial_bosses"]
    assert trials["Rockgrove"] > trials["Aetherian Archive"]
    rg1, rg2 = bosses["Rockgrove"][:2]
    aa1, aa_last = bosses["Aetherian Archive"][0], bosses["Aetherian Archive"][-1]

    expected = [
        ("Rockgrove", rg1, "dps", 200000),
        ("Rockgrove", rg1, "dps", 100000),
        ("Rockgrove", rg1, "healer", 9000),
        ("Rockgrove", rg1, "tank", 60),
        ("Rockgrove", rg2, "dps", 150000),
        ("Rockgrove", TRASH, "dps", 90000),
        ("Aetherian Archive", aa1, "dps", 110000),
        ("Aetherian Archive", aa_last, "tank", 50),
        ("Aetherian Archive", TRASH, "healer", 8000),
    ]
    builds = [
        make_build(t, b, r, metric=m, slug=f"s{i}-a-b-c-d")
        for i, (t, b, r, m) in enumerate(expected)
    ]
    scrambled = builds[::-1][1:] + builds[::-1][:1]
    rows = gen._build_finder_rows(scrambled)
    got = [(r["trial_name"], r["boss_name"], r["role"], r["metric"]) for r in rows]
    assert got == expected


# 5. generate_build_finder_page

@pytest.fixture
def finder_soup(gen, tmp_path, sample_builds):
    path = gen.generate_build_finder_page(sample_builds)
    assert Path(path) == tmp_path / "build-finder.html"
    return BeautifulSoup(
        (tmp_path / "build-finder.html").read_text(encoding="utf-8"), "html.parser"
    )


def _data_rows(soup):
    return [
        tr for tr in soup.select("#finder-table tbody tr") if tr.get("id") != "finder-empty"
    ]


def test_finder_page_file_is_written(finder_soup, tmp_path):
    assert (tmp_path / "build-finder.html").exists()


def test_finder_class_select_has_expected_options(finder_soup):
    values = {o.get("value") for o in finder_soup.select("select#finder-class option")}
    assert values == {
        "", "arcanist", "dragonknight", "necromancer", "nightblade",
        "sorcerer", "templar", "warden",
    }


def test_finder_role_select_has_expected_options(finder_soup):
    values = {o.get("value") for o in finder_soup.select("select#finder-role option")}
    assert values == {"", "dps", "healer", "tank"}


def test_finder_has_reset_and_table(finder_soup):
    assert finder_soup.select_one("#finder-reset") is not None
    assert finder_soup.select_one("#finder-table") is not None


def test_finder_count_text_shows_total(finder_soup, sample_builds):
    n = len(sample_builds)
    text = finder_soup.select_one("#finder-count").get_text(" ", strip=True)
    assert f"Showing {n} of {n} builds" in text


def test_finder_data_row_count_matches_builds(finder_soup, sample_builds):
    assert len(_data_rows(finder_soup)) == len(sample_builds)


def test_finder_rows_have_filter_data_attributes(finder_soup):
    for tr in _data_rows(finder_soup):
        for attr in ("data-class", "data-role", "data-trash"):
            assert tr.has_attr(attr), attr


def test_finder_cells_have_data_label(finder_soup):
    for tr in _data_rows(finder_soup):
        tds = tr.find_all("td")
        assert tds
        assert all(td.get("data-label") for td in tds)


def test_finder_rows_have_one_build_link_matching_filename(finder_soup, sample_builds):
    expected = sorted(PageGenerator.build_page_filename(b) for b in sample_builds)
    hrefs = []
    for tr in _data_rows(finder_soup):
        links = tr.select("a.finder-build-link")
        assert len(links) == 1
        hrefs.append(links[0]["href"])
    assert sorted(hrefs) == expected


def test_finder_rows_have_one_external_esologs_link(finder_soup):
    rows_with_url = [
        tr for tr in _data_rows(finder_soup) if not tr.select(".finder-esologs-missing")
    ]
    assert rows_with_url
    for tr in rows_with_url:
        links = tr.select("a.finder-esologs-link")
        assert len(links) == 1
        assert links[0].get("target") == "_blank"
        assert "noopener" in links[0].get("rel", [])


def test_finder_empty_row_exists_and_is_hidden(finder_soup):
    empty = finder_soup.select_one("tr#finder-empty")
    assert empty is not None
    assert empty.has_attr("hidden")


def test_finder_page_includes_filter_script(finder_soup):
    assert any(
        "finder-class" in (s.string or s.get_text()) for s in finder_soup.find_all("script")
    )


# 6. sitemap

def test_sitemap_includes_build_finder(gen, sample_builds):
    gen.generate_build_finder_page(sample_builds)
    grouped = gen._group_builds_by_trial(sample_builds)
    path = gen.generate_sitemap(sample_builds, grouped)
    assert "/build-finder.html</loc>" in Path(path).read_text(encoding="utf-8")


def test_sitemap_omits_build_finder_when_page_missing(gen, sample_builds, tmp_path):
    assert not (tmp_path / "build-finder.html").exists()
    grouped = gen._group_builds_by_trial(sample_builds)
    path = gen.generate_sitemap(sample_builds, grouped)
    assert "build-finder.html" not in Path(path).read_text(encoding="utf-8")


# 7. generate_all_pages wiring

def test_generate_all_pages_returns_existing_build_finder_file(gen):
    builds = [
        make_build("Rockgrove", "Oaxiltso", slug="a-b-c-s1-s2"),
        make_build("Aetherian Archive", "The Mage", "healer", "Templar", 9000, slug="d-e-f-s3-s4"),
    ]
    files = gen.generate_all_pages(builds, "U50")
    assert "build_finder" in files
    assert Path(files["build_finder"]).exists()


def test_generate_all_pages_trial_links_and_entry_points_exist(gen, tmp_path):
    builds = [
        make_build("Kyne's Aegis", "Yandir the Butcher", slug="a-b-c-s1-s2"),
        make_build("Aetherian Archive", "The Mage", "healer", "Templar", 9000, slug="d-e-f-s3-s4"),
    ]
    gen.generate_all_pages(builds, "U50")
    rows = gen._build_finder_rows(builds)
    assert len(rows) == 2
    for row in rows:
        assert (tmp_path / f"{row['trial_slug']}.html").exists(), row["trial_slug"]

    home = BeautifulSoup((tmp_path / "index.html").read_text(encoding="utf-8"), "html.parser")
    assert home.find("a", href="build-finder.html") is not None
    nav = home.select_one(".header-nav")
    assert nav is not None
    assert "Build Finder" in nav.get_text()


def test_generate_all_pages_survives_finder_failure(gen, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("finder broke")

    monkeypatch.setattr(gen, "generate_build_finder_page", boom)
    files = gen.generate_all_pages([make_build("Rockgrove", "Oaxiltso", slug="a-b-c-s1-s2")], "U50")
    assert "build_finder" not in files
    assert "home" in files and "sitemap" in files


# 8. review fixes

def test_rows_sort_does_not_interleave_unknown_trials(gen):
    builds = [
        make_build("Zeta Fake Trial", "Boss A", slug="z1-a-b-c-d", metric=100),
        make_build("Alpha Fake Trial", "Boss A", slug="a1-a-b-c-d", metric=500),
        make_build("Zeta Fake Trial", "Boss B", slug="z2-a-b-c-d", metric=900),
        make_build("Alpha Fake Trial", "Boss B", slug="a2-a-b-c-d", metric=50),
    ]
    trials = [r["trial_name"] for r in gen._build_finder_rows(builds)]
    assert trials == ["Alpha Fake Trial"] * 2 + ["Zeta Fake Trial"] * 2


def test_rows_skip_unknown_role(gen):
    build = make_build("Rockgrove", "Oaxiltso")
    build.best_player.role = ""
    assert gen._build_finder_rows([build]) == []


def test_rows_skip_unknown_class(gen):
    build = make_build("Rockgrove", "Oaxiltso", class_name="Bard")
    assert gen._build_finder_rows([build]) == []


def test_rows_esologs_fallback_prefers_player_report(gen):
    build = make_build("Rockgrove", "Oaxiltso", player_url="")
    build.report_code = "BUILD999"
    build.fight_id = 99
    assert (
        gen._build_finder_rows([build])[0]["esologs_url"]
        == "https://www.esologs.com/reports/ABC123?fight=7"
    )


def _finder_soup_for(gen, tmp_path, builds):
    gen.generate_build_finder_page(builds)
    return BeautifulSoup(
        (tmp_path / "build-finder.html").read_text(encoding="utf-8"), "html.parser"
    )


def test_finder_renders_bold_base_class_for_dragonknight(gen, tmp_path):
    build = make_build(
        "Rockgrove", "Oaxiltso", class_name="DragonKnight",
        subclasses=("Ardent", "Draconic", "Herald"),
    )
    soup = _finder_soup_for(gen, tmp_path, [build])
    bold = {span.get_text() for span in soup.select("#finder-table span.finder-base")}
    assert bold == {"Ardent", "Draconic"}


def test_finder_escapes_apostrophes_in_attributes(gen, tmp_path):
    build = make_build("Kyne's Aegis", "Yandir the Butcher", player_name="@O'Brien")
    soup = _finder_soup_for(gen, tmp_path, [build])
    tr = _data_rows(soup)[0]
    assert tr.select_one("a.finder-esologs-link")["aria-label"] == "Open @O'Brien's log on ESO Logs"
    parts = " / ".join(name for name, _base, _padded in build.get_display_parts(abbreviated=True))
    assert (
        tr.select_one("a.finder-build-link")["aria-label"]
        == f"View Build: {parts}, Deadly Strike + Perfected Ansuul's Torment"
        " (Kyne's Aegis, Yandir the Butcher)"
    )
    set_links = tr.select('td[data-label="Signature Sets"] a')
    assert "Perfected Ansuul's Torment" in [a.get_text() for a in set_links]


def test_finder_view_build_labels_unique_when_only_sets_differ(gen, tmp_path):
    builds = [
        make_build("Rockgrove", "Oaxiltso", slug="a-b-c-s1-s2", sets=("Set One", "Set Two")),
        make_build("Rockgrove", "Oaxiltso", slug="a-b-c-s3-s4", sets=("Set Three", "Set Four")),
    ]
    soup = _finder_soup_for(gen, tmp_path, builds)
    labels = [a["aria-label"] for a in soup.select("a.finder-build-link")]
    assert len(set(labels)) == 2
    assert all(label.startswith("View Build") for label in labels)


def test_finder_frequency_pluralisation(gen, tmp_path):
    build = make_build("Rockgrove", "Oaxiltso")
    build.count = 1
    build.report_count = 1
    soup = _finder_soup_for(gen, tmp_path, [build])
    cell = _data_rows(soup)[0].find("td", attrs={"data-label": "Frequency"})
    assert cell.get_text(" ", strip=True).startswith("1 player / 1 report ")


def test_finder_filters_hidden_without_js_and_noscript_present(finder_soup):
    assert finder_soup.select_one(".finder-filters").has_attr("hidden")
    assert "Filtering needs JavaScript" in finder_soup.find("noscript").get_text()
    css = "\n".join(style.get_text() for style in finder_soup.find_all("style"))
    assert re.search(r"\.finder-filters\[hidden\]\s*\{[^}]*display:\s*none", css)


def test_finder_og_image_is_not_missing_topbuilds_preview(finder_soup):
    og = finder_soup.find("meta", attrs={"property": "og:image"})
    assert og is not None and og.get("content")
    assert "topbuilds" not in og["content"]


def test_rows_metric_none_becomes_zero(gen):
    build = make_build("Rockgrove", "Oaxiltso")
    build.best_player.dps = None
    assert gen._build_finder_rows([build])[0]["metric"] == 0.0


def test_finder_row_without_any_log_renders_no_log(gen, tmp_path):
    build = make_build("Rockgrove", "Oaxiltso", player_url="")
    build.best_player.report_code = None
    build.best_player.fight_id = None
    build.report_code = None
    build.fight_id = None
    assert gen._build_finder_rows([build])[0]["esologs_url"] == ""
    tr = _data_rows(_finder_soup_for(gen, tmp_path, [build]))[0]
    assert tr.select("a.finder-esologs-link") == []
    assert tr.select_one(".finder-esologs-missing").get_text() == "No log"


def test_deployment_check_4_passes_then_fails_on_corruption(gen, tmp_path):
    builds = [
        make_build("Kyne's Aegis", "Yandir the Butcher", slug="a-b-c-s1-s2"),
        make_build("Aetherian Archive", "The Mage", "healer", "Templar", 9000, slug="d-e-f-s3-s4"),
    ]
    gen.generate_all_pages(builds, "U50")

    checker = DeploymentChecker(str(tmp_path))
    assert checker.check_4_build_finder() is True
    assert checker.checks_failed == 0
    assert checker.warnings == []

    finder = tmp_path / "build-finder.html"
    html = finder.read_text(encoding="utf-8")
    assert 'data-class="nightblade"' in html
    finder.write_text(
        html.replace('data-class="nightblade"', 'data-class="bogus"', 1), encoding="utf-8"
    )
    checker = DeploymentChecker(str(tmp_path))
    checker.check_4_build_finder()
    assert checker.checks_failed > 0
