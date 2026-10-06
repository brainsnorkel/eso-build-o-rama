#!/usr/bin/env python3
"""
Check an ESO Log Tail game-asset bundle against the contract in
docs/handoff/uesp-game-asset-export-request.md (checks T1-T7 in docs/GAME_ASSET_BUNDLE.md).

Usage:
    python scripts/check_asset_bundle.py <bundle.zip|bundle-dir> [--builds <path-or-https-url>]
        [--icons-dir static/icons] [--fixtures docs/handoff] [--json]

Exit code 1 if any contract check (T1-T6) fails. T7 (icon diff) is informational.
Set-name and fixture-name differences are warnings, not failures.
"""

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TABLES = ("abilities", "skill_lines", "mundus", "sets")

# The 21 slottable class skill lines (Appendix A of the brief). models.CLASS_SKILL_LINES only
# carries abbreviations, so the full names live here.
CLASS_LINES: Dict[str, str] = {
    "Ardent Flame": "Dragonknight", "Draconic Power": "Dragonknight", "Earthen Heart": "Dragonknight",
    "Dark Magic": "Sorcerer", "Daedric Summoning": "Sorcerer", "Storm Calling": "Sorcerer",
    "Assassination": "Nightblade", "Shadow": "Nightblade", "Siphoning": "Nightblade",
    "Aedric Spear": "Templar", "Dawn's Wrath": "Templar", "Restoring Light": "Templar",
    "Animal Companions": "Warden", "Green Balance": "Warden", "Winter's Embrace": "Warden",
    "Grave Lord": "Necromancer", "Bone Tyrant": "Necromancer", "Living Death": "Necromancer",
    "Herald of the Tome": "Arcanist", "Curative Runeforms": "Arcanist", "Soldier of Apocrypha": "Arcanist",
}

CLASS_ICON_PREFIXES = (
    "ability_dragonknight", "ability_sorcerer", "ability_nightblade", "ability_templar",
    "ability_warden", "ability_necromancer", "ability_arcanist",
)

# Abilities whose names collide with class-line substrings; they must resolve to non-class lines.
NON_CLASS_PROBES = {38745: "Carve", 85187: "Rend", 42176: "Bone Surge"}

FIXTURE_ICONS = "referenced-icons-u49-u50.txt"
FIXTURE_ABILITIES = "referenced-abilities-u49-u50.json"
FIXTURE_EXTRA_STEMS = "extra-icon-stems.txt"

# Copy of ESOLogsAPIClient.MUNDUS_ABILITY_IDS, used only when importing api_client fails
# (it pulls in the esologs SDK and dotenv).
_MUNDUS_FALLBACK = {
    13940: "The Warrior", 13943: "The Mage", 13974: "The Serpent", 13975: "The Thief",
    13976: "The Lady", 13977: "The Steed", 13978: "The Lord", 13979: "The Apprentice",
    13980: "The Ritual", 13981: "The Lover", 13982: "The Atronach", 13984: "The Shadow",
    13985: "The Tower",
}


def site_mundus() -> Tuple[Dict[int, str], str]:
    """Return the site's mundus id -> name table and where it came from."""
    try:
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
        from src.eso_build_o_rama.api_client import ESOLogsAPIClient
        return dict(ESOLogsAPIClient.MUNDUS_ABILITY_IDS), "api_client.py"
    except Exception:
        return dict(_MUNDUS_FALLBACK), "hardcoded copy, api_client import failed"


# ---------------------------------------------------------------- loading

def open_bundle(path: Path) -> Tuple[Path, Optional[tempfile.TemporaryDirectory]]:
    """Return the directory holding manifest.json. A zip is extracted to a temp dir that the
    caller must keep alive (second return value) while using the bundle."""
    tmp = None
    root = path
    if path.is_file() and zipfile.is_zipfile(path):
        tmp = tempfile.TemporaryDirectory(prefix="esobundle-")
        with zipfile.ZipFile(path) as zf:
            zf.extractall(tmp.name)
        root = Path(tmp.name)
    if not root.is_dir():
        raise FileNotFoundError(f"not a bundle zip or directory: {path}")
    if (root / "manifest.json").is_file():
        return root, tmp
    found = sorted(p for p in root.rglob("manifest.json") if "__MACOSX" not in p.parts)
    if not found:
        raise FileNotFoundError(f"no manifest.json under {path}")
    return found[0].parent, tmp


