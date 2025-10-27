# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ESO Build-O-Rama is a static site generator that analyzes top-performing Elder Scrolls Online trial builds from ESO Logs. It scans leaderboard data, identifies common build patterns among elite players, and generates HTML pages showcasing these builds with full gear, abilities, and performance metrics.

**Live Site**: [esobuild.com](https://esobuild.com)

## Core Commands

### Development

```bash
# Scan specific trial by ID
python -m src.eso_build_o_rama.main --trial-id 15  # Rockgrove

# Scan specific trial by name
python -m src.eso_build_o_rama.main --trial "Dreadsail Reef"

# Scan all trials (production mode)
python -m src.eso_build_o_rama.main

# Test mode (first trial only)
python -m src.eso_build_o_rama.main --test
```

### Cache Management

```bash
# View cache statistics
python -m src.eso_build_o_rama.main --cache-stats

# Clear cache before scan
python -m src.eso_build_o_rama.main --trial-id 17 --clear-cache

# Disable caching (force fresh API calls)
python -m src.eso_build_o_rama.main --trial-id 17 --no-cache

# Migrate cache to new structure
python utils/migrate_cache.py --dry-run
python utils/migrate_cache.py
```

### Testing

```bash
# Serve locally
cd output-dev && python3 -m http.server 8080

# Run deployment checks (REQUIRED before merging to main)
./scripts/pre-merge-check.sh output-dev
python3 scripts/deployment_check.py output-dev

# Test API client
python tests/test_api_client.py
python tests/test_build_analysis.py
```

### GitHub Actions

```bash
# Trigger specific trial manually
gh workflow run "Generate ESO Builds (Staggered)" -f trial_id=15

# Check workflow status
gh run list --workflow="Generate ESO Builds (Staggered)" --limit 5

# View logs
gh run view <run_id> --log
```

## Architecture

### Data Flow Pipeline

1. **Fetch Rankings**: Query ESO Logs API for top 10 ranked reports per boss
2. **Download Reports**: Fetch full report data for each ranked log
3. **Parse Player Data**: Extract gear, abilities, performance metrics
4. **Detect Subclasses**: Analyze ability usage to identify skill lines (top 3)
5. **Identify Gear Sets**: Parse equipped items to find 5-piece/2-piece sets
6. **Query Mundus Stones**: Use per-player buff queries with sourceID filtering
7. **Build Consolidation**: Group identical builds across reports, count occurrences
8. **Apply Thresholds**: Filter builds by role-based minimums (5+ DPS, 3+ tank/healer)
9. **Persist Data**: Save to `builds.json` with incremental updates
10. **Generate HTML**: Render Jinja2 templates with responsive design
11. **Deploy**: GitHub Actions pushes to GitHub Pages

### Key Architecture Patterns

**Build Identification System**:
- Build uniqueness determined by: 3 sorted subclasses + 2 sorted gear sets
- Build slug format: `subclass1-subclass2-subclass3-set1-set2`
- Normalization: lowercase, no spaces, no apostrophes
- Example: `ardent-ass-herald-deadly-strike-perfected-ansuuls-torment`

**Build Consolidation Algorithm**:
- Group all players by (trial, boss, build_slug)
- Count unique reports (not total players) for threshold checks
- Deduplicate same character appearing in multiple reports
- Select highest DPS player as representative
- Preserve mundus stone from any instance of same character

**Subclass Detection**:
- Count ability casts per skill line from combat logs
- Weight ultimates more heavily than normal abilities
- Select top 3 skill lines by weighted usage
- Normalize to abbreviated names (e.g., "Ardent Flame" → "Ardent")

**Mundus Stone Detection**:
- Query Buffs table with `sourceID` filtering (per-player)
- Match buff ability IDs against known mundus IDs (13940-13985)
- Verify high uptime (mundus buffs persist throughout fight)
- Map ability ID to mundus name

### Module Structure

**Core Orchestration**:
- `main.py` - Application entry point, CLI argument handling, branch detection
- `trial_scanner.py` - Coordinates scanning across multiple bosses per trial
- `data_store.py` - Manages `builds.json` persistence and incremental updates

**Data Processing**:
- `api_client.py` - ESO Logs OAuth + GraphQL client with caching and rate limiting
- `data_parser.py` - Parses API responses into PlayerBuild objects
- `build_analyzer.py` - Consolidates builds, applies thresholds
- `subclass_analyzer.py` - Detects skill lines from ability usage patterns

**Output Generation**:
- `page_generator.py` - Renders Jinja2 templates, generates sitemap/robots.txt
- `social_preview_generator.py` - Creates Open Graph images for social sharing
- `csv_exporter.py` - Exports build data to CSV format

**Data Models** (`models.py`):
- `PlayerBuild` - Individual player's build in a specific fight
- `CommonBuild` - Build appearing multiple times across reports
- `GearPiece` - Individual equipment piece with traits/enchants
- `TrialReport` - Container for trial/boss data and all associated builds

## Branch Strategy

### Critical Branch Behavior

**Main Branch** (`main`):
- Production code only
- Outputs to `output/` directory
- Triggers GitHub Actions on push
- Deploys to esobuild.com via GitHub Pages
- Only `builds.json` is git-tracked in output directory

**Development Branch** (`develop`):
- Active development branch
- Outputs to `output-dev/` directory (gitignored)
- Does NOT trigger GitHub Actions
- Safe for local testing
- Use this for all development work

### Pre-Merge Requirements

**BEFORE merging ANY branch to main**, you MUST:

1. Generate test build: `python3 -m src.eso_build_o_rama.main --trial-id 1`
2. Run deployment check: `./scripts/pre-merge-check.sh output-dev`
3. All checks must pass (exit code 0)
4. Only then merge: `git checkout main && git merge develop`

**Deployment checks validate**:
- Home page loads with trial content
- Trial pages have bosses and builds
- Build pages have player info
- Mundus stones are not "Unknown"
- No missing ability icons

### Workflow Protection

The application includes multiple safety checks:
- Main entry point (`main.py`) detects current branch
- Exits with error if develop branch detected in GitHub Actions environment
- Workflow YAML only triggers on main branch pushes
- Branch-specific output directories prevent accidental overwrites

## API Integration Details

### ESO Logs GraphQL API

**Authentication**: OAuth 2.0 with environment variables:
```bash
export ESOLOGS_ID="your_client_id"
export ESOLOGS_SECRET="your_client_secret"
```

**Primary Queries**:
- `worldData.zones` - Trial and encounter metadata (IDs, names)
- `characterRankings(leaderboard: LogsOnly)` - Top-ranked players per boss
- `reportData.report` - Full report with fight data
- `reportData.report.table(dataType: Summary)` - Player performance and gear
- `reportData.report.table(dataType: Buffs, sourceID: X)` - Per-player buff uptime

**Rate Limiting Strategy**:
- API limit: 18,000 points/hour
- Report queries: 5-10 points each
- Minimum request delay: 2 seconds between calls
- Retry attempts: 3 with exponential backoff (120s, 240s, 360s)
- Typical scan: ~200 points (well under limit)
- HTTP 429 triggers automatic retry with increasing delays

### Caching System

**Cache Architecture**:
- Location: `cache/` directory (gitignored, persistent across runs)
- Structure: Subdirectories for buffs, tables, rankings, reports
- Duration: Indefinite (manual clear only)
- Effectiveness: 95-97% cache hit rate in production
- Key format: `{type}_{parameters_hash}`

**Cache Performance**:
- Reduces API calls by 97% after initial scan
- ~46MB cache with 1,500+ files (typical)
- Enables rapid rescans for testing and development
- Cache migration utilities handle structure changes

## Configuration Files

**data/trials.json**:
- List of trials with IDs, names, abbreviations
- Maps trial IDs to ESO Logs zone IDs

**data/trial_bosses.json**:
- Maps trial names to boss encounters in order
- Used for page navigation and build grouping

**.github/workflows/generate-builds.yml**:
- Staggered schedule: one trial per hour
- Each trial updates every 14 hours (14 trials × 1 hour)
- Reference time: 20:00 UTC = Aetherian Archive (index 0)
- Includes backup/restore logic for builds.json

## Deployment System

### GitHub Actions Staggered Schedule

The workflow runs every hour on the hour, cycling through 14 trials:

```
Index 0  (20:00 UTC) → Aetherian Archive
Index 1  (21:00 UTC) → Hel Ra Citadel
Index 2  (22:00 UTC) → Sanctum Ophidia
Index 3  (23:00 UTC) → Maw of Lorkhaj
Index 4  (00:00 UTC) → Halls of Fabrication
Index 5  (01:00 UTC) → Asylum Sanctorium
Index 6  (02:00 UTC) → Cloudrest
Index 7  (03:00 UTC) → Sunspire
Index 8  (04:00 UTC) → Kyne's Aegis
Index 9  (05:00 UTC) → Rockgrove
Index 10 (06:00 UTC) → Dreadsail Reef
Index 11 (07:00 UTC) → Sanity's Edge
Index 12 (08:00 UTC) → Lucent Citadel
Index 13 (09:00 UTC) → Ossein Cage
```

### Workflow Steps

1. Calculate trial index from current UTC hour
2. Download existing `builds.json` from live site
3. Create timestamped backup (keeps last 5)
4. Run scan for determined trial
5. Validate builds.json structure and content
6. Copy static assets (icons only, not social previews)
7. Upload artifact to GitHub Pages
8. Deploy to production

**Important**: Social preview images in `output/static/` are pre-optimized (167KB) and committed to repo. The workflow does NOT overwrite these with freshly generated (240KB) images from `static/`.

## Key Data Models

### PlayerBuild

Individual player's build in a specific fight.

**Critical Fields**:
- `character_name`, `account_name` - Player identity
- `player_id` - API source ID for buff queries
- `class_name`, `role` - Character class and role
- `dps` - Damage per second (preserved through analysis)
- `gear` - List of GearPiece objects with traits/enchants
- `abilities_bar1`, `abilities_bar2` - Two skill bars with abilities
- `subclasses` - List of 3 detected skill lines
- `sets_equipped` - Dictionary of set names to piece counts
- `mundus` - Mundus stone name
- `report_code`, `fight_id` - Link back to source ESO Logs report

**Key Methods**:
- `get_build_slug()` - Generates normalized build identifier
- `get_top_two_sets()` - Returns the two sets with most pieces equipped

### CommonBuild

Build appearing multiple times across reports.

**Critical Fields**:
- `build_slug` - Normalized identifier (subclasses + sets)
- `subclasses` - List of 3 skill lines
- `sets` - List of gear set names
- `count` - Total players with this build
- `report_count` - Unique reports (used for threshold checks)
- `best_player` - Highest DPS player with this build
- `all_players` - List of all PlayerBuild instances

**Key Methods**:
- `get_display_name()` - Human-readable name with sorted subclasses
- `get_sorted_sets()` - Alphabetically sorted set list
- `meets_threshold()` - Role-based occurrence check (5+ DPS, 3+ tank/healer)

## Trial Reference

| ID | Trial Name                | Abbreviation |
|----|---------------------------|--------------|
| 1  | Aetherian Archive         | AA           |
| 2  | Hel Ra Citadel           | HRC          |
| 3  | Sanctum Ophidia          | SO           |
| 5  | Maw of Lorkhaj           | MoL          |
| 6  | The Halls of Fabrication | HoF          |
| 7  | Asylum Sanctorium        | AS           |
| 8  | Cloudrest                | CR           |
| 12 | Sunspire                 | SS           |
| 14 | Kyne's Aegis             | KA           |
| 15 | Rockgrove                | RG           |
| 16 | Dreadsail Reef           | DSR          |
| 17 | Sanity's Edge            | SE           |
| 18 | Lucent Citadel           | LC           |
| 19 | Ossein Cage              | OC           |

## Troubleshooting

### No Publishable Builds Found

Expected behavior for older trials with diverse meta. Top players may use varied builds that don't meet the 5+/3+ occurrence threshold. These trials won't appear on the index page until enough common patterns emerge.

### Rate Limit Errors

Solutions:
- Increase `min_request_delay` in APIClient initialization (default: 2.0s)
- Avoid `--clear-cache` unless absolutely necessary
- Wait 2-3 minutes between manual workflow triggers
- Let automated schedule handle timing naturally

### GitHub Actions Race Conditions

When triggering multiple workflows manually, wait 2-3 minutes between them. Each workflow downloads builds.json from the live site. If workflows overlap, the later one may download stale data before the earlier deployment completes.

### Template Changes Not Appearing

CDN caching on esobuild.com has 10-minute TTL (max-age=600). To see changes immediately:
- Hard refresh browser (Cmd/Ctrl + Shift + R)
- Wait 10 minutes for CDN cache expiration
- Check deployment completed successfully in GitHub Actions

### Mundus Showing Unknown

Indicates player had no mundus active during fight or data parsing issue. Verify on ESO Logs directly and check application logs for buff query issues.

## Critical Implementation Notes

### DPS Preservation

DPS values MUST be preserved throughout the analysis pipeline. The build analysis process sorts players by DPS and selects the highest DPS player as the representative for each CommonBuild. Any code that modifies PlayerBuild objects must preserve the `dps` field.

### Build Consolidation Timing

Builds are NOT filtered by threshold during initial analysis. The `BuildAnalyzer` returns ALL builds from a fight, then consolidation happens across multiple reports in `DataStore`. Only after consolidation does threshold filtering occur via `get_publishable_builds()`. This allows builds to accumulate occurrences across reports before being evaluated.

### Mundus Detection Requirements

Mundus stone detection requires `sourceID` filtering in buff queries. Without per-player filtering, all mundus stones from all players appear in results. The `api_client.py` must use:
```graphql
table(dataType: Buffs, sourceID: $playerID)
```

### Branch Safety Checks

Multiple layers prevent accidental production deployment from develop:
1. Workflow YAML triggers only on main branch
2. `main.py` checks git branch and exits in CI if develop detected
3. Output directory differs by branch (output/ vs output-dev/)
4. Pre-merge checks enforce validation before merging

## SEO and Social Features

### Structured Data

All pages include JSON-LD structured data:
- **Home page**: WebSite schema with Elder Scrolls Online context
- **Trial pages**: BreadcrumbList for navigation hierarchy
- **Build pages**: HowTo schema with gear/ability steps + BreadcrumbList

### Social Media Preview Images

Generated via Pillow with trial-specific backgrounds:
- Home page: Generic ESO logo
- Trial pages: Trial-specific boss art
- Build pages: Trial-specific backgrounds
- Production images: Pre-optimized to 167KB (committed to repo)
- Development images: Generated fresh in `static/` (not deployed)

### Sitemap and Robots.txt

Automatically generated on every build:
- `sitemap.xml` - All pages with last modified dates, priorities
- `robots.txt` - Allows all crawlers, points to sitemap, excludes cache/

## Interactive Features

### ESO-Hub Tooltips

Gear set names and mundus stones have hover tooltips powered by ESO-Hub:
```html
<a href="https://eso-hub.com/en/sets/ansuuls-torment" class="eso-hub-link" data-eso-hub-tooltip="ansuuls-torment">Ansuul's Torment</a>
```

External JavaScript from ESO-Hub renders the tooltips with set bonuses, stats, and acquisition info.

### Responsive Design

- **Desktop** (≥1024px): Full tables with all columns
- **Tablet** (769-1023px): Tables with reduced padding
- **Mobile** (≤768px): Card-based layout, each row becomes vertical card

## Performance Metrics

**Typical Trial Scan**:
- API calls: 10-15 new requests, 300+ cached
- Duration: 5-12 minutes per trial
- Data volume: 100-500KB per trial
- Page generation: Under 1 second

**Resource Usage**:
- API points: ~200 per scan (1% of 18,000 hourly limit)
- Storage: ~5MB per trial in builds.json
- Cache size: 50-200MB typical
