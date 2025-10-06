# ESO Build-O-Rama

**BS ESO Meta Build Explorer** - Automated analysis and visualization of top-performing Elder Scrolls Online trial builds from ESO Logs.

🌐 **Live Site**: [esobuild.com](https://esobuild.com)

## Overview

ESO Build-O-Rama automatically scans the top-ranked ESO Logs trial reports, identifies common builds among elite players, and generates beautiful, mobile-responsive static web pages showcasing these meta builds. Each trial is scanned independently on a staggered daily schedule, ensuring the site always has fresh data without overwhelming the ESO Logs API.

### What Makes a Build "Common"?

A build is featured on the site if it appears frequently in the top 10 ranked logs for a specific boss:
- **DPS Builds**: 5 or more occurrences
- **Tank/Healer Builds**: 3 or more occurrences (since these roles are less common in top logs)

### Build Definition

For this tool, a "build" is defined as a unique combination of:
1. **Subclasses**: The 3 skill lines (e.g., Assassination, Dawn's Wrath, Herald of the Tome)
2. **Two 5-Piece Gear Sets**: The two dominant armor/weapon sets (e.g., Aegis Caller + Perfected Slivers of the Null Arca)

## Key Features

### 🎯 Data Collection & Analysis
- **Top 10 Logs Per Boss**: Analyzes the highest-ranked ESO Logs reports for each trial boss
- **Build Consolidation**: Merges identical builds across multiple reports into single entries
- **Smart Deduplication**: Handles same character appearing in multiple reports
- **Role-Based Thresholds**: Different minimum occurrences for DPS vs. support roles
- **Per-Player Mundus Stones**: Accurately identifies each player's mundus using source_id filtering

### 📊 Build Data Captured
- **Gear**: All equipment pieces with traits and enchantments
- **Abilities**: Both skill bars with ultimate abilities
- **Subclasses**: Detected from skill usage patterns
- **Sets**: Identifies 5-piece, 2-piece, and arena weapon sets
- **Mundus Stones**: Extracted from buff uptime data
- **Performance**: DPS, player rankings, and report links
- **Frequency**: How many times the build appears across top logs

### 🎨 Beautiful, Responsive UI
- **Desktop**: Full-width tables with sortable columns
- **Mobile**: Card-based layout that converts tables to stacked, labeled cards (≤768px)
- **Touch-Friendly**: Properly sized buttons and interactive elements
- **Modern Design**: Gradient backgrounds, glassmorphism effects, smooth animations
- **Accessible**: ARIA labels, semantic HTML, keyboard navigation

### ⚡ Performance & Efficiency
- **Response Caching**: Reduces redundant API calls by ~97%
- **Incremental Updates**: Trial data persists between scans
- **Staggered Scanning**: Each trial updates on its own schedule (every 7 hours)
- **Rate Limit Compliance**: 2-second delays between requests, automatic retry with exponential backoff
- **Static Generation**: Fast-loading HTML pages with no server processing

### 🔄 Automated Deployment
- **GitHub Actions**: Automated workflows for continuous updates
- **Daily Regeneration**: Each trial scanned once per day (staggered over 14 hours)
- **GitHub Pages**: Static hosting with CDN distribution
- **Branch Isolation**: Develop branch for testing, main for production

## Installation & Setup

### Prerequisites
- Python 3.9+
- ESO Logs API credentials ([obtain here](https://www.esologs.com/api/clients))
- Git

### Local Development Setup

```bash
# Clone the repository
git clone https://github.com/brainsnorkel/eso-build-o-rama.git
cd eso-build-o-rama

# Install dependencies
pip install -r requirements.txt

# Configure API credentials
# Add to ~/.zshrc or ~/.bashrc:
export ESOLOGS_ID="your_client_id"
export ESOLOGS_SECRET="your_client_secret"

# Reload environment
source ~/.zshrc  # or source ~/.bashrc
```

### Branch Strategy

**Main Branch** (`main`):
- Production-ready code
- Outputs to `output/` directory
- Triggers GitHub Actions on push
- Deploys to esobuild.com via GitHub Pages

**Development Branch** (`develop`):
- Feature development and testing
- Outputs to `output-dev/` directory (gitignored)
- Does NOT trigger GitHub Actions
- Safe for local experimentation

## Usage

### Scanning Trials

```bash
# Scan all trials (full scan - rarely needed)
python -m src.eso_build_o_rama.main

# Scan a specific trial by ID
python -m src.eso_build_o_rama.main --trial-id 15  # Rockgrove

# Scan a specific trial by name
python -m src.eso_build_o_rama.main --trial "Dreadsail Reef"

# Test mode (scan only first trial with logs)
python -m src.eso_build_o_rama.main --test
```

### Cache Management

```bash
# View cache statistics
python -m src.eso_build_o_rama.main --cache-stats

# Clear cache before running
python -m src.eso_build_o_rama.main --trial-id 17 --clear-cache

# Disable caching (force fresh API calls)
python -m src.eso_build_o_rama.main --trial-id 17 --no-cache
```

### Manual GitHub Actions Trigger

```bash
# Trigger a specific trial scan
gh workflow run "Generate ESO Builds (Staggered)" -f trial_id=15

# Check workflow status
gh run list --workflow="Generate ESO Builds (Staggered)" --limit 5

# View specific run logs
gh run view <run_id> --log
```

### Local Testing with ngrok

```bash
# On develop branch, run a trial scan
git checkout develop
python -m src.eso_build_o_rama.main --trial-id 1

# Serve the output-dev directory
cd output-dev
python3 -m http.server 8080 &

# Expose to internet with ngrok (in another terminal)
ngrok http 8080

# Access your development site at the ngrok URL
```

## Trial IDs Reference

| ID | Trial Name                  | Abbreviation |
|----|-----------------------------|--------------| 
| 1  | Aetherian Archive           | AA           |
| 2  | Hel Ra Citadel              | HRC          |
| 3  | Sanctum Ophidia             | SO           |
| 5  | Maw of Lorkhaj              | MoL          |
| 6  | The Halls of Fabrication    | HoF          |
| 7  | Asylum Sanctorium           | AS           |
| 8  | Cloudrest                   | CR           |
| 12 | Sunspire                    | SS           |
| 14 | Kyne's Aegis                | KA           |
| 15 | Rockgrove                   | RG           |
| 16 | Dreadsail Reef              | DSR          |
| 17 | Sanity's Edge               | SE           |
| 18 | Lucent Citadel              | LC           |
| 19 | Ossein Cage                 | OC           |

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions                          │
│  (Staggered Schedule: Every 30 min, 14 trials rotating)   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   ESO Build-O-Rama                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ API Client   │→ │ Data Parser  │→ │ Build        │     │
│  │ (GraphQL)    │  │ (Gear, Bars) │  │ Analyzer     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         │                                     │             │
│         ▼                                     ▼             │
│  ┌──────────────┐                   ┌──────────────┐      │
│  │ Cache        │                   │ Trial        │      │
│  │ Manager      │                   │ Scanner      │      │
│  └──────────────┘                   └──────────────┘      │
│                                             │              │
│                                             ▼              │
│                                   ┌──────────────┐         │
│                                   │ Data Store   │         │
│                                   │ (builds.json)│         │
│                                   └──────────────┘         │
│                                             │              │
│                                             ▼              │
│                                   ┌──────────────┐         │
│                                   │ Page         │         │
│                                   │ Generator    │         │
│                                   └──────────────┘         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              GitHub Pages (esobuild.com)                    │
│  ├── index.html (Home page with all trials)                │
│  ├── builds.json (Persistent data store)                   │
│  ├── {trial}.html (Per-trial pages)                        │
│  ├── {trial}-{boss}-{build-slug}.html (Build detail pages) │
│  └── static/ (Icons, CSS, assets)                          │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Fetch Rankings**: Query ESO Logs for top 10 LogsOnly ranked reports per boss
2. **Download Reports**: Get full report data including fights, players, and performance
3. **Parse Builds**: Extract gear, abilities, traits, enchantments from each player
4. **Detect Subclasses**: Analyze ability usage to determine skill line focus
5. **Identify Sets**: Find 5-piece and 2-piece gear sets from equipped items
6. **Fetch Mundus**: Query Buffs table filtered by source_id for per-player mundus stones
7. **Consolidate Builds**: Merge identical builds across multiple reports
8. **Apply Thresholds**: Filter builds by role-based occurrence minimums
9. **Save Data**: Persist trial data to builds.json for incremental updates
10. **Generate Pages**: Create HTML from templates with all builds and metadata
11. **Deploy**: Upload to GitHub Pages via Actions artifacts

### Key Algorithms

#### Build Slug Generation
```python
def get_build_slug(self):
    """Generate consistent slug for build comparison."""
    # Sort subclasses and top 2 sets alphabetically
    sorted_subclasses = sorted(self.subclasses)
    sorted_sets = sorted(self.get_top_sets())
    
    # Create normalized slug
    slug = '-'.join(sorted_subclasses + sorted_sets)
    return slug.lower().replace(' ', '-').replace("'", "")
```

#### Build Consolidation
```python
# Group builds by (trial, boss, build_slug)
# Merge all players with same build
# Count unique reports (not total players)
# Select best player by DPS
# Preserve mundus from any instance of same character
```

#### Subclass Detection
Analyzes ability usage patterns to identify the 3 dominant skill lines:
- Counts ability casts per skill line
- Weighs ultimate abilities more heavily
- Selects top 3 skill lines by weighted usage
- Normalizes to abbreviated names (e.g., "ass", "ardent", "herald")

## Configuration Files

### `data/trials.json`
List of all ESO trials with IDs, names, and abbreviations.

### `data/trial_bosses.json`
Maps trial names to their boss encounters in correct encounter order.

### `.github/workflows/generate-builds.yml`
GitHub Actions workflow with:
- Staggered cron schedule (every 30 minutes, rotating through trials)
- Manual workflow dispatch for testing
- Push trigger (main branch only)
- Automatic trial selection based on time
- GitHub Pages deployment

## API Integration

### ESO Logs GraphQL API

The tool uses the ESO Logs v2 GraphQL API with OAuth 2.0 authentication.

**Key Queries**:
- `worldData.zones`: Get trial IDs and encounter IDs
- `characterRankings`: Fetch top-ranked players/reports for a boss
- `reportData.report`: Get full report details (fights, players, performance)
- `reportData.report.table(dataType: Summary)`: Get player performance with combatantInfo (gear, abilities)
- `reportData.report.table(dataType: Buffs, sourceID: X)`: Get per-player buff uptime for mundus detection

**Rate Limiting**:
- **API Limit**: 18,000 points per hour
- **Report queries**: 5-10 points each
- **Our delays**: 2 seconds between requests
- **Retries**: 3 attempts with exponential backoff (120s, 240s, 360s)
- **Safety**: Each trial scan ~200 points, well under hourly limit

### Caching Strategy

Response caching reduces API load by ~97%:
- **Cache Location**: `cache/` directory (gitignored, persists between runs)
- **Cache Keys**: Based on request type and parameters (report code, encounter ID, etc.)
- **Cache Duration**: Permanent (until manually cleared)
- **Cache Effectiveness**: Typical scan hits cache for 300+ calls, only makes ~10 new API requests

**Cache Types**:
- Zone/encounter data (rarely changes)
- Rankings (changes weekly)
- Report data (permanent once logged)
- Player buffs (permanent once logged)

## Page Generation

### Templates (Jinja2)

- `base.html`: Base template with header, footer, and responsive CSS
- `index_page.html`: Home page showing all trials and builds
- `trial.html`: Per-trial page with boss-grouped builds
- `build_page.html`: Detailed build page with gear, abilities, mundus, and players

### Responsive Design

**Desktop (≥1024px)**:
- Full-width tables with all columns
- Hover effects and animations
- Multi-column layouts for abilities and info boxes

**Tablet (769px - 1023px)**:
- Slightly reduced padding
- Tables remain in table format
- Responsive grids for info boxes

**Mobile (≤768px)**:
- Tables convert to card-based layout
- Each row becomes a vertical card
- Labels on left, data on right
- Touch-friendly buttons (8-15px padding)
- No horizontal scrolling
- Reduced font sizes for readability

### Build Pages Include

- **Trial & Boss Information**: Where the build was found
- **Model Player**: Highest DPS player with this build
- **Mundus Stone**: Per-player mundus (filtered by source_id)
- **Ability Bars**: Both skill bars with ability icons and names
- **Gear Table**: All equipment with sets, traits, and enchantments
- **Sets Used**: Visual badges showing all equipped sets with piece counts
- **Other Example Players**: All players using this build with links to their logs

## GitHub Actions Workflow

### Staggered Schedule

The workflow runs **every 30 minutes**, cycling through all 14 trials sequentially. Each trial is scanned approximately **every 7 hours** (14 trials × 30 minutes).

**Current Schedule** (starts Sunday 8:32 PM UTC):
```
Index 0  (8:32 PM) → Aetherian Archive
Index 1  (9:02 PM) → Hel Ra Citadel
Index 2  (9:32 PM) → Sanctum Ophidia
Index 3  (10:02 PM) → Maw of Lorkhaj
Index 4  (10:32 PM) → Halls of Fabrication
Index 5  (11:02 PM) → Asylum Sanctorium
Index 6  (11:32 PM) → Cloudrest
Index 7  (12:02 AM) → Sunspire
Index 8  (12:32 AM) → Kyne's Aegis
Index 9  (1:02 AM) → Rockgrove
Index 10 (1:32 AM) → Dreadsail Reef
Index 11 (2:02 AM) → Sanity's Edge
Index 12 (2:32 AM) → Lucent Citadel
Index 13 (3:02 AM) → Ossein Cage
(Then repeats)
```

### Workflow Triggers

1. **Scheduled**: Every 30 minutes (cron: `0,30 * * * *`)
2. **Manual**: Via GitHub web UI or `gh workflow run`
3. **Push**: Only on `main` branch (develop branch does NOT trigger workflows)

### Workflow Steps

1. **Determine Trial**: Calculate which trial to scan based on current time
2. **Checkout Code**: Get latest code from main branch
3. **Setup Python**: Install Python 3.9 and dependencies
4. **Download builds.json**: Get existing trial data from esobuild.com
5. **Run Scan**: Execute `python -m src.eso_build_o_rama.main --trial-id X`
6. **Copy Assets**: Include static files (icons, CSS)
7. **Deploy**: Upload to GitHub Pages and deploy

### Branch Protection

The workflow is configured to **prevent develop branch** from deploying to production:
- Workflow only triggers on `main` branch pushes
- Safety check in code exits if develop branch detected in GitHub Actions
- Develop branch uses `output-dev/` directory (gitignored)

## Development Workflow

### Working on Features

```bash
# Switch to develop branch
git checkout develop

# Make your changes
# ... edit files ...

# Test locally (outputs to output-dev/)
python -m src.eso_build_o_rama.main --trial-id 1

# View results locally with ngrok
cd output-dev
python3 -m http.server 8080 &
ngrok http 8080
# Access the ngrok URL to test

# Commit to develop
git add .
git commit -m "feat: Your feature description"
git push origin develop

# When ready to deploy, merge to main
git checkout main
git merge develop
git push origin main  # This triggers deployment
```

### Output Directories

| Branch    | Output Dir  | Committed? | Deployed?  |
|-----------|-------------|------------|------------|
| `main`    | `output/`   | No*        | Yes (GH Pages) |
| `develop` | `output-dev/` | No (gitignored) | No |

*Only `output/builds.json` is tracked for data persistence.

## Data Models

### PlayerBuild
Represents a single player's build in a specific fight:
- Character and player names
- Player ID (source ID for API queries)
- Class and role
- DPS and performance metrics
- Gear with traits and enchantments
- Abilities (2 bars)
- Subclasses (detected)
- Sets equipped
- Mundus stone
- Report and fight references

### CommonBuild
Represents a build that appears multiple times:
- Build slug (normalized identifier)
- Subclasses and sets
- Count (total players with this build)
- Report count (unique reports)
- Best player (highest DPS)
- All players (list of everyone using this build)
- Trial and boss information
- Methods: `get_display_name()`, `get_sorted_sets()`, `meets_threshold()`

### GearPiece
Individual equipment piece:
- Slot (head, chest, main_hand, etc.)
- Set name
- Item name
- Armor weight (L/M/H)
- Trait and trait ID
- Enchantment and enchant ID
- Item ID and quality

## API Client Features

### Automatic Rate Limiting
```python
async def _retry_on_rate_limit(self, func, *args, **kwargs):
    """Retry API calls with exponential backoff on rate limits."""
    for attempt in range(self.max_retries):
        try:
            # Wait minimum delay between requests
            await self._wait_for_rate_limit()
            
            # Make the API call
            result = await func(*args, **kwargs)
            return result
            
        except RateLimitError:
            # Exponential backoff: 120s, 240s, 360s
            delay = self.retry_delay * (2 ** attempt)
            logger.warning(f"Rate limited, retrying in {delay}s...")
            await asyncio.sleep(delay)
```

### Mundus Stone Detection

Mundus stones are identified using a sophisticated buff analysis:

1. **Query Buffs Table**: Filter by player's source_id
2. **Match Ability IDs**: Check against known mundus IDs (13940-13985)
3. **Verify High Uptime**: Mundus buffs have ~100% uptime throughout fight
4. **Map to Names**: Convert ability ID to mundus name (e.g., 13975 → "The Thief")

**Mundus Ability IDs**:
```python
MUNDUS_ABILITY_IDS = {
    13940: "The Warrior",
    13943: "The Mage",
    13974: "The Serpent",
    13975: "The Thief",
    13976: "The Lady",
    13977: "The Steed",
    13978: "The Lord",
    13979: "The Apprentice",
    13980: "The Ritual",
    13981: "The Lover",
    13982: "The Atronach",
    13984: "The Shadow",
    13985: "The Tower"
}
```

## Troubleshooting

### Common Issues

**"No publishable builds found"**
- This is normal for older trials (e.g., Sanctum Ophidia, Hel Ra Citadel)
- Top players use diverse/experimental builds
- No single build meets the 5+ (DPS) or 3+ (Tank/Healer) threshold
- Trial won't appear on index page (expected behavior)

**"Mundus showing as Unknown"**
- Usually means player had no mundus active during fight
- Check ESO Logs directly to verify
- Could indicate data parsing issue (check logs)

**Rate Limit Errors**
- Increase `min_request_delay` in APIClient (default: 2.0s)
- Use `--clear-cache` cautiously (forces many API calls)
- Wait between manual trial triggers (2-3 minutes minimum)

**GitHub Actions Race Condition**
- If triggering multiple workflows manually, wait 2-3 minutes between them
- Each workflow downloads builds.json from live site
- If workflows run too close together, later one downloads stale data
- Automated schedule handles this automatically

### Debug Mode

Enable detailed logging:
```python
logging.basicConfig(level=logging.DEBUG)
```

Check specific components:
```bash
# View cache stats
python -m src.eso_build_o_rama.main --cache-stats

# Clear cache and run fresh
python -m src.eso_build_o_rama.main --trial-id 15 --clear-cache

# Check git branch detection
python3 -c "import subprocess; result = subprocess.run(['git', 'branch', '--show-current'], capture_output=True, text=True, check=True); print(f'Branch: {result.stdout.strip()}')"
```

## Project Structure

```
eso-build-o-rama/
├── .github/
│   └── workflows/
│       └── generate-builds.yml          # GitHub Actions workflow
├── cache/                                # API response cache (gitignored)
├── data/
│   ├── trials.json                       # Trial IDs and names
│   └── trial_bosses.json                 # Boss lists per trial
├── docs/                                 # Project documentation
├── output/                               # Production output (main branch)
│   └── builds.json                       # Persistent trial data (tracked)
├── output-dev/                           # Development output (gitignored)
├── src/eso_build_o_rama/
│   ├── __init__.py
│   ├── main.py                           # Main orchestrator
│   ├── api_client.py                     # ESO Logs API client
│   ├── trial_scanner.py                  # Trial scanning orchestration
│   ├── data_parser.py                    # Parse API responses
│   ├── build_analyzer.py                 # Identify common builds
│   ├── subclass_analyzer.py              # Detect skill line usage
│   ├── page_generator.py                 # Generate HTML pages
│   ├── data_store.py                     # JSON persistence
│   ├── cache_manager.py                  # Response caching
│   └── models.py                         # Data models
├── static/
│   └── icons/                            # Ability icons
├── templates/
│   ├── base.html                         # Base template with CSS
│   ├── index_page.html                   # Home page template
│   ├── trial.html                        # Trial page template
│   └── build_page.html                   # Build detail template
├── tests/                                # Test suite
├── .gitignore                            # Git ignore rules
├── CHANGELOG.md                          # Version history
├── README.md                             # This file
└── requirements.txt                      # Python dependencies
```

## Recent Updates

### October 6, 2025

**Per-Player Mundus Detection**
- Fixed issue where builds showed incorrect mundus stones
- Implemented source_id filtering for Buffs table queries
- Each player now gets their own accurate mundus (e.g., Tentaculaire shows "The Thief" instead of "The Atronach")

**Mobile Responsiveness**
- Comprehensive mobile-first responsive design
- Tables convert to card layout on mobile devices
- Touch-friendly buttons and properly sized elements
- Desktop experience unchanged

**UI/UX Improvements**
- Sorted subclasses alphabetically in build display names
- Updated page title to "BS ESO Meta Build Explorer"
- Accurate "About This Data" section with clear threshold explanations
- Static generation timestamps (shows when page was built, not current time)
- Better terminology: "Subclassing" instead of "Build", "Frequency" instead of "Popularity"

**Development Environment**
- Branch-based output directories (main→output, develop→output-dev)
- GitHub Actions only triggers on main branch
- Safety checks prevent develop from running in CI/CD
- output-dev/ gitignored for clean repository

**Build Consolidation**
- Merge identical builds across multiple reports
- Count unique reports, not total player instances
- Preserve mundus data during consolidation
- Prevent duplicate players in build lists

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## Performance Metrics

**Typical Trial Scan**:
- **API Calls**: ~10-15 new calls (300+ cached)
- **Duration**: 5-12 minutes (depending on trial size)
- **Data Volume**: ~100-500KB per trial
- **Page Generation**: <1 second for all pages
- **Cache Effectiveness**: 95-97% of calls served from cache

**Resource Usage**:
- **API Points**: ~200 per trial scan (out of 18,000/hour limit)
- **Storage**: ~5MB per trial in builds.json
- **CDN Bandwidth**: Static files, minimal server load

## Contributing

### Code Standards
- Type hints for all function parameters and returns
- Comprehensive docstrings
- Logging at appropriate levels (INFO, WARNING, ERROR, DEBUG)
- Error handling with specific exception types
- Async/await for all API calls

### Testing Checklist
- [ ] Test on develop branch first
- [ ] Verify output-dev/ directory used
- [ ] Check logs for errors
- [ ] Test mobile responsiveness (browser dev tools)
- [ ] Verify desktop layout unchanged
- [ ] Confirm mundus stones are accurate
- [ ] Check builds.json structure
- [ ] Merge to main only when stable

### Pull Request Process
1. Create feature branch from `develop`
2. Make changes and test locally
3. Merge feature branch to `develop`
4. Test thoroughly on develop
5. Create PR: `develop` → `main`
6. Review and merge
7. Monitor first GitHub Actions deployment

## Credits & Acknowledgments

This project would not be possible without:

- **[ESO Logs](https://www.esologs.com)** - Combat log data and rankings API
- **[UESP.net](https://en.uesp.net/wiki/Online:Online)** - ESO reference data and ability information
- **[LibSets by Baertram](https://www.esoui.com/downloads/info2241-LibSets.html)** - Comprehensive gear set data
- **[esoskillbarbuilder by sheumais](https://github.com/sheumais/esoskillbarbuilder)** - Ability icons and assets
- **[ESO-Log-Build-and-Buff-Summary](https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary)** - Original subclass detection logic
- **[The Elder Scrolls Online](https://www.elderscrollsonline.com)** - Game content © ZeniMax Media Inc.

## License

MIT License - see [LICENSE](LICENSE) file for details.

Copyright © 2025 Chris Gentle ([@brainsnorkel](https://github.com/brainsnorkel))

This is a fan-made tool for the Elder Scrolls Online community. The Elder Scrolls Online and all related content are © ZeniMax Media Inc. This project is not affiliated with or endorsed by ZeniMax Media Inc.

---

**Questions or Issues?** Open an issue on GitHub or reach out to [@brainsnorkel](https://github.com/brainsnorkel)