def load_bundle(bundle_dir: Path) -> dict:
    b = {"dir": bundle_dir}
    b["manifest"] = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    for name in TABLES:
        p = bundle_dir / f"{name}.json"
        b[name] = json.loads(p.read_text(encoding="utf-8"))[name] if p.is_file() else {}
    icons_dir = bundle_dir / "icons"
    b["icons"] = {p.stem for p in icons_dir.glob("*.png")} if icons_dir.is_dir() else set()
    b["grimoire"] = {s: line for line, v in b["skill_lines"].items()
                     for s in (v.get("grimoire_icon_stems") or [])}
    return b


def resolve(b: dict, ability_id, icon: str) -> Tuple[Optional[str], Optional[str]]:
    """Resolve a slotted ability to (skill_line, how): by id first, then by grimoire icon stem."""
    if ability_id is not None:
        e = b["abilities"].get(str(ability_id))
        if e:
            return e.get("skill_line"), "id"
    if icon and icon in b["grimoire"]:
        return b["grimoire"][icon], "icon"
    return None, None


def is_class_line(b: dict, line: Optional[str]) -> bool:
    return line in CLASS_LINES and (b["skill_lines"].get(line) or {}).get("category") == "class"


def rgba(path: Path) -> Tuple[Tuple[int, int], bytes]:
    with Image.open(path) as im:
        im = im.convert("RGBA")
        return im.size, im.tobytes()


def _result(tid: str, name: str, ok: Optional[bool], summary: str, warnings=None, **details) -> dict:
    return {"id": tid, "name": name, "ok": ok, "summary": summary, "warnings": warnings or [],
            "details": details}


# ---------------------------------------------------------------- checks

def check_manifest(b: dict) -> dict:
    man, d = b["manifest"], b["dir"]
    actual = {"icons": len(b["icons"]), **{t: len(b[t]) for t in TABLES}}
    counts = man.get("counts") or {}
    count_diff = {k: {"manifest": counts.get(k), "actual": v} for k, v in actual.items() if counts.get(k) != v}
    files = man.get("files") or {}
    mismatched, missing = [], []
    for rel, sha in sorted(files.items()):
        p = d / rel
        if not p.is_file():
            missing.append(rel)
        elif hashlib.sha1(p.read_bytes()).hexdigest() != sha:
            mismatched.append(rel)
    on_disk = {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()
               and not any(part.startswith(".") or part == "__MACOSX" for part in p.relative_to(d).parts)}
    unlisted = sorted(on_disk - set(files) - {"manifest.json"})
    ok = not (count_diff or mismatched or missing or unlisted)
    verified = len(files) - len(mismatched) - len(missing)
    summary = (f"{actual['icons']:,} icons, {actual['abilities']:,} abilities, {actual['skill_lines']} lines, "
               f"{actual['mundus']} mundus, {actual['sets']} sets; {verified:,}/{len(files):,} hashes OK"
               + (f", {len(unlisted)} unlisted" if unlisted else ""))
    return _result("T1", "manifest", ok, summary, counts=actual, count_mismatch=count_diff,
                   hash_mismatch=mismatched, listed_missing=missing, unlisted=unlisted)


def check_icons(b: dict) -> dict:
    bad = []
    for stem in sorted(b["icons"]):
        problems = []
        if stem != stem.lower():
            problems.append("stem not lowercase")
        try:
            with Image.open(b["dir"] / "icons" / f"{stem}.png") as im:
                if im.format != "PNG":
                    problems.append(f"format {im.format}")
                if im.size != (64, 64):
                    problems.append(f"size {im.size[0]}x{im.size[1]}")
                if im.mode != "RGBA":
                    problems.append(f"mode {im.mode}")
        except Exception as e:
            problems.append(f"unreadable: {e}")
        if problems:
            bad.append({"stem": stem, "problems": problems})
    n = len(b["icons"])
    return _result("T2", "icons 64x64 RGBA PNG", not bad and n > 0,
                   f"{n - len(bad):,}/{n:,} icons valid", bad=bad)


