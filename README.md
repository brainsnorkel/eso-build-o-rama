# ESO Build-O-Rama

A weekly scan of ESOLogs to publish new top-performing trial builds.

## Project Overview

This project automates the process of:
- Scanning ESOLogs for top 5 logs per trial
- Extracting build information (gear, abilities, mundus, CP)
- Identifying common builds across top performers
- Publishing static web pages showcasing these builds
- Updating weekly with new builds from the current game update

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

### Next Steps
- Integration testing with live API data
- Refine data parsing and error handling
- Implement GitHub Actions for weekly execution
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

**Safe Operation**: With 2s delays and ~5-10 points per request, a full scan of 14 trials uses ~2,800 points (well within the 18,000/hour limit).

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

# Install dependencies (when requirements.txt is created)
pip install -r requirements.txt

# Copy environment template and add your API keys
cp .env.example .env
# Edit .env with your credentials
```

## Architecture

**Data Flow**: ESO Logs API → Data Collection → Build Analysis → Page Generation → Static Hosting

**Components**:
1. Data Collection Module - API client for ESO Logs
2. Build Analysis Module - Subclass detection and common build identification
3. Page Generation Module - Static HTML generator
4. Deployment Module - Publisher to S3/Cloudflare
5. Scheduler - Weekly Lambda/Worker execution

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
