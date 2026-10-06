#!/usr/bin/env python3
"""
Import an ESO Log Tail game-asset bundle into the site.

Usage:
    python scripts/import_game_assets.py <release-tag|bundle.zip|bundle-dir>
        [--repo brainsnorkel/eso-live-encounterlog-sets-abilities] [--update uXX] [--dry-run]

Runs the contract checks from check_asset_bundle.py first and refuses to import on failure. Then:
- copies icons into static/icons add-or-update only: new stems, and stems whose RGBA pixels differ.
  Pixel-identical files are skipped even if their bytes differ; nothing is ever deleted.
- writes data/game/<update>/{abilities,skill_lines,mundus,sets,manifest}.json, where <update> is
  --update or manifest["update"].
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_asset_bundle import (  # noqa: E402
    PROJECT_ROOT, contract_ok, diff_icons, load_bundle, open_bundle, print_report, run_checks,
)

DEFAULT_REPO = "brainsnorkel/eso-live-encounterlog-sets-abilities"
TABLE_FILES = ("abilities.json", "skill_lines.json", "mundus.json", "sets.json", "manifest.json")


def download_release(tag: str, repo: str, dest: Path) -> Path:
    """Download a release's assets with gh and return the bundle zip."""
    subprocess.run(["gh", "release", "download", tag, "--repo", repo, "--dir", str(dest)], check=True)
    zips = sorted(dest.glob("*.zip"))
    if len(zips) != 1:
        raise SystemExit(f"expected one .zip in release {tag}, found {[z.name for z in zips]}")
    return zips[0]


def apply_import(bundle_dir: Path, icons_dir: Path, data_root: Path, update: str, dry_run: bool = False) -> dict:
    """Copy new/changed icons and write the tables. Returns what changed (or would change)."""
    diff = diff_icons(bundle_dir / "icons", icons_dir)
    if not dry_run:
        icons_dir.mkdir(parents=True, exist_ok=True)
        for stem in diff["new"] + diff["changed"]:
            shutil.copyfile(bundle_dir / "icons" / f"{stem}.png", icons_dir / f"{stem}.png")
    out_dir = data_root / update
    tables = []
    for name in TABLE_FILES:
        src, dst = bundle_dir / name, out_dir / name
        if not src.is_file():
            continue
        status = "unchanged" if dst.is_file() and dst.read_bytes() == src.read_bytes() else \
            ("updated" if dst.is_file() else "new")
        tables.append((name, status))
        if not dry_run and status != "unchanged":
            out_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)
    return {"icons": diff, "tables": tables, "out_dir": out_dir}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Check and import an ESO Log Tail game-asset bundle.")
    ap.add_argument("source", help="release tag, bundle .zip, or unzipped bundle directory")
    ap.add_argument("--repo", default=DEFAULT_REPO, help=f"GitHub repo for release tags (default {DEFAULT_REPO})")
    ap.add_argument("--update", help="target update, e.g. u51 (default: manifest['update'])")
    ap.add_argument("--dry-run", action="store_true", help="show what would change without writing")
    ap.add_argument("--icons-dir", default=str(PROJECT_ROOT / "static" / "icons"), help=argparse.SUPPRESS)
    ap.add_argument("--data-root", default=str(PROJECT_ROOT / "data" / "game"), help=argparse.SUPPRESS)
    ap.add_argument("--fixtures", default=str(PROJECT_ROOT / "docs" / "handoff"), help=argparse.SUPPRESS)
    args = ap.parse_args(argv)

    icons_dir, data_root = Path(args.icons_dir), Path(args.data_root)
    download_tmp: Optional[tempfile.TemporaryDirectory] = None
    source = Path(args.source)
    if not source.exists():
        download_tmp = tempfile.TemporaryDirectory(prefix="esobundle-dl-")
        source = download_release(args.source, args.repo, Path(download_tmp.name))

    bundle_dir, extract_tmp = open_bundle(source)
    try:
        results = run_checks(bundle_dir, icons_dir=icons_dir, fixtures_dir=Path(args.fixtures))
        if not contract_ok(results):
            print_report(results, args.source)
            print("\nRefusing to import: the bundle fails the contract checks above.")
            return 1
        print("Contract checks: PASS (" + "; ".join(f"{r['id']} {r['summary']}" for r in results
                                                    if r["id"] in ("T1", "T5")) + ")")

        update = args.update or load_bundle(bundle_dir)["manifest"].get("update")
        if not update or not re.fullmatch(r"u\d+", update):
            print(f"Invalid or missing update id {update!r}; pass --update uXX")
            return 1

        res = apply_import(bundle_dir, icons_dir, data_root, update, args.dry_run)
    finally:
        if extract_tmp:
            extract_tmp.cleanup()
        if download_tmp:
            download_tmp.cleanup()

    verb = "Would" if args.dry_run else "Did"
    d = res["icons"]
    print(f"\n{verb} copy icons into {icons_dir}: {len(d['new'])} new, {len(d['changed'])} updated "
          f"(pixels differ), {len(d['unchanged'])} unchanged; {len(d['site_only'])} site-only kept")
    for k, label in (("new", "new"), ("changed", "updated")):
        if d[k]:
            print(f"  {label}: {', '.join(d[k][:30])}{' ...' if len(d[k]) > 30 else ''}")
    print(f"{verb} write tables to {res['out_dir']}: "
          + ", ".join(f"{name} ({status})" for name, status in res["tables"]))
    rel = res["out_dir"]
    try:
        rel = rel.relative_to(PROJECT_ROOT)
    except ValueError:
        pass
    print(f"\nReminder: *.json is gitignored; stage the tables with: git add -f {rel}/*.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