def check_skill_lines(b: dict) -> dict:
    lines = b["skill_lines"]
    missing, wrong = [], []
    for line, cls in CLASS_LINES.items():
        v = lines.get(line)
        if v is None:
            missing.append(line)
        elif v.get("category") != "class" or v.get("class") != cls:
            wrong.append({"line": line, "category": v.get("category"), "class": v.get("class"),
                          "expected_class": cls})
    other_class = sorted(k for k, v in lines.items() if v.get("category") == "class"
                         and k not in CLASS_LINES and not k.startswith("Class Mastery"))
    warnings = [f"unexpected class-category lines: {other_class}"] if other_class else []
    return _result("T3", "21 class skill lines", not (missing or wrong),
                   f"{21 - len(missing) - len(wrong)}/21 class lines correct",
                   warnings=warnings, missing=missing, wrong=wrong, other_class_lines=other_class)


def check_mundus(b: dict) -> dict:
    expected, source = site_mundus()
    got = {int(k): (v or {}).get("name") for k, v in b["mundus"].items()}
    missing = sorted(set(expected) - set(got))
    extra = sorted(set(got) - set(expected))
    name_diff = [{"id": i, "site": expected[i], "bundle": got[i]} for i in sorted(set(expected) & set(got))
                 if expected[i] != got[i]]
    good = len(set(expected) & set(got)) - len(name_diff)
    return _result("T4", "mundus", not (missing or extra or name_diff),
                   f"{good}/{len(expected)} mundus match ({source})",
                   missing=missing, extra=extra, name_diff=name_diff, source=source)


def check_fixtures(b: dict, fixtures_dir: Optional[Path]) -> dict:
    if not fixtures_dir or not (fixtures_dir / FIXTURE_ICONS).is_file() \
            or not (fixtures_dir / FIXTURE_ABILITIES).is_file():
        return _result("T5", "fixtures", None, f"skipped: fixtures not found in {fixtures_dir}")
    stems = {l.strip() for l in (fixtures_dir / FIXTURE_ICONS).read_text(encoding="utf-8").splitlines()
             if l.strip()}
    missing_icons = sorted(stems - b["icons"])
    rows = json.loads((fixtures_dir / FIXTURE_ABILITIES).read_text(encoding="utf-8"))["abilities"]
    unresolved, name_diff, class_fail = [], [], []
    class_rows = 0
    for r in rows:
        aid, icon = r.get("ability_id"), r.get("icon") or ""
        line, how = resolve(b, aid, icon)
        if how is None:
            unresolved.append({"ability_id": aid, "name": r.get("name"), "icon": icon})
        elif how == "id":
            bname = b["abilities"][str(aid)].get("name")
            if bname != r.get("name"):
                name_diff.append({"ability_id": aid, "fixture": r.get("name"), "bundle": bname})
        if icon.startswith(CLASS_ICON_PREFIXES):
            class_rows += 1
            if not is_class_line(b, line):
                class_fail.append({"ability_id": aid, "name": r.get("name"), "line": line})
    probes = {}
    for aid, name in NON_CLASS_PROBES.items():
        line, _ = resolve(b, aid, "")
        probes[name] = {"line": line, "ok": line is not None and not is_class_line(b, line)}
    ok = not (missing_icons or unresolved or class_fail) and all(p["ok"] for p in probes.values())
    extra_missing = []
    if (fixtures_dir / FIXTURE_EXTRA_STEMS).is_file():
        extra = {l.strip() for l in (fixtures_dir / FIXTURE_EXTRA_STEMS).read_text(encoding="utf-8").splitlines()
                 if l.strip()}
        extra_missing = sorted(extra - b["icons"])
    warnings = []
    if name_diff:
        warnings.append(f"{len(name_diff)} fixture rows resolve by id to a different name, e.g. {name_diff[:3]}")
    if extra_missing:
        warnings.append(f"{len(extra_missing)} {FIXTURE_EXTRA_STEMS} stems absent: {extra_missing[:10]}")
    summary = (f"icons {len(stems) - len(missing_icons)}/{len(stems)}; "
               f"abilities {len(rows) - len(unresolved)}/{len(rows)}; "
               f"class-icon rows {class_rows - len(class_fail)}/{class_rows}; "
               + ", ".join(f"{n}->{p['line']}" for n, p in probes.items()))
    return _result("T5", "fixtures", ok, summary, warnings=warnings, missing_icons=missing_icons,
                   unresolved=unresolved, class_fail=class_fail, probes=probes, name_diff=name_diff,
                   extra_stems_missing=extra_missing)


