# Game asset bundles: how to test one and how the site uses it

Since Update 51 the icons and lookup tables that used to be hand-maintained here come from a bundle built by the
sibling project [ESO Log Tail](https://github.com/brainsnorkel/eso-live-encounterlog-sets-abilities) on a Windows
machine with the ESO client and UESP's EsoExtractData. The bundle is built to the contract in
[docs/handoff/uesp-game-asset-export-request.md](handoff/uesp-game-asset-export-request.md) and published as a
GitHub release asset, one per update:

```bash
gh release download esobuild-assets-u51-20261006 --repo brainsnorkel/eso-live-encounterlog-sets-abilities --dir /tmp/bundle
unzip -q /tmp/bundle/esobuild-assets-u51-20261006.zip -d /tmp/bundle/x
```

Contents: `manifest.json`, `icons/<stem>.png` (64×64 RGBA, stem = game texture basename), `abilities.json`
(game ability id → name, icon, skill line, class, type), `skill_lines.json`, `mundus.json`, `sets.json`
(LibSets id → name, type, ESO-Hub path, perfected pairing), and the three `esohub/*_en.json` slug maps.

Work is tracked under epic `eso-build-o-rama-au6`; task ids below refer to its children.

## 1. Test a bundle before importing it

Never trust the release notes alone; they are written by the producer. Run the checks below from a worktree that has
`docs/handoff/` and the current `static/icons/`. Until `scripts/check_asset_bundle.py` exists (task `au6.1`), the
checks are the ones a prototype ran on 2026-10-06; the expected values are from the `u51-20261006` bundle.

| # | Check | Expected (u51-20261006) |
|---|---|---|
| T1 | `manifest.counts` equal the actual entries; every SHA-1 in `manifest.files` verifies; no file on disk is unlisted | 1,879 icons, 4,789 abilities, 70 lines, 13 mundus, 714 sets; 1,886 hashes, 0 mismatches |
| T2 | every icon is 64×64 RGBA PNG with a lowercase stem | 1,879 of 1,879 |
| T3 | `skill_lines.json` has the 21 slottable class lines with `category: class` and the right class (Appendix A of the brief) | all 21; plus 7 `Class Mastery (<class>)` passive-only lines, which are ignored |
| T4 | `mundus.json` ids and display names equal `MUNDUS_ABILITY_IDS` in `api_client.py` | 13 of 13 |
| T5 | fixtures: every stem in `docs/handoff/referenced-icons-u49-u50.txt` has a PNG; every row of `referenced-abilities-u49-u50.json` resolves by id or, for pseudo-ids, by `grimoire_icon_stems`; every class-icon row maps to a class line; Carve, Rend, Bone Surge map to Two Handed, Dual Wield, Undaunted | 357/357; 474/474; 228/228; yes |
| T6 | live data: for `https://esobuild.com/<update>/builds.json`, every slotted ability resolves, every referenced icon has a PNG, every `set_id` other than 0 is in `sets.json` with the same name | u51: 6,055 slots resolved (6,014 by id, 41 by grimoire icon), 291/291 icons, 134/134 sets |
| T7 | icon diff against `static/icons`: list new stems, pixel-different stems, and site-only stems | 219 new, 9 pixel-different, 9 site-only (`gp_class_*`, `abilityframe64_up`, `ridingskill_ready`, all site-authored and must survive) |

Read the release notes after the checks pass, specifically the "What the importer should know" list. For
`u51-20261006` the items that change our code are:

- ESO Logs pseudo-ids for scribed skills run from 1000 to at least 1022, not 1008. Look every id up in
  `abilities.json` first and fall back to the grimoire icon stem when absent; never test `id >= 1009`.
- `abilities.json` carries 1,607 `variant_of` entries (internal effects, bar swaps, retired ranks) and 7 Class Mastery
  lines. Use `skill_line` and `category`, never the icon family, to decide whether an ability is a class ability.
- ESO-Hub mundus pages are `/en/mundus-stones/<slug>`; the site's current `/en/guides/<slug>` returns 404
  (verified 2026-10-06). `mundus.json` has the right paths.
- Gear with `set_id` 0 and an empty name appears in `builds.json`; skip it.
- The 9 pixel-different icons are the game's updated Dragonknight, Sorcerer pet and Warden art; the bundle wins.

## 2. Use it: phased integration

Order matters: phase 1 needs no code and fixes visible defects today; phase 2 is the behaviour change; phase 3 and 4
are quality and tooling.

### Phase 1: icons and attribution (`au6.2`)

Copy `icons/` into `static/icons/` add-or-update only. Never delete: the 9 site-authored files are not in any bundle.
The hourly cron copies `static/icons` into `output/u51/static/icons`, so u51 pages pick the new icons up on the next
run. Archived updates serve their committed per-update copy (see `docs/UPDATE_FLIP.md`), so the Rampage icon that
`eso-build-o-rama-2m6` reports must also be copied into `output/u50/static/icons/` and committed. Update
`templates/about.html`: icons are extracted from the game client via UESP's EsoExtractData by ESO Log Tail; they are
© ZeniMax Online Studios; ability and set data from UESP (CC-BY-SA 2.5); set ids from LibSets.

### Phase 2: tables and id-based skill-line detection (`au6.6`, decision `au6.3`)

Store `abilities.json`, `skill_lines.json`, `mundus.json`, `sets.json`, `manifest.json` under `data/game/u51/`.
The repo ignores `*.json`, so force-add them, as `docs/UPDATE_FLIP.md` does for `builds.json`. Load the table for
`current_update` from `data/update_config.json`, falling back to the newest `data/game/*`.

Change `ESOSubclassAnalyzer` to resolve each slotted ability in this order: `ability_id` in `abilities.json` and
`category == class` → that line; else `ability_icon` in `grimoire_icon_stems` → a non-class line (excluded); else
the legacy name match, kept only as a last resort and logged when it fires. Keep the 21 abbreviations. Tests come
from `docs/handoff/referenced-abilities-u49-u50.json`.

Measured on live u51 (505 builds) against the stored slugs:

| Outcome | Builds |
|---|---|
| incomplete today, three class lines with id lookup | 51 |
| complete today but wrong (substring false positives such as Carve → Herald), corrected | 18 |
| still fewer than three class lines on the bars | 249 (164 DPS, 52 healers, 33 tanks) |
| of those, every detected line is native to the player's class | 246 |

The 249 are not a lookup gap: those players slot abilities from one or two class lines and fill the rest of the
bars with weapon, guild and scribed skills. How to label and group them is decision `au6.3`. Recommendation: pad
from the player's class-native lines and mark padded lines in the UI and in `builds.json`, since an ESO character
always has three lines and for a stock-class player the unslotted ones are known. Option A keeps `x`/Unknown;
option C shows only detected lines.

Rollout needs no migration. `DataStore.save_trial_builds` replaces a trial's whole entry on each scan, and reports
are cached, so the 14-hour cron cycle rewrites every trial's slugs with the new analyzer within a day of deploying.
Expect the build set to regroup (merges where false positives split builds, splits where they merged).

### Phase 3: ESO-Hub links (`au6.4`)

Mundus links from `mundus.json`; set links from `sets.json` by `set_id` with the slugify fallback only for unknown
ids. Add a deployment-check spot check that a few links return 200.

### Phase 4: tooling (`au6.1`, `au6.5`)

`scripts/check_asset_bundle.py` runs section 1 and exits non-zero on a contract failure.
`scripts/import_game_assets.py <tag|zip|dir>` downloads, checks, copies icons add-or-update, writes
`data/game/<update>/`, prints added/changed/removed counts and the force-add reminder. `deployment_check.py` gains a
builds.json-driven test that every referenced icon exists, and its ability-slot selector is fixed so the per-page
check stops silently skipping (`eso-build-o-rama-06l`).

## 3. Refresh routine for later bundles

1. ESO Log Tail publishes `esobuild-assets-<uXX>-<YYYYMMDD>`; the release notes carry its own V1–V7 numbers.
2. `python scripts/import_game_assets.py esobuild-assets-<uXX>-<YYYYMMDD>` from a worktree on a non-main branch.
3. Review the printed diff: new icons are new skills; pixel changes are art updates; removed icons never delete.
4. Run `scripts/pre-merge-check.sh output-dev/<uXX>` after a test scan, then merge. The next cron run deploys the
   icons for the active update; archived updates only change if their committed copy is updated on purpose.
5. If the bundle is for a new update, do this together with `docs/UPDATE_FLIP.md` step 3, before the first scan of
   the new update, so its first pages already use the new tables.

## 4. Verified state on 2026-10-06

Bundle `esobuild-assets-u51-20261006` (client `eso.live.12.1.5`, databuild of 2026-09-25, UESP fetched 2026-10-06)
passed every check in section 1 independently of the producer's notes. It is ready to import; nothing in the site
consumes it yet.
