"""Tests for scripts/check_asset_bundle.py and scripts/import_game_assets.py on a synthetic bundle."""

import hashlib
import json
import sys
from pathlib import Path

import pytest
from PIL import Image, PngImagePlugin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import check_asset_bundle as cab  # noqa: E402
import import_game_assets as iga  # noqa: E402


def _png(path: Path, color, size=64, text=None):
    info = None
    if text:
        info = PngImagePlugin.PngInfo()
        info.add_text("note", text)
    Image.new("RGBA", (size, size), color).save(path, pnginfo=info)


def _write_manifest(bundle: Path):
    files = {p.relative_to(bundle).as_posix(): hashlib.sha1(p.read_bytes()).hexdigest()
             for p in sorted(bundle.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    tables = {t: json.loads((bundle / f"{t}.json").read_text())[t] for t in cab.TABLES}
    manifest = {"update": "u99", "bundle_format": 1, "files": files,
                "counts": {"icons": len(list((bundle / "icons").glob("*.png"))),
                           **{t: len(v) for t, v in tables.items()}}}
    (bundle / "manifest.json").write_text(json.dumps(manifest))


@pytest.fixture
def bundle(tmp_path) -> Path:
    b = tmp_path / "bundle"
    (b / "icons").mkdir(parents=True)
    _png(b / "icons" / "ability_bow_001.png", (255, 0, 0, 255))
    _png(b / "icons" / "ability_bow_002.png", (0, 0, 255, 255))
    _png(b / "icons" / "ability_grimoire_bow.png", (0, 255, 0, 255))
    tables = {
        "abilities": {"100": {"name": "Snipe", "icon": "ability_bow_001", "skill_line": "Bow", "type": "active"}},
        "skill_lines": {"Bow": {"category": "weapon", "class": None, "ability_ids": [100],
                                "grimoire_icon_stems": ["ability_grimoire_bow"]}},
        "mundus": {"13940": {"name": "The Warrior", "icon": "ability_mundusstones_001"}},
        "sets": {"7": {"name": "Hawk's Eye", "max_equip": 5}},
    }
    for name, table in tables.items():
        (b / f"{name}.json").write_text(json.dumps({name: table, "update": "u99"}))
    _write_manifest(b)
    return b


def test_manifest_verifies_and_catches_tampered_file(bundle):
    assert cab.check_manifest(cab.load_bundle(bundle))["ok"] is True
    (bundle / "sets.json").write_text(json.dumps({"sets": {"7": {"name": "Tampered"}}}))
    res = cab.check_manifest(cab.load_bundle(bundle))
    assert res["ok"] is False
    assert res["details"]["hash_mismatch"] == ["sets.json"]


def test_manifest_reports_unlisted_file(bundle):
    (bundle / "stray.txt").write_text("x")
    res = cab.check_manifest(cab.load_bundle(bundle))
    assert res["ok"] is False
    assert res["details"]["unlisted"] == ["stray.txt"]


def test_icon_check_catches_32px_icon(bundle):
    assert cab.check_icons(cab.load_bundle(bundle))["ok"] is True
    _png(bundle / "icons" / "ability_bow_002.png", (0, 0, 255, 255), size=32)
    res = cab.check_icons(cab.load_bundle(bundle))
    assert res["ok"] is False
    assert res["details"]["bad"] == [{"stem": "ability_bow_002", "problems": ["size 32x32"]}]


def test_fixture_resolution_by_id_and_grimoire_icon(bundle, tmp_path):
    b = cab.load_bundle(bundle)
    assert cab.resolve(b, 100, "whatever") == ("Bow", "id")
    assert cab.resolve(b, 1015, "ability_grimoire_bow") == ("Bow", "icon")
    assert cab.resolve(b, 1015, "ability_unknown") == (None, None)

    fx = tmp_path / "fixtures"
    fx.mkdir()
    (fx / cab.FIXTURE_ICONS).write_text("ability_bow_001\nability_grimoire_bow\n")
    rows = [{"ability_id": 100, "name": "Snipe", "icon": "ability_bow_001"},
            {"ability_id": 1015, "name": "Vault", "icon": "ability_grimoire_bow"},
            {"ability_id": 999999, "name": "Ghost", "icon": "ability_nope"}]
    (fx / cab.FIXTURE_ABILITIES).write_text(json.dumps({"abilities": rows}))
    res = cab.check_fixtures(b, fx)
    assert res["details"]["missing_icons"] == []
    assert [r["ability_id"] for r in res["details"]["unresolved"]] == [999999]
    assert res["ok"] is False


def _site_icons(bundle: Path, site: Path):
    """Site dir with: one pixel-identical re-encode, one pixel-different, one site-only; one bundle icon missing."""
    site.mkdir(parents=True)
    _png(site / "ability_bow_001.png", (255, 0, 0, 255), text="re-encoded")  # same pixels, other bytes
    _png(site / "ability_bow_002.png", (0, 0, 200, 255))  # pixels differ
    _png(site / "gp_class_warden.png", (1, 2, 3, 255))  # site-authored
    assert (site / "ability_bow_001.png").read_bytes() != (bundle / "icons" / "ability_bow_001.png").read_bytes()


def test_icon_diff_classifies_new_changed_and_reencoded(bundle, tmp_path):
    site = tmp_path / "site_icons"
    _site_icons(bundle, site)
    d = cab.diff_icons(bundle / "icons", site)
    assert d == {"new": ["ability_grimoire_bow"], "changed": ["ability_bow_002"],
                 "unchanged": ["ability_bow_001"], "site_only": ["gp_class_warden"]}


def test_importer_copies_only_new_or_changed_and_never_deletes(bundle, tmp_path):
    site = tmp_path / "site_icons"
    _site_icons(bundle, site)
    reencoded_before = (site / "ability_bow_001.png").read_bytes()
    res = iga.apply_import(bundle, site, tmp_path / "data_game", "u99")
    assert res["icons"]["new"] == ["ability_grimoire_bow"]
    assert (site / "ability_grimoire_bow.png").read_bytes() == (bundle / "icons" / "ability_grimoire_bow.png").read_bytes()
    assert (site / "ability_bow_002.png").read_bytes() == (bundle / "icons" / "ability_bow_002.png").read_bytes()
    assert (site / "ability_bow_001.png").read_bytes() == reencoded_before  # no churn
    assert (site / "gp_class_warden.png").is_file()  # site-only file survives


def test_importer_dry_run_writes_nothing(bundle, tmp_path):
    site = tmp_path / "site_icons"
    _site_icons(bundle, site)
    before = {p.name: p.read_bytes() for p in site.iterdir()}
    iga.apply_import(bundle, site, tmp_path / "data_game", "u99", dry_run=True)
    assert {p.name: p.read_bytes() for p in site.iterdir()} == before
    assert not (tmp_path / "data_game").exists()


def test_importer_writes_update_tables(bundle, tmp_path):
    data_root = tmp_path / "data_game"
    res = iga.apply_import(bundle, tmp_path / "site_icons", data_root, "u99")
    written = sorted(p.name for p in (data_root / "u99").iterdir())
    assert written == sorted(iga.TABLE_FILES)
    assert (data_root / "u99" / "sets.json").read_bytes() == (bundle / "sets.json").read_bytes()
    assert all(status == "new" for _, status in res["tables"])
    again = iga.apply_import(bundle, tmp_path / "site_icons", data_root, "u99")
    assert all(status == "unchanged" for _, status in again["tables"])


def test_importer_refuses_bundle_failing_contract(bundle, tmp_path):
    # The synthetic bundle lacks the 21 class lines (T3), so the importer must refuse and write nothing.
    site, data_root = tmp_path / "site_icons", tmp_path / "data_game"
    rc = iga.main([str(bundle), "--icons-dir", str(site), "--data-root", str(data_root),
                   "--fixtures", str(tmp_path / "no_fixtures")])
    assert rc == 1
    assert not site.exists() and not data_root.exists()
