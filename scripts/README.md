# Deployment Check Script

## Overview

`deployment_check.py` is a pre-deployment validation script that checks the generated HTML pages for common issues before merging to `main`.

## Requirements

```bash
pip3 install beautifulsoup4 --user
```

## Usage

```bash
# Check output-dev (develop branch)
python3 scripts/deployment_check.py output-dev

# Check output (main branch)
python3 scripts/deployment_check.py output

# Or use default (output)
python3 scripts/deployment_check.py
```

## Checks Performed

### Check 0: Home Page Loads
- ✅ Verifies `index.html` exists
- ✅ Checks for `<title>` tag
- ✅ Confirms trial content is present

### Check 1: Home Page Trial Content
- ✅ Each trial has build information displayed
- ✅ "Highest DPS Build" shown for each trial

### Check 2: Trial Pages Content
- ✅ Each trial page has at least 1 boss section
- ✅ Each trial page has at least 1 build listed

### Check 3: Build Pages Content
- ✅ Best player name is displayed (not "Unknown")
- ✅ Mundus stone is set (not "Unknown" or empty)
- ⚠️  Ability icons are present (warning if missing; slots are `div.abilities-bar > div.ability`,
  icon paths are resolved relative to the page)

### Check 4: Build Finder Page
- ✅ Filters, rows and build links are valid

### Check 5: builds.json Ability Icons
- ✅ Every `ability_icon` of every player in `<output_dir>/builds.json` has
  `<output_dir>/static/icons/<stem>.png` (error lists stem and ability name)

## Exit Codes

- **0**: All checks passed ✅
- **1**: One or more checks failed ❌

## Example Output

```
======================================================================
ESO BUILD-O-RAMA DEPLOYMENT READINESS CHECK
======================================================================
Output Directory: /path/to/output-dev

============================================================
CHECK 0: Home Page Loads
============================================================
✅ Home page loads successfully with 5 trials

============================================================
CHECK 1: Home Page Trial Content
============================================================
✅ Ossein Cage: Has build information
✅ Rockgrove: Has build information
...

======================================================================
SUMMARY
======================================================================
✅ Checks Passed: 12
❌ Checks Failed: 0

🎉 All checks passed! Ready to deploy.
======================================================================
```

## Integration with Git Workflow

### Pre-Merge Checklist

Before merging to `main`:

1. Generate builds locally:
   ```bash
   python3 -m src.eso_build_o_rama.main --trial-id 1
   ```

2. Run deployment check:
   ```bash
   python3 scripts/deployment_check.py output-dev
   ```

3. If checks pass, merge to `main`:
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

### GitHub Actions Integration (Future)

This script could be integrated into CI/CD:

```yaml
- name: Run Deployment Checks
  run: python3 scripts/deployment_check.py output
  
- name: Deploy to GitHub Pages
  if: success()
  uses: actions/deploy-pages@v4
```

## Troubleshooting

### "No module named 'bs4'"
Install BeautifulSoup4:
```bash
pip3 install beautifulsoup4 --user
```

### "Output directory does not exist"
Generate pages first:
```bash
python3 -m src.eso_build_o_rama.main --trial-id 1
```

### False Positives

Some warnings/errors might be expected:
- **"No ability slots found"**: May occur if abilities aren't rendered in HTML
- **"No builds found" for trial pages**: May trigger on build pages misidentified as trial pages

## Customization

You can modify the script to add more checks:

1. Open `scripts/deployment_check.py`
2. Add new check methods following the pattern:
   ```python
   def check_N_description(self) -> bool:
       """Check N: Description."""
       print("\n" + "="*60)
       print("CHECK N: Description")
       print("="*60)
       
       # Your check logic here
       
       return self.checks_failed == 0
   ```
3. Add the check to `run_all_checks()` method

## Game Asset Bundle Scripts

Icons and lookup tables come from a bundle published by ESO Log Tail; see
`docs/GAME_ASSET_BUNDLE.md` for the contract and expected numbers.

### check_asset_bundle.py

Runs checks T1–T7 on a bundle zip or unzipped directory: manifest counts and SHA-1s (T1),
64×64 RGBA icons (T2), the 21 class skill lines (T3), mundus vs `api_client.py` (T4), the u49/u50
fixtures in `docs/handoff/` (T5), a live `builds.json` (T6, only with `--builds`), and an icon diff
against `static/icons` (T7, informational). Exits 1 on any contract failure; set-name and
fixture-name differences are warnings.

```bash
python3 scripts/check_asset_bundle.py /tmp/bundle/x --builds https://esobuild.com/u51/builds.json
python3 scripts/check_asset_bundle.py bundle.zip --json
```

### import_game_assets.py

Downloads a release tag with `gh` (or takes a zip/dir), runs the contract checks and refuses to
import on failure, then copies icons into `static/icons` add-or-update only (new stems and stems
whose pixels differ; pixel-identical re-encodes are skipped; nothing is deleted) and writes
`data/game/<update>/{abilities,skill_lines,mundus,sets,manifest}.json`. `*.json` is gitignored, so
stage the tables with `git add -f data/game/<update>/*.json`.

```bash
python3 scripts/import_game_assets.py esobuild-assets-u51-20261006 --dry-run
python3 scripts/import_game_assets.py /tmp/bundle/x --update u51
```

Tests: `python3 -m pytest tests/test_asset_tools.py -q`

## Support

For issues or enhancements, create a GitHub issue in the repository.
