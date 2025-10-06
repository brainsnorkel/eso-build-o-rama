# ESO Build-O-Rama

Automated analysis and visualization of top-performing Elder Scrolls Online trial builds from ESO Logs.

**Live Site**: [esobuild.com](https://esobuild.com)

## Overview

ESO Build-O-Rama scans the top-ranked ESO Logs trial reports, identifies common builds among elite players, and generates static web pages showcasing these builds. Each trial is scanned independently on a staggered schedule to manage API load and ensure fresh data.

### Build Classification

A build is featured if it appears frequently in the top 10 ranked logs for a specific boss:
- **DPS Builds**: 5 or more occurrences
- **Tank/Healer Builds**: 3 or more occurrences

### Build Definition

A "build" consists of:
1. **Three Subclasses**: Skill lines identified from ability usage patterns
2. **Two 5-Piece Gear Sets**: The dominant armor/weapon sets

## Features

### Data Collection
- Analyzes top 10 ESO Logs reports per boss encounter
- Consolidates identical builds across multiple reports
- Deduplicates same character appearing in multiple reports
- Applies role-based occurrence thresholds
- Extracts per-player mundus stones via source-filtered buff queries

### Captured Build Data
- Gear (all equipment pieces with traits and enchantments)
- Abilities (both skill bars including ultimates)
- Subclasses (detected from skill usage patterns)
- Gear Sets (5-piece, 2-piece, and arena weapons)
- Mundus Stones (from buff uptime data)
- Performance metrics (DPS, rankings, report links)
- Occurrence frequency across top logs

### User Interface
- Desktop: Full-width tables with sortable columns
- Mobile: Card-based layout for screens ≤768px width
- Responsive design with proper touch targets
- Ability icons and visual set indicators
- Direct links to source ESO Logs reports

### Performance
- Response caching reduces API calls by approximately 97%
- Incremental data storage between scans
- Staggered trial scanning (one trial every 30 minutes)
- Rate limit compliance (2-second delays, automatic retry)
- Static HTML generation for fast page loads

### Deployment
- GitHub Actions for automated scanning
- Staggered schedule (each trial updated every 7 hours)
- GitHub Pages hosting with CDN distribution
- Branch isolation (develop for testing, main for production)

## Installation

### Prerequisites
- Python 3.9 or higher
- ESO Logs API credentials from [esologs.com/api/clients](https://www.esologs.com/api/clients)
- Git

### Setup

```bash
# Clone repository
git clone https://github.com/brainsnorkel/eso-build-o-rama.git
cd eso-build-o-rama

# Install dependencies
pip install -r requirements.txt

# Configure API credentials (add to shell profile)
export ESOLOGS_ID="your_client_id"
export ESOLOGS_SECRET="your_client_secret"
source ~/.zshrc  # or ~/.bashrc
```

### Branch Structure

**Main Branch** (`main`):
- Production code
- Outputs to `output/` directory
- Triggers GitHub Actions on push
- Deploys to esobuild.com

**Development Branch** (`develop`):
- Feature development and testing
- Outputs to `output-dev/` directory (gitignored)
- Does not trigger GitHub Actions
- Safe for local testing

## Usage

### Scan Commands

```bash
# Scan all trials
python -m src.eso_build_o_rama.main

# Scan specific trial by ID
python -m src.eso_build_o_rama.main --trial-id 15  # Rockgrove

# Scan specific trial by name
python -m src.eso_build_o_rama.main --trial "Dreadsail Reef"

# Test mode (first trial only)
python -m src.eso_build_o_rama.main --test
```

### Cache Management

```bash
# View cache statistics
python -m src.eso_build_o_rama.main --cache-stats

# Clear cache before scan
python -m src.eso_build_o_rama.main --trial-id 17 --clear-cache

# Disable caching
python -m src.eso_build_o_rama.main --trial-id 17 --no-cache
```

### Manual Workflow Triggers

```bash
# Trigger specific trial
gh workflow run "Generate ESO Builds (Staggered)" -f trial_id=15

# Check status
gh run list --workflow="Generate ESO Builds (Staggered)" --limit 5

# View logs
gh run view <run_id> --log
```

### Local Testing

```bash
# On develop branch
git checkout develop
python -m src.eso_build_o_rama.main --trial-id 1

# Serve locally
cd output-dev
python3 -m http.server 8080 &
ngrok http 8080
```

## Trial Reference

| ID | Trial Name                  | Abbr |
|----|-----------------------------|------|
| 1  | Aetherian Archive           | AA   |
| 2  | Hel Ra Citadel              | HRC  |
| 3  | Sanctum Ophidia             | SO   |
| 5  | Maw of Lorkhaj              | MoL  |
| 6  | The Halls of Fabrication    | HoF  |
| 7  | Asylum Sanctorium           | AS   |
| 8  | Cloudrest                   | CR   |
| 12 | Sunspire                    | SS   |
| 14 | Kyne's Aegis                | KA   |
| 15 | Rockgrove                   | RG   |
| 16 | Dreadsail Reef              | DSR  |
| 17 | Sanity's Edge               | SE   |
| 18 | Lucent Citadel              | LC   |
| 19 | Ossein Cage                 | OC   |

## Architecture

### System Overview

```
GitHub Actions (Staggered Schedule)
    |
    v
ESO Build-O-Rama Application
    |
    +-- API Client (GraphQL)
    +-- Data Parser (Gear, Abilities)
    +-- Build Analyzer (Consolidation)
    +-- Trial Scanner (Orchestration)
    +-- Cache Manager (Response Cache)
    +-- Data Store (builds.json)
    +-- Page Generator (HTML Templates)
    |
    v
GitHub Pages Deployment (esobuild.com)
```

### Data Flow

1. Fetch rankings from ESO Logs API
2. Download top 10 reports per boss
3. Parse gear, abilities, and performance data
4. Detect subclasses from ability usage
5. Identify gear sets from equipped items
6. Query buff table for per-player mundus stones
7. Consolidate identical builds across reports
8. Apply role-based occurrence thresholds
9. Save trial data to builds.json
10. Generate HTML from templates
11. Deploy to GitHub Pages

### Key Algorithms

**Build Identification**:
```python
# Normalize build for comparison
slug = sorted(subclasses) + sorted(top_two_sets)
slug = slug.lower().replace(' ', '-').replace("'", "")
```

**Build Consolidation**:
- Group by (trial, boss, build_slug)
- Merge all players with matching build
- Count unique reports (not total players)
- Select highest DPS as representative player
- Preserve mundus from any instance of same character

**Subclass Detection**:
- Count ability casts per skill line
- Weight ultimates more heavily
- Select top 3 skill lines by usage
- Normalize to abbreviated names

## API Integration

### ESO Logs GraphQL API

Authentication: OAuth 2.0  
API Version: v2

**Primary Queries**:
- `worldData.zones` - Trial and encounter IDs
- `characterRankings(leaderboard: LogsOnly)` - Top-ranked players per boss
- `reportData.report` - Full report data
- `reportData.report.table(dataType: Summary)` - Player performance and gear
- `reportData.report.table(dataType: Buffs, sourceID: X)` - Per-player buff uptime

**Rate Limiting**:
- API limit: 18,000 points/hour
- Report queries: 5-10 points each
- Request delay: 2 seconds minimum
- Retry attempts: 3 with exponential backoff (120s, 240s, 360s)
- Typical scan: ~200 points (well under limit)

### Caching

- **Location**: `cache/` directory (gitignored, persistent)
- **Duration**: Indefinite (manual clear only)
- **Effectiveness**: 95-97% cache hit rate
- **Key Format**: `{type}_{parameters_hash}`

**Cache Types**:
- Zone/encounter data
- Rankings
- Report data
- Player buffs

## Page Generation

### Templates (Jinja2)

- `base.html` - Base template with header, footer, responsive CSS
- `index_page.html` - Home page listing all trials and builds
- `trial.html` - Per-trial page with boss-grouped builds
- `build_page.html` - Detailed build page

### Responsive Breakpoints

- **Desktop** (≥1024px): Full tables, all columns visible
- **Tablet** (769-1023px): Tables with reduced padding
- **Mobile** (≤768px): Card-based layout with labeled fields

### Mobile Table Transformation

Tables convert to vertical cards on mobile:
- Each row becomes a standalone card
- Labels appear on left (40% width)
- Data appears on right (60% width)
- Touch-friendly links with padding
- No horizontal scrolling required

## GitHub Actions

### Schedule

Workflow runs every 30 minutes, cycling through 14 trials. Each trial updates approximately every 7 hours.

**Reference time**: Sunday 8:32 PM UTC

```
Index 0  (8:32 PM)  → Aetherian Archive
Index 1  (9:02 PM)  → Hel Ra Citadel
Index 2  (9:32 PM)  → Sanctum Ophidia
Index 3  (10:02 PM) → Maw of Lorkhaj
Index 4  (10:32 PM) → Halls of Fabrication
Index 5  (11:02 PM) → Asylum Sanctorium
Index 6  (11:32 PM) → Cloudrest
Index 7  (12:02 AM) → Sunspire
Index 8  (12:32 AM) → Kyne's Aegis
Index 9  (1:02 AM)  → Rockgrove
Index 10 (1:32 AM)  → Dreadsail Reef
Index 11 (2:02 AM)  → Sanity's Edge
Index 12 (2:32 AM)  → Lucent Citadel
Index 13 (3:02 AM)  → Ossein Cage
```

### Triggers

1. **Schedule**: `0,30 * * * *` (every 30 minutes)
2. **Manual**: Workflow dispatch with optional trial_id parameter
3. **Push**: Main branch only (develop branch excluded)

### Workflow Steps

1. Determine which trial to scan based on current time
2. Checkout latest code from main branch
3. Install Python 3.9 and dependencies
4. Download existing builds.json from live site
5. Run scan for determined trial
6. Copy static assets
7. Upload artifact to GitHub Pages
8. Deploy

### Branch Protection

Develop branch is prevented from deploying:
- Workflow triggers only on main branch
- Code checks for develop branch in GitHub Actions environment
- Exits with error if develop detected in CI/CD

## Data Models

### PlayerBuild
Individual player's build in a specific fight.

**Fields**:
- Character and account names
- Player ID (API source ID)
- Class and role
- DPS and performance metrics
- Gear with traits and enchantments
- Abilities (two skill bars)
- Subclasses (detected from abilities)
- Equipped sets
- Mundus stone
- Report and fight references

### CommonBuild
Build appearing multiple times across reports.

**Fields**:
- Build slug (normalized identifier)
- Subclasses and gear sets
- Count (total players)
- Report count (unique reports)
- Best player (highest DPS)
- All players list
- Trial and boss information

**Methods**:
- `get_display_name()` - Human-readable name with sorted subclasses
- `get_sorted_sets()` - Alphabetically sorted set list
- `meets_threshold()` - Role-based occurrence check

### GearPiece
Individual equipment piece.

**Fields**:
- Slot identifier
- Set name
- Item name
- Armor weight (L/M/H)
- Trait and trait ID
- Enchantment and enchant ID
- Item ID and quality

## Mundus Stone Detection

Mundus stones are identified through buff analysis:

1. Query Buffs table filtered by player's source_id
2. Match buff ability IDs against known mundus IDs (13940-13985)
3. Verify high uptime (mundus buffs persist throughout fight)
4. Map ability ID to mundus name

**Mundus Ability IDs**:
```
13940: The Warrior
13943: The Mage
13974: The Serpent
13975: The Thief
13976: The Lady
13977: The Steed
13978: The Lord
13979: The Apprentice
13980: The Ritual
13981: The Lover
13982: The Atronach
13984: The Shadow
13985: The Tower
```

## Project Structure

```
eso-build-o-rama/
├── .github/workflows/
│   └── generate-builds.yml          # CI/CD workflow
├── cache/                            # API response cache (gitignored)
├── data/
│   ├── trials.json                   # Trial definitions
│   └── trial_bosses.json             # Boss lists per trial
├── docs/                             # Additional documentation
├── output/                           # Production output (main)
│   └── builds.json                   # Persistent data (tracked)
├── output-dev/                       # Development output (gitignored)
├── src/eso_build_o_rama/
│   ├── main.py                       # Application orchestrator
│   ├── api_client.py                 # ESO Logs API client
│   ├── trial_scanner.py              # Scan orchestration
│   ├── data_parser.py                # Parse API responses
│   ├── build_analyzer.py             # Build identification
│   ├── subclass_analyzer.py          # Skill line detection
│   ├── page_generator.py             # HTML generation
│   ├── data_store.py                 # JSON persistence
│   ├── cache_manager.py              # Response caching
│   └── models.py                     # Data structures
├── static/icons/                     # Ability icons
├── templates/                        # Jinja2 templates
├── tests/                            # Test suite
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── README.md
└── requirements.txt
```

## Configuration

### Environment Variables

Required for API access:
```bash
export ESOLOGS_ID="your_client_id"
export ESOLOGS_SECRET="your_client_secret"
```

### Configuration Files

**data/trials.json**  
List of trials with IDs, names, and abbreviations.

**data/trial_bosses.json**  
Maps trial names to boss encounters in encounter order.

**.github/workflows/generate-builds.yml**  
GitHub Actions workflow configuration with scheduling, triggers, and deployment steps.

## Development Workflow

### Making Changes

```bash
# Switch to develop branch
git checkout develop

# Make changes and test locally
python -m src.eso_build_o_rama.main --trial-id 1

# Verify output in output-dev/
ls output-dev/

# Commit changes
git add .
git commit -m "description"
git push origin develop

# Test with local server
cd output-dev
python3 -m http.server 8080 &

# When ready, merge to main
git checkout main
git merge develop
git push origin main
```

### Output Directories

| Branch    | Output Dir    | Git Tracked | Deployed |
|-----------|---------------|-------------|----------|
| main      | `output/`     | builds.json only | Yes (GitHub Pages) |
| develop   | `output-dev/` | No (gitignored) | No |

### Testing Checklist

- Test on develop branch first
- Verify correct output directory
- Check logs for errors
- Test responsive layout (browser dev tools)
- Verify desktop layout unchanged
- Confirm data accuracy
- Review builds.json structure
- Merge to main when stable

## Troubleshooting

### No Publishable Builds Found

This is expected for older trials with diverse meta. Top players in trials like Sanctum Ophidia or Hel Ra Citadel may use varied builds that don't meet the 5+/3+ threshold. These trials won't appear on the index page.

### Mundus Showing Unknown

Indicates player had no mundus active during the fight or data parsing issue. Verify on ESO Logs directly and check application logs.

### Rate Limit Errors

Solutions:
- Increase `min_request_delay` in APIClient (default: 2.0s)
- Avoid `--clear-cache` unless necessary
- Wait 2-3 minutes between manual workflow triggers
- Automated schedule handles this automatically

### GitHub Actions Race Conditions

When triggering multiple workflows manually, wait 2-3 minutes between them. Each workflow downloads builds.json from the live site. If workflows overlap, the later one may download stale data before the earlier deployment completes.

### Template Changes Not Appearing

CDN caching on esobuild.com has 10-minute TTL (max-age=600). To see changes immediately:
- Hard refresh browser (Cmd/Ctrl + Shift + R)
- Wait 10 minutes for cache expiration
- Check deployment completed successfully

## Performance Metrics

**Typical Trial Scan**:
- API calls: 10-15 new requests, 300+ cached
- Duration: 5-12 minutes per trial
- Data volume: 100-500KB per trial
- Page generation: Under 1 second

**Resource Usage**:
- API points: ~200 per scan (1% of hourly limit)
- Storage: ~5MB per trial in builds.json
- Cache size: Varies, typically 50-200MB

## API Details

### Request Rate Limiting

```python
async def _retry_on_rate_limit(self, func, *args, **kwargs):
    for attempt in range(self.max_retries):
        await self._wait_for_rate_limit()  # 2s minimum
        try:
            return await func(*args, **kwargs)
        except RateLimitError:
            delay = self.retry_delay * (2 ** attempt)  # 120s, 240s, 360s
            await asyncio.sleep(delay)
```

### GraphQL Query Examples

**Fetch Top Rankings**:
```graphql
query GetRankings($zoneID: Int!, $encounterID: Int!) {
  characterRankings(
    zoneID: $zoneID
    encounterID: $encounterID
    leaderboard: LogsOnly
  )
}
```

**Fetch Player Buffs**:
```graphql
query GetBuffs($code: String!, $startTime: Float!, $endTime: Float!, $sourceID: Int!) {
  reportData {
    report(code: $code) {
      table(
        startTime: $startTime
        endTime: $endTime
        dataType: Buffs
        sourceID: $sourceID
      )
    }
  }
}
```

## Contributing

### Code Standards

- Type hints on all function signatures
- Docstrings for all public methods
- Logging at appropriate levels (INFO, WARNING, ERROR, DEBUG)
- Specific exception handling (KeyError, ValueError, TypeError)
- Async/await for all API operations

### Commit Message Format

```
type: Brief description

Longer explanation if needed.

CHANGES:
- Specific change 1
- Specific change 2

RESULT:
- Outcome or effect
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

## Recent Updates

### 2025-10-06

**Per-Player Mundus Detection**  
Fixed incorrect mundus stones by implementing source_id filtering in Buffs table queries.

**Mobile Responsiveness**  
Added responsive CSS that converts tables to card layout on screens ≤768px.

**UI Improvements**  
- Sorted subclasses alphabetically
- Updated page title to "BS ESO Meta Build Explorer"
- Accurate "About This Data" section
- Static generation timestamps
- Improved terminology

**Development Environment**  
- Branch-based output directories
- GitHub Actions filtering (main only)
- Safety checks for develop branch
- output-dev/ gitignored

**Build Consolidation**  
- Merge identical builds across reports
- Count unique reports
- Prevent duplicate players

See [CHANGELOG.md](CHANGELOG.md) for complete history.

## Credits

This project uses data and resources from:

- [ESO Logs](https://www.esologs.com) - Combat log data and rankings API
- [UESP.net](https://en.uesp.net/wiki/Online:Online) - ESO reference data
- [LibSets by Baertram](https://www.esoui.com/downloads/info2241-LibSets.html) - Gear set information
- [esoskillbarbuilder by sheumais](https://github.com/sheumais/esoskillbarbuilder) - Ability icons
- [ESO-Log-Build-and-Buff-Summary](https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary) - Subclass detection logic
- [The Elder Scrolls Online](https://www.elderscrollsonline.com) - Game content, Copyright ZeniMax Media Inc.

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright 2025 Chris Gentle ([@brainsnorkel](https://github.com/brainsnorkel))

This is a fan-made tool for the Elder Scrolls Online community. The Elder Scrolls Online and all related content are Copyright ZeniMax Media Inc. This project is not affiliated with or endorsed by ZeniMax Media Inc.

## Support

Report issues or request features: [GitHub Issues](https://github.com/brainsnorkel/eso-build-o-rama/issues)
