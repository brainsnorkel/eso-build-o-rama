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

### Phase 1: icons and attribution (`au6.2`, done)

Copy `icons/` into `static/icons/` add-or-update only (pixel-aware: the bundle re-encodes every PNG, so byte
comparison would churn 1,600 identical files). Never delete: the 9 site-authored files are not in any bundle.

**Two icon copies are served, and which one a page loads depends on when it was generated.**

- Pages generated from this change on reference `static/icons/` relative to their own update directory
  (`/u51/static/icons/`). The generator copies `static/` there on every run and the workflow refreshes it before
  every deploy, so an icon import is live on the next cron run.
- Pages committed before this change (the `u48`, `u49`, `u50` archives and the u51 pages live today) reference
  `../static/icons/`, which resolves to the root copy `output/static/icons/`. Nothing refreshes that copy: it was
  the October 2025 import plus one manual sync, and on 2026-10-06 it lacked the Stonefist icons (Magma Fist was a
  broken image on live pages). It is synced from `static/icons` in this change; sync it again (add-or-update,
  never delete) whenever an archived page needs an icon it lacks. `scripts/import_game_assets.py` does not touch
  it on purpose, since archives change rarely and deliberately.

`templates/about.html` now credits ESO Log Tail, UESP's EsoExtractData and ESO log data (CC-BY-SA 2.5), carries the
ZeniMax ownership notice, and keeps the sheumais credit for the original icon collection.

### Phase 2: tables and id-based skill-line detection (`au6.6`, decision `au6.3`, done)

The tables live under `data/game/u51/` (`src/eso_build_o_rama/game_data.py` loads them for `current_update`,
falling back to the newest imported update, and returns None when nothing is imported). The repo ignores `*.json`,
so they are force-added, as `docs/UPDATE_FLIP.md` does for `builds.json`.

`ESOSubclassAnalyzer.analyze_player` resolves each slotted ability in this order: `ability_id` in `abilities.json`
(a known id with no line, such as a mythic's granted skill, counts as resolved and belongs to no line); else
`ability_icon` in `grimoire_icon_stems` (a scribed skill's non-class line); else the legacy name match, only for
abilities the tables do not know, logged at debug level. Class lines are the 21 slottable ones; `Class Mastery`
passive lines and `variant_of` entries are ignored by construction. When fewer than three class lines are proven,
the rest are padded from the player's class-native lines (decision `au6.3`) and recorded in
`PlayerBuild.subclasses_padded` and `CommonBuild.subclasses_padded`, which `builds.json` round-trips. Pages mark
padded lines with a dotted underline and a hover note (`get_display_parts` returns `(name, is_base, is_padded)`).
Tests: `tests/test_game_data.py`, driven by `docs/handoff/referenced-abilities-u49-u50.json`.

Measured on live u51 (505 builds) against the stored slugs:

| Outcome | Builds |
|---|---|
| incomplete today, three class lines with id lookup | 51 |
| complete today but wrong (substring false positives such as Carve → Herald), corrected | 18 |
| still fewer than three class lines on the bars | 249 (164 DPS, 52 healers, 33 tanks) |
| of those, every detected line is native to the player's class | 246 |

The 249 are not a lookup gap: those players slot abilities from one or two class lines and fill the rest of the
bars with weapon, guild and scribed skills. Decision `au6.3` (2026-10-06): pad from the player's class-native lines
and mark padded lines in the UI and in `builds.json`, since an ESO character always has three lines and for a
stock-class player the unslotted ones are known. Re-deriving every live u51 best player's bars with the shipped
analyzer gives 256 builds with three proven lines, 178 with one padded line, 71 with two, and none left at `x`;
303 of 505 slugs change (padding plus the 18 corrections).

Rollout needs no migration. `DataStore.save_trial_builds` replaces a trial's whole entry on each scan, and reports
are cached, so the 14-hour cron cycle rewrites every trial's slugs with the new analyzer within a day of deploying.
Expect the build set to regroup (merges where false positives split builds, splits where they merged, and
`herald-x-x` style builds merging into their padded three-line slug).

### Phase 3: ESO-Hub links (`au6.4`, done)

`PageGenerator` looks mundus links up in `mundus.json` and set links in `sets.json` by name (the game's current
names, which match ESO Logs for every set seen in live data); the slugify fallback only runs for names the tables
do not know. The mundus filter had the dead `/en/guides/<slug>` pattern and was unused by any template; it now
produces `/en/mundus-stones/<slug>` and the build page links the mundus stone.

### Phase 4: tooling (`au6.1`, `au6.5`, done)

`scripts/check_asset_bundle.py <zip|dir> [--builds <path|url>]` runs section 1 (T1–T7) and exits non-zero on a
contract failure. `scripts/import_game_assets.py <tag|zip|dir> [--dry-run]` downloads with `gh release download`,
refuses to import on a failed check, copies icons add-or-update (pixel-aware), writes `data/game/<update>/`, and
prints the counts and the force-add reminder. `deployment_check.py` gained check 5 (every icon referenced by
`builds.json` exists in the update's `static/icons`) and its per-page selector now matches the markup the template
emits, so the per-page icon check runs instead of silently skipping (`eso-build-o-rama-06l`).

## 3. Refresh routine for later bundles

1. ESO Log Tail publishes `esobuild-assets-<uXX>-<YYYYMMDD>`; the release notes carry its own V1–V7 numbers.
2. `python scripts/import_game_assets.py esobuild-assets-<uXX>-<YYYYMMDD>` from a worktree on a non-main branch.
3. Review the printed diff: new icons are new skills; pixel changes are art updates; removed icons never delete.
4. Run `scripts/pre-merge-check.sh output-dev/<uXX>` after a test scan, then merge. The next cron run deploys the
   icons for the active update; archived updates only change if their committed copy is updated on purpose.
5. If the bundle is for a new update, do this together with `docs/UPDATE_FLIP.md` step 3, before the first scan of
   the new update, so its first pages already use the new tables.

## 4. State on 2026-10-06

Bundle `esobuild-assets-u51-20261006` (client `eso.live.12.1.5`, databuild of 2026-09-25, UESP fetched 2026-10-06)
passed every check in section 1 independently of the producer's notes and is imported: icons in `static/icons`
(219 new, 9 updated) and in the root copy `output/static/icons` (221 new including the Stonefist icons, 9 updated),
tables in `data/game/u51/`. All four phases above are implemented on branch `feat/game-asset-bundle`; the first
cron run after merging regenerates u51 with the new analyzer, and the remaining trials follow over the 14-hour
cycle.
