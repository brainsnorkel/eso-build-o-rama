# ESO Build-O-Rama

A staggered daily scan of ESOLogs to publish new top-performing trial builds, with each trial updated independently.

## Project Overview

This project automates the process of:
- Scanning ESOLogs for top 10 logs per trial
- Extracting build information (gear, abilities, mundus, CP)
- Identifying common builds across top performers
- Publishing static web pages showcasing these builds
- Updating each trial independently on a staggered schedule (14 trials, 1 hour apart starting Sunday 1am UTC)

## Status

**Phase**: Testing & Refinement  
**Current**: End-to-end integration testing

### Completed (Phases 1-3)
- ✅ Repository setup and project structure
- ✅ API research and authentication
- ✅ Working API client with OAuth 2.0
- ✅ **API rate limiting with automatic retry** (0.5s delay, exponential backoff)
- ✅ Data models and parsers
- ✅ Subclass detection algorithm
- ✅ Build analysis engine
- ✅ Trial scanner orchestration
- ✅ Static page generator
- ✅ Responsive HTML templates
- ✅ Comprehensive test suite (7 passing tests)
- ✅ Main application script

### Recent Changes
- ✅ **Staggered Trial Scanning** - Each trial now runs on its own schedule
- ✅ **Incremental Updates** - Trial data persists between runs, allowing partial updates
- ✅ **Timestamp Display** - Each trial shows when it was last updated
- ✅ **CLI Support** - Can scan individual trials with `--trial-id` or `--trial` arguments

### Next Steps
- Integration testing with live API data
- Monitor staggered execution performance
- Deploy to GitHub Pages

## Features

### Rate Limiting
The API client includes automatic rate limiting to prevent hitting ESO Logs API limits:
- **API Limit**: 18,000 points per hour (report queries = 5-10 points each)
- **Minimum delay**: 2.0 seconds between requests (configurable)
- **Automatic retry**: Up to 3 retries on rate limit errors
- **Exponential backoff**: 120s, 240s, 360s retry delays
- **Transparent**: Works automatically without code changes

Configure rate limiting when creating the client:
```python
client = ESOLogsAPIClient(
    min_request_delay=2.0,  # 2 seconds between requests (default)
    max_retries=3,          # retry up to 3 times
    retry_delay=120.0       # start with 120s delay on rate limit
)
```

**Safe Operation**: With 2s delays and ~5-10 points per request, a single trial scan uses ~200 points (well within the 18,000/hour limit). Each trial runs 1 hour apart to ensure adequate rate limit recovery.

## Documentation

- [Requirements & Design](docs/requirements_and_design.md) - Original requirements and feature specifications
- [Project Plan](docs/project_plan.md) - Architecture, phases, and timeline
- [Open Questions](docs/open_questions.md) - Research items and unresolved questions
- [Changelog](CHANGELOG.md) - Version history and changes

## Development

### Prerequisites
- Python 3.9+
- ESO Logs API key (to be obtained)
- AWS account OR Cloudflare account (for hosting)

### Local Setup
```bash
# Clone the repository
git clone git@github.com:brainsnorkel/eso-build-o-rama.git
cd eso-build-o-rama

# Set up virtual environment (when ready)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.example .env
# Edit .env with your credentials
```

### Usage

The main script now supports different scanning modes:

```bash
# Scan all trials (full scan)
python -m src.eso_build_o_rama.main

# Scan a specific trial by ID
python -m src.eso_build_o_rama.main --trial-id 12  # Sunspire

# Scan a specific trial by name
python -m src.eso_build_o_rama.main --trial "Sunspire"

# Test mode (scan only first trial)
python -m src.eso_build_o_rama.main --test
```

**Trial IDs**:
- 1: Aetherian Archive (AA)
- 2: Hel Ra Citadel (HRC) 
- 3: Sanctum Ophidia (SO)
- 5: Maw of Lorkhaj (MoL)
- 6: Halls of Fabrication (HoF)
- 7: Asylum Sanctorium (AS)
- 8: Cloudrest (CR)
- 12: Sunspire (SS)
- 14: Kyne's Aegis (KA)
- 15: Rockgrove (RG)
- 16: Dreadsail Reef (DSR)
- 17: Sanity's Edge (SE)
- 18: Lucent Citadel (LC)
- 19: Ossein Cage (OC)

## Architecture

**Data Flow**: ESO Logs API → Data Collection → Build Analysis → Incremental Data Storage → Page Generation → Static Hosting

**Components**:
1. Data Collection Module - API client for ESO Logs
2. Build Analysis Module - Subclass detection and common build identification
3. Data Storage Module - JSON persistence for incremental trial updates
4. Page Generation Module - Static HTML generator with timestamp support
5. Deployment Module - GitHub Actions with staggered scheduling
6. Scheduler - 14 separate cron jobs (1 hour apart, Sunday 1am UTC start)

**Staggered Schedule**:
- Sunday 1:00 AM UTC: Aetherian Archive (AA)
- Sunday 2:00 AM UTC: Hel Ra Citadel (HRC)
- Sunday 3:00 AM UTC: Sanctum Ophidia (SO)
- Sunday 4:00 AM UTC: Maw of Lorkhaj (MoL)
- Sunday 5:00 AM UTC: Halls of Fabrication (HoF)
- Sunday 6:00 AM UTC: Asylum Sanctorium (AS)
- Sunday 7:00 AM UTC: Cloudrest (CR)
- Sunday 8:00 AM UTC: Sunspire (SS)
- Sunday 9:00 AM UTC: Kyne's Aegis (KA)
- Sunday 10:00 AM UTC: Rockgrove (RG)
- Sunday 11:00 AM UTC: Dreadsail Reef (DSR)
- Sunday 12:00 PM UTC: Sanity's Edge (SE)
- Sunday 1:00 PM UTC: Lucent Citadel (LC)
- Sunday 2:00 PM UTC: Ossein Cage (OC)

See [Project Plan](docs/project_plan.md) for detailed architecture.

## Contributing

This is currently a private project in early development.

## Credits

This project relies on and acknowledges:
- [ESO Logs](https://www.esologs.com) - For combat log data
- [UESP.net](https://en.uesp.net/wiki/Online:Online) - ESO reference and ability data
- [LibSets by Baertram](https://www.esoui.com/downloads/info2241-LibSets.html) - Set data
- [esoskillbarbuilder by sheumais](https://github.com/sheumais/esoskillbarbuilder) - Ability icons
- [ESO-Log-Build-and-Buff-Summary](https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary) - Subclass detection logic
- [The Elder Scrolls Online](https://www.elderscrollsonline.com) by ZeniMax Media Inc

## License

Copyright © 2025 [@brainsnorkel](https://github.com/brainsnorkel)