def load_builds(src: str) -> dict:
    if src.startswith(("https://", "http://")):
        with urllib.request.urlopen(src, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    return json.loads(Path(src).read_text(encoding="utf-8"))


def iter_builds(obj):
    """Yield every build (a dict with both best_player and build_slug) in a builds.json tree."""
    if isinstance(obj, dict):
        if "best_player" in obj and "build_slug" in obj:
            yield obj
            return
        for v in obj.values():
            yield from iter_builds(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_builds(v)


def build_players(build: dict) -> list:
    return [p for p in (build.get("all_players") or [build.get("best_player")]) if p]


def check_builds(b: dict, builds_src: str) -> dict:
    builds = list(iter_builds(load_builds(builds_src)))
    slots, by = 0, {"id": 0, "icon": 0}
    unresolved: Dict[tuple, int] = {}
    icons, best_icons, sets_seen = set(), set(), {}
    for build in builds:
        for bar in ("abilities_bar1", "abilities_bar2"):
            best_icons.update(ab.get("ability_icon") for ab in (build["best_player"] or {}).get(bar) or []
                              if ab.get("ability_icon"))
        for pl in build_players(build):
            for bar in ("abilities_bar1", "abilities_bar2"):
                for ab in pl.get(bar) or []:
                    icon = ab.get("ability_icon") or ""
                    if icon:
                        icons.add(icon)
                    if ab.get("ability_id") is None and not ab.get("ability_name"):
                        continue  # empty slot
                    slots += 1
                    _, how = resolve(b, ab.get("ability_id"), icon)
                    if how:
                        by[how] += 1
                    else:
                        key = (ab.get("ability_id"), ab.get("ability_name"), icon)
                        unresolved[key] = unresolved.get(key, 0) + 1
            for g in pl.get("gear") or []:
                sid = g.get("set_id")
                if sid not in (None, 0, "0", ""):
                    sets_seen.setdefault(int(sid), g.get("set_name") or "")
    missing_icons = sorted(icons - b["icons"])
    missing_sets = [{"set_id": i, "name": n} for i, n in sorted(sets_seen.items()) if str(i) not in b["sets"]]
    name_diff = [{"set_id": i, "builds": n, "bundle": b["sets"][str(i)].get("name")}
                 for i, n in sorted(sets_seen.items())
                 if str(i) in b["sets"] and b["sets"][str(i)].get("name") != n]
    warnings = [f"{len(name_diff)} set names differ, e.g. {name_diff[:5]}"] if name_diff else []
    summary = (f"{len(builds)} builds; {slots:,} slots, {sum(unresolved.values())} unresolved "
               f"({by['id']:,} by id, {by['icon']} by grimoire icon); "
               f"icons {len(icons) - len(missing_icons)}/{len(icons)} ({len(best_icons)} on best players); "
               f"sets {len(sets_seen) - len(missing_sets)}/{len(sets_seen)}")
    return _result("T6", "live builds.json", not (unresolved or missing_icons or missing_sets), summary,
                   warnings=warnings, builds=len(builds), slots=slots, resolved_by=by,
                   unresolved=[{"ability_id": k[0], "name": k[1], "icon": k[2], "slots": c}
                               for k, c in sorted(unresolved.items(), key=lambda kv: -kv[1])],
                   missing_icons=missing_icons, missing_sets=missing_sets, set_name_diff=name_diff)


def diff_icons(bundle_icons_dir: Path, site_icons_dir: Path) -> dict:
    """Classify bundle icons against a site icon dir: new, changed (RGBA pixels differ),
    unchanged (pixel-identical, even if the file bytes differ), and site-only stems."""
    bundle = {p.stem for p in bundle_icons_dir.glob("*.png")}
    site = {p.stem for p in site_icons_dir.glob("*.png")} if site_icons_dir.is_dir() else set()
    changed, unchanged = [], []
    for stem in sorted(bundle & site):
        a, s = bundle_icons_dir / f"{stem}.png", site_icons_dir / f"{stem}.png"
        if a.read_bytes() == s.read_bytes() or rgba(a) == rgba(s):
            unchanged.append(stem)
        else:
            changed.append(stem)
    return {"new": sorted(bundle - site), "changed": changed, "unchanged": unchanged,
            "site_only": sorted(site - bundle)}


def check_icon_diff(b: dict, icons_dir: Path) -> dict:
    d = diff_icons(b["dir"] / "icons", icons_dir)
    summary = (f"vs {icons_dir}: {len(d['new'])} new, {len(d['changed'])} pixel-different, "
               f"{len(d['unchanged'])} identical, {len(d['site_only'])} site-only")
    return _result("T7", "icon diff", None, summary, **d)


def run_checks(bundle_dir: Path, builds: Optional[str] = None, icons_dir: Optional[Path] = None,
               fixtures_dir: Optional[Path] = None) -> List[dict]:
    b = load_bundle(bundle_dir)
    results = [check_manifest(b), check_icons(b), check_skill_lines(b), check_mundus(b),
               check_fixtures(b, fixtures_dir)]
    if builds:
        results.append(check_builds(b, builds))
    if icons_dir:
        results.append(check_icon_diff(b, icons_dir))
    return results


def contract_ok(results: List[dict]) -> bool:
    return all(r["ok"] is not False for r in results)


def print_report(results: List[dict], bundle: str) -> None:
    print(f"Bundle: {bundle}")
    print(f"{'Check':<5} {'Name':<22} {'Status':<6} Summary")
    print("-" * 100)
    for r in results:
        st = {True: "PASS", False: "FAIL", None: "INFO"}[r["ok"]]
        if r["summary"].startswith("skipped"):
            st = "SKIP"
        print(f"{r['id']:<5} {r['name']:<22} {st:<6} {r['summary']}")
    quiet = {"counts", "probes", "resolved_by", "name_diff", "set_name_diff", "extra_stems_missing",
             "other_class_lines", "source"}
    for r in results:
        if r["ok"] is False:
            print(f"\n{r['id']} failures:")
            for k, v in r["details"].items():
                if k not in quiet and isinstance(v, (list, dict)) and v:
                    print(f"  {k}: {json.dumps(v)[:600]}")
            if r["id"] == "T5":
                print(f"  probes: {json.dumps(r['details']['probes'])}")
    t7 = next((r for r in results if r["id"] == "T7"), None)
    if t7:
        for k in ("new", "changed", "site_only"):
            v = t7["details"][k]
            if v:
                print(f"\nT7 {k} ({len(v)}): {', '.join(v[:20])}{' ...' if len(v) > 20 else ''}")
    warns = [(r["id"], w) for r in results for w in r["warnings"]]
    if warns:
        print("\nWarnings:")
        for tid, w in warns:
            print(f"  {tid}: {w}")
    print(f"\nContract: {'PASS' if contract_ok(results) else 'FAIL'}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check an ESO Log Tail game-asset bundle (T1-T7).")
    ap.add_argument("bundle", help="bundle .zip or unzipped directory")
    ap.add_argument("--builds", help="builds.json path or https URL (enables T6)")
    ap.add_argument("--icons-dir", default=str(PROJECT_ROOT / "static" / "icons"),
                    help="site icon directory for the T7 diff (default: static/icons)")
    ap.add_argument("--fixtures", default=str(PROJECT_ROOT / "docs" / "handoff"),
                    help="directory with the u49/u50 fixture files (default: docs/handoff)")
    ap.add_argument("--json", action="store_true", help="print a machine-readable result")
    args = ap.parse_args(argv)

    bundle_dir, tmp = open_bundle(Path(args.bundle))
    try:
        results = run_checks(bundle_dir, args.builds, Path(args.icons_dir), Path(args.fixtures))
    finally:
        if tmp:
            tmp.cleanup()
    ok = contract_ok(results)
    if args.json:
        print(json.dumps({"bundle": args.bundle, "ok": ok, "checks": results}, indent=1, default=str))
    else:
        print_report(results, args.bundle)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
