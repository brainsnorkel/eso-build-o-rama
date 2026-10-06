# Export request: game-mined icons and ability data for esobuild.com

Written 2026-10-06 in the `eso-build-o-rama` repo (the generator behind [esobuild.com](https://esobuild.com)).
Addressed to whoever works in `brainsnorkel/eso-live-encounterlog-sets-abilities` (ESO Log Tail) on the Windows
machine that has an installed ESO client and UESP's EsoExtractData. The ask is a repeatable export utility in that
repo, run now against the live Update 51 client and again after each later patch, that produces a bundle this site
can import. Update 51 is live and the site is moving its active update to `u51` as this is written; `u50` becomes
archived content and needs no bundle of its own (icons are shared across updates on the site).

The three fixture files beside this document travel with it:

| File | Rows | What it is |
|---|---|---|
| `referenced-icons-u49-u50.txt` | 357 | every icon stem slotted on a top-ranked player's bar in the site's U49 and U50 data |
| `referenced-abilities-u49-u50.json` | 474 | every distinct (ability id, name, icon) tuple from the same data, with how often it was seen |
| `extra-icon-stems.txt` | 2 | referenced stems outside the `ability_*` family that the normal extraction misses |

## 1. The task in one paragraph

Add `scripts/export_esobuild_assets.py` (name is a suggestion) that writes a versioned bundle containing: the full
`ability_*` icon family as 64 px PNGs plus an explicit list of extra stems; an ability table keyed by game ability id
that gives each id its skill line, icon and type; a skill-line table that says which lines are class lines; the 13
mundus boon ids; a set table keyed by LibSets id with ESO-Hub slugs; and a manifest that records the client version
and the update tag. Reuse `scripts/extract_ability_icons.py` for icons and `scripts/generate_esohub_links.py` for
ESO-Hub slugs. Section 4 is the contract, section 5 the checklist, section 7 the validation to run before handing
over.

## 2. Why: what is broken today, with numbers

The site renders each build's two ability bars with the game's icons and labels every build by its three class skill
lines (for example `ardent-ass-herald`). Both depend on tables that are hand-typed in the site repo and were last
refreshed by hand. Measured on 2026-10-06 against the live U50 data (454 builds) and the committed U49 data (404 builds):

- **Skill-line detection**: 253 of 454 live U50 builds have fewer than three detected class lines and render as
  "Unknown". Of the 228 class-family abilities slotted in top builds, 25 are unknown to the site's name table. They
  are almost all renames from the 2026 class rework: Dragonfire Breath, Searing Claw, Heart of Flame, Magma Fist,
  Earthshield Mantle, Chains of Dominance, Blood of the Green Dragon, Vibrant Shroud, Tidal Chakram, Ritual of
  Retribution, Ice Fortress, Healthy Offering and more. The full list is in section 7, check V3.
- **Same table, same staleness, in your repo**: the site's `SKILL_LINE_ABILITIES` in `subclass_analyzer.py` is the
  table that lives in your `src/eso_sets.py`. Your `docs/research/esohub-icons-and-tooltips.md` section 5 measured
  39 of its 378 names as no longer existing. One generated table fixes both consumers.
- **Name matching is unsafe**: the site matches by case-insensitive substring in either direction, so `Carve`
  attributes to Herald of the Tome (via Fatecarver), `Rend` to Living Death (via Render Flesh) and `Bone Surge` to
  Storm Calling (via Surge). An id-keyed table removes the heuristic.
- **Icons go missing silently**: ESO Logs returns the game's texture basename for each slotted ability and the site
  looks up `static/icons/<stem>.png` (1,669 files, imported once in October 2025, patched by hand since). When U49
  renamed the Stonefist morph textures to `ability_dragonknight_013_stonefist_{a,b}` the site served a broken image
  on about 19 pages before anyone noticed. Today one referenced stem is absent from the site's set and also from your 1,956-icon set:
  `achievement_u26_skyrim_werewolfdevour100` (werewolf Rampage, 5 slots in U50; the U51 launch check found the same
  gap independently). Your set already has 297 stems the site lacks, including 58 `ability_u49_*` and 6 `ability_u51_*`.
- **No version provenance**: the site tags content `u48`, `u49`, `u50` by configuration, and its attempt to derive the
  update from the ESO Logs game version string fails for current versions (every U50 trial is tagged
  `unknown-20261001`). The bundle must therefore carry an explicit update tag and the raw client version.

## 3. How the site consumes the assets (contracts to match)

Read this before designing the output. Every rule here is checked by section 7.

### 3.1 Icons

- ESO Logs gives `abilityIcon` as the game texture basename, lowercase, without path or extension
  (`ability_arcanist_003_a`). The page template emits `<img src="../static/icons/{{ stem }}.png">`. CSS shows it at
  48 px (40 px on mobile); the committed files are 64×64.
- **The stem is the key.** Do not rename, alias, deduplicate identical images, or change case. One file per stem,
  `icons/<stem>.png`, 64×64 RGBA PNG, stem identical to the game basename.
- Scope is the whole `ability_*` family (so new skills are covered before anyone notices) plus the stems in
  `extra-icon-stems.txt`. Player bars occasionally reference other families; today that is one `achievement_*` and
  one `u38_*` stem. The site does not use `death_recap_*`.

### 3.2 Ability ids

- ESO Logs `abilityGameID` (the `guid` of a slotted talent) is the game's ability id, the same id space as UESP's
  `minedSkills`. Verified: id 183006 is "Cephaliarch's Flail" with texture `ability_arcanist_003_a` and skill line
  "Herald of the Tome" on both sides.
- Slotted ids are rank or morph specific, not base ids. The fixture shows Blighted Blastbones as 117690 and 117693,
  Incapacitating Strike as 36508 and 113105, Ulfsild's Contingency as 222678 and 240150. The table must resolve
  **every** rank and morph id, not only base ids.
- Scribed skills arrive with ESO Logs pseudo-ids 1000 to 1008, names such as
  `Shocking Banner (Class Flourish / Courage)`, and the grimoire's icon (`ability_grimoire_support`). For those the
  site will attribute by icon stem, so each grimoire needs an icon-stem to skill-line entry (section 4.3).

### 3.3 Skill lines

The site keeps exactly 21 class skill lines with fixed abbreviations (Appendix A) and builds its slug from the top
three. Everything else (weapon, armor, guild, world, alliance war, racial, craft, scribing grimoires) must be
identifiable so it is excluded on purpose rather than by failing to match.

### 3.4 Mundus

The site reads each player's buffs from ESO Logs and matches the 13 boon ability ids 13940 to 13985 (Appendix B).
UESP names them "Boon: The Warrior"; the site displays "The Warrior" and links `eso-hub.com/en/guides/the-warrior`.
Icons are `ability_mundusstones_0NN`, already inside the `ability_*` family.

### 3.5 Sets

ESO Logs gives `set_id` and `set_name` per gear piece in the LibSets id space (270 is Slimecraw). The site links to
ESO-Hub by naive slugify of the name, the approach your research measured at 38 misses in 722. Wanted: id to canonical
name, ESO-Hub slug, type, and the perfected pairing.

### 3.6 Update tags

The site's `data/update_config.json` names updates `u48` to `u51`; `u51` has been the active update since 2026-10-06
and the earlier three are archived. The bundle takes the tag
from the command line and records the client's own version string beside it. Never infer the tag from a date or from
the eso.mnf modification time.

## 4. Deliverable: bundle layout and schemas

```
esobuild-assets-<uXX>-<YYYYMMDD>.zip
  manifest.json
  icons/<stem>.png              one per stem, 64x64
  abilities.json
  skill_lines.json
  mundus.json
  sets.json
  esohub/skills_en.json         copies of your generated maps, unchanged
  esohub/sets_en.json
  esohub/scribing_en.json
```

Priorities: **P0** manifest, icons, abilities, skill_lines (these fix the two live defects). **P1** mundus, sets,
esohub. **P2** the optional enums in Appendix C.

JSON conventions: UTF-8, keys sorted, 1-space indent (matches your `manifest.json`), ids as strings when used as
object keys and as integers in values, stable ordering so two runs on the same client produce identical files apart
from `generated`.

### 4.1 manifest.json

```json
{
 "bundle_format": 1,
 "generator": "export_esobuild_assets.py@<git sha>",
 "generated": "2026-10-07T03:00:00+00:00",
 "update": "u51",
 "game": {
  "server": "live",
  "version": "<client version string, eso.live.x.y.z>",
  "eso_mnf": "C:\\...\\depot\\eso.mnf",
  "eso_mnf_modified": "<eso.mnf modification time, ISO 8601>"
 },
 "sources": {
  "icons": "eso.mnf via EsoExtractData 0.53",
  "abilities": "https://esolog.uesp.net/exportJson.php?table=skillTree (fetched 2026-10-07)",
  "sets": "LibSets_SetData.xlsm 2026-xx-xx + https://esolog.uesp.net/exportJson.php?table=setSummary",
  "esohub": "sitemaps fetched 2026-10-07"
 },
 "counts": {"icons": 1958, "abilities": 4210, "skill_lines": 61, "mundus": 13, "sets": 714},
 "files": {"icons/ability_arcanist_003_a.png": "<sha1>", "abilities.json": "<sha1>"},
 "licensing": "Icons (c) ZeniMax Online Studios, extracted from the user's client for display only. Ability and set text from UESP (CC-BY-SA 2.5). Set ids from LibSets by Baertram."
}
```

`update` comes from `--update`. `game.version` is the client's version string; take it from the client's version
file or from a recent `Encounter.log` `BEGIN_LOG` line, and leave it `""` rather than guess. `server` is `live` or
`pts`.

### 4.2 abilities.json

One entry per player-skill ability id, every rank and morph, plus the 13 mundus ids.

```json
{
 "update": "u51",
 "abilities": {
  "183006": {
   "name": "Cephaliarch's Flail",
   "icon": "ability_arcanist_003_a",
   "skill_line": "Herald of the Tome",
   "class": "Arcanist",
   "type": "active",
   "base_ability_id": 185817,
   "base_name": "Abyssal Impact",
   "morph": 1,
   "rank": 1
  }
 }
}
```

`type` is one of `active`, `ultimate`, `passive`. `class` is null for non-class lines. `icon` is the texture
basename, lowercase, no extension, so it joins directly to `icons/`. Include ids whose icon falls outside the
`ability_*` family exactly as the game names them.

### 4.3 skill_lines.json

```json
{
 "skill_lines": {
  "Herald of the Tome": {"category": "class", "class": "Arcanist", "ability_ids": [185817, 183006, "..."]},
  "Two Handed": {"category": "weapon", "class": null, "ability_ids": ["..."]},
  "Assault": {"category": "alliance-war", "class": null, "ability_ids": ["..."],
              "grimoire_icon_stems": ["ability_grimoire_assault"]}
 }
}
```

`category` is one of `class`, `weapon`, `armor`, `guild`, `world`, `alliance-war`, `racial`, `craft`. Each line
that owns a scribing grimoire lists the grimoire's icon stem(s) under `grimoire_icon_stems`, since scribed skills
reach the site with pseudo-ids and only the icon identifies the line. Exclude ESO-Hub's `vengeance-*` variants, or
flag them with `"ruleset": "vengeance"`; the site only sees standard-ruleset trial logs.

### 4.4 mundus.json

```json
{
 "mundus": {
  "13940": {"name": "The Warrior", "game_name": "Boon: The Warrior",
            "icon": "ability_mundusstones_001", "esohub": "/en/guides/the-warrior"}
 }
}
```

Keep the display names in Appendix B; they are what the site's existing pages and ESO-Hub links use.

### 4.5 sets.json

```json
{
 "sets": {
  "270": {"name": "Slimecraw", "type": "Monster", "max_equip": 2,
          "perfected_id": null, "unperfected_id": null, "esohub": "/en/sets/slimecraw"}
 }
}
```

Key is the LibSets id (UESP `setSummary.gameId` is the same number; the full table downloaded fine today, 714
records, fields `setName`, `gameId`, `type`, `setMaxEquipCount`, `setBonusDesc1..`). Pair perfected and
unperfected sets by the "Perfected X" / "Perfect X" naming rule from your research notes; apply your Appendix A
aliases when deriving `esohub`. A set with no ESO-Hub page gets `"esohub": null`, never a guessed slug.

## 5. Requirements checklist

Each item is checkable; the why is attached so the implementation can deviate where the why still holds.

- **R1 Icons.** Every `ability_*` stem present in eso.mnf, plus every stem in `extra-icon-stems.txt`, exists as
  `icons/<stem>.png` at 64×64. Extra stems that cannot be found are listed in the run summary and in
  `manifest.json` under `"missing_extra_stems"`, never dropped silently. Why: a missing icon is invisible until a
  reader hits a broken image; the site has no fallback image.
- **R2 Extra stems via exact name.** Use EsoExtractData `-n <name>` for the extra list; it reloads the MNF per
  file (about 3 s) which is fine for a dozen files and avoids pulling the 34,600-file icon folder. Accept
  `--extra-stems <file>` so the site can grow the list without a code change.
- **R3 Abilities.** `abilities.json` resolves every id in `referenced-abilities-u49-u50.json` with id ≥ 1009, and
  every entry whose icon starts with a class family (`ability_dragonknight`, `ability_sorcerer`,
  `ability_nightblade`, `ability_templar`, `ability_warden`, `ability_necromancer`, `ability_arcanist`) carries one
  of the 21 class lines. Why: this is the defect behind 253 "Unknown" builds.
- **R4 Skill lines.** All 21 class lines in Appendix A are present with `category: class` and the right class.
  Every grimoire has an icon-stem entry. Why: the site's build slug depends on exactly these 21 names.
- **R5 Manifest provenance.** `update`, `game.version`, `game.server`, `eso_mnf_modified`, per-file SHA-1 and
  source URLs with fetch dates. Why: the site publishes per-update pages and must be able to say which client a
  table came from when a reader disputes a build label.
- **R6 Re-runnable.** Flags: `--update uXX` (required), `--eso-dir`, `--server live|pts`, `--out`, `--size`
  (default 64), `--extra-stems`, `--previous <bundle>` (prints added, removed and changed entries, the way
  `extract_ability_icons.py` does for icons), `--check-fixtures <dir>` (runs section 7), `--dry-run`. Why: the next
  update follows within months and each PTS cycle can change names.
- **R7 Determinism.** Two runs against the same client differ only in `generated` and fetch dates. Why: lets the
  site diff bundles meaningfully.
- **R8 Do not commit the bundle to the repo.** Publish as a GitHub release asset (suggested tag
  `esobuild-assets-u51-<YYYYMMDD>`) so both repos stay small and the site can fetch with `gh release download`.
  Decided; see section 9.
- **R9 Licensing text in the manifest** as in 4.1; the site's About page will credit UESP, EsoExtractData,
  LibSets and the ZeniMax ownership notice using that text.

Non-goals: do not change the site, do not call ESO-Hub's tooltip API, do not include `death_recap_*` or companion
assets, do not produce WebP or sizes under 64 px, do not rename or alias stems.

## 6. Sources and what to reuse

### 6.1 Icons

`scripts/extract_ability_icons.py` already does the hard part (table dump, offset calibration, range extraction,
Pillow conversion, manifest with SHA-1s). Run it with `--size 64 --out <bundle>/icons` and add the extra-stems
pass. Your current manifest (eso.mnf modified 2026-09-29) predates the Update 51 client, so let the launcher finish
patching and re-run against the new eso.mnf first. UESP's mined tables can lag a new update by days; before trusting
`abilities.json`, confirm that a skill renamed or added in Update 51 resolves with its new name (compare against a
fresh `Encounter.log` or the client's lang data), and say in the release notes which UESP fetch date the table
reflects.

### 6.2 Ability table

Two options; prefer (a) unless (b) is already solved in your tooling.

(a) UESP's esolog export, keyed by game id. Verified fields today:

- `exportJson.php?table=skillTree&id=183006` returns one row per (ability, rank): `abilityId`, `displayId`,
  `skillTypeName` (`"Arcanist::Herald of the Tome"`, the class before `::`), `baseName`, `name`, `rank`,
  `maxRank`, `type` (`Active`), `cost`, `icon` (`/esoui/art/icons/ability_arcanist_003_a.dds`), `description`,
  `learnedLevel`, `skillIndex`.
- `exportJson.php?table=minedSkills&id=183006` adds `baseAbilityId`, `morph`, `rank`, `isPassive`, `classType`,
  `skillLine`, `texture`, `prevSkill`, `nextSkill`.
- `minedSkills&id=13940` is `"Boon: The Warrior"` with texture `ability_mundusstones_001`, empty `skillLine`.

Your research notes record that list queries were sometimes answered with a Cloudflare challenge while per-id
lookups worked; `setSummary` without an id downloaded fine from here today. Try the full `skillTree` table first
and fall back to per-id requests for the fixture's ids plus the full class lines. Your research notes record UESP's
licence as CC-BY-SA 2.5 and a warning that excessive usage can lead to blocking, so cache the raw responses in the
bundle's working folder and fetch once per run.

(b) Game files: EsoExtractData can also extract the `.lang` tables and skill data, from which name, icon and skill
line can be rebuilt without UESP. This is more work and only worth it if UESP lags a PTS build you need.

### 6.3 Sets and ESO-Hub maps

`scripts/generate_esohub_links.py` and `scripts/generate_gear_data.py` as they are; drop a current
`LibSets_SetData.xlsm` into `data/gear_sets/` first. Add UESP `setSummary` for `type` and `setMaxEquipCount`.

### 6.4 Client version

A recent `Encounter.log` carries the client version on its `BEGIN_LOG` line (`eso.live.x.y.z`) and ESO Log Tail
already parses that line; reuse it, or read the version from the client install if you know where it is stored. If
neither is available, leave `""`.

## 7. Validation before hand-over

Run these with `--check-fixtures <folder containing the three fixture files>` and put the numbers in the release
notes.

- **V1** Every stem in `referenced-icons-u49-u50.txt` has `icons/<stem>.png`. Expected 357 of 357. Both current
  icon sets score 356 of 357; the miss is `achievement_u26_skyrim_werewolfdevour100`.
- **V2** Every `ability_id` ≥ 1009 in `referenced-abilities-u49-u50.json` is a key in `abilities.json`. Report
  how many names and icons match the fixture exactly and list the differences; ESO Logs occasionally trails the
  game by a patch, so a short mismatch list is information, not failure.
- **V3** Every fixture row with a class-family icon maps to a class line. These 25 names must resolve (ESO Logs id
  in brackets): Vibrant Shroud [28311], Healthy Offering [34727], Shrewd Offering [34721], Tidal Chakram [186209],
  Heart of Flame [32785], Soul of Flame [32792], Earthshield Mantle [20328], Shatterspike Mantle [20323],
  Chains of Dominance [20496], Incinerate [32853], Searing Claw [20668], Blood of the Green Dragon [32744],
  Blood of the Elder Dragon [32722], Fire Keeper [20779], Hearth and Home [32710], Magma Fist [31816],
  Dragonfire Breath [20917], Disintegrating Dragonfire [20944], Engulfing Dragonfire [20930],
  Protect the Brood [21017], Fleetstep Wings [21014], Ritual of Retribution [22259], Regenerative Ward [29482],
  Ice Fortress [86130], Twilight Tormentor Enrage [77140].
- **V4** Carve [38745] maps to Two Handed, Rend [85187] to Dual Wield, Bone Surge [42176] to Undaunted. None of
  them is a class line.
- **V5** Every `ability_grimoire_*` stem in the fixture appears in some line's `grimoire_icon_stems`.
- **V6** `manifest.counts` equal the actual file and entry counts and every listed SHA-1 verifies.
- **V7** Running twice yields identical files except `generated` and fetch dates.

## 8. What the site will do with the bundle (context, not your task)

A follow-up in `eso-build-o-rama` adds `scripts/import_game_assets.py <bundle.zip>` that copies `icons/` into
`static/icons/` (add or update, never delete), writes the JSON tables under `data/game/<uXX>/`, and prints the diff.
The subclass analyzer then resolves skill lines by ability id first, by grimoire icon stem for pseudo-ids, and by
name only as a last resort; the deployment check gains a test that every icon referenced by `builds.json` exists.
Related tracked work there: `eso-build-o-rama-06l` (log missing icons during a scan), `eso-build-o-rama-2m6` (the
werewolf icon missing on U51 pages), `eso-build-o-rama-399` (Unknown subclasses), `eso-build-o-rama-xqr` (update tag
never derived from game version).

## 9. Decisions (all resolved with Chris, 2026-10-06)

- **Q1 Delivery.** GitHub release asset on the ESO Log Tail repo: one zip per bundle, release tag
  `esobuild-assets-<uXX>-<YYYYMMDD>`, validation numbers from section 7 in the release notes. Do not commit the
  bundle to either repo.
- **Q2 U51 timing (resolved 2026-10-06).** Update 51 is live. Build the bundle from the live client with
  `--server live --update u51`; no PTS bundle and no `u50` bundle are needed.
- **Q3 Sizes.** 64 px only. The site scales in CSS; no 40 px set.
- **Q4 Enums.** Include `enums.json` (Appendix C) only if it falls out of data you already mine; if it needs new
  tooling, skip it. It stays P2.

## Appendix A: the 21 class skill lines and the site's abbreviations

The abbreviation is what appears in build slugs and page titles; the set per class is what the site uses to bold a
build's own class lines.

| Class | Skill line | Abbreviation |
|---|---|---|
| Dragonknight | Ardent Flame | Ardent |
| Dragonknight | Draconic Power | Draconic |
| Dragonknight | Earthen Heart | Earthen |
| Sorcerer | Dark Magic | Dark |
| Sorcerer | Daedric Summoning | Daedric |
| Sorcerer | Storm Calling | Storm |
| Nightblade | Assassination | Ass |
| Nightblade | Shadow | Shadow |
| Nightblade | Siphoning | Siphon |
| Templar | Aedric Spear | Spear |
| Templar | Dawn's Wrath | Dawn |
| Templar | Restoring Light | Resto |
| Warden | Animal Companions | Animal |
| Warden | Green Balance | Green |
| Warden | Winter's Embrace | Winter |
| Necromancer | Grave Lord | Grave |
| Necromancer | Bone Tyrant | Bone |
| Necromancer | Living Death | Living |
| Arcanist | Herald of the Tome | Herald |
| Arcanist | Curative Runeforms | Curative |
| Arcanist | Soldier of Apocrypha | Soldier |

Note: ESO Logs spells the class `DragonKnight`; the site normalises class names case-insensitively, so use the
game's spelling `Dragonknight` in the bundle.

## Appendix B: mundus boon ids the site matches

| Ability id | Display name |
|---|---|
| 13940 | The Warrior |
| 13943 | The Mage |
| 13974 | The Serpent |
| 13975 | The Thief |
| 13976 | The Lady |
| 13977 | The Steed |
| 13978 | The Lord |
| 13979 | The Apprentice |
| 13980 | The Ritual |
| 13981 | The Lover |
| 13982 | The Atronach |
| 13984 | The Shadow |
| 13985 | The Tower |

## Appendix C: optional enumerations (P2)

The site maps ESO Logs `trait` and `enchant` integers to names with hand-typed tables (`TRAIT_NAMES`,
`ENCHANT_NAMES` in `data_parser.py`). The trait table has duplicate names at different ids (Reinforced at 4 and 8,
Infused at 3, 16, 22 and 26, Harmony at 14 and 17), which suggests at least some entries are wrong. Those integers
are ESO Logs' own enumeration, so a game-side `ITEM_TRAIT_TYPE_*` table may not line up one to one. If it is cheap,
include `enums.json` with the game's trait type and glyph enumerations (id, constant name, display name) so Chris
can cross-check; if it is not cheap, skip it.
