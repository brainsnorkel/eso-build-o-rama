# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Experimental (2025-10-07 - Fight Rankings Architecture)
- **NEW APPROACH**: Switched from characterRankings to fightRankings for discovering common builds
  - Uses fightRankings (speed metric) on final boss to get top 12 reports per trial
  - Extracts ALL boss fights from each top report (not just final boss)
  - Finds shortest/fastest attempt for each boss in each report
  - Analyzes all players from top-performing groups
  - Benefits: 70% fewer API calls, consistent data across all bosses, better efficiency
  - Created `utils/query_tester.py` for testing different query approaches
  - Changed output directory logic: main→output/, all others→output-dev/
  - Now processes 12 reports per trial (up from 5-10)
  - Validates fights match expected encounters before processing

### Added (2025-01-XX - Social Media Preview System)
- **Social Media Preview Functionality**: Comprehensive social media preview system for better link sharing
  - Added `social_preview_generator.py` with PIL-based image generation
  - Added Open Graph and Twitter Card meta tags to all HTML templates
  - Added Pillow dependency for image generation capabilities
  - Added page-specific social media metadata blocks for build, trial, and home pages
  - Added automatic social preview generation during build process
  - Added helper scripts for manual preview generation and testing
  - Generated 1200x630px preview images with site branding and color schemes
  - Supports both production (green/teal) and development (orange/amber) themes

### Removed (2025-01-XX - Social Media Preview Cleanup)
- **Social Media Preview Functionality**: Removed social media preview generation system
  - Removed `social_preview_generator.py` and related image generation code
  - Removed Open Graph and Twitter Card meta tags from HTML templates
  - Removed Pillow dependency from requirements.txt
  - Simplified page templates by removing social media metadata blocks
  - Fixed datetime generation to use UTC instead of local time in page generator

### Fixed (2025-10-06 - Per-Player Mundus Detection)
- **Correct Per-Player Mundus Stones**: Fixed issue where build pages showed incorrect mundus stones
  - Problem: Buffs table query returned ALL players' buffs, taking first mundus found (could be any player)
  - Root Cause: `player_id` (source ID) was extracted but never assigned to PlayerBuild objects
  - Solution: Added `player_id` to PlayerBuild, filter Buffs table by `source_id` for player-specific results
  - Example: Tentaculaire now correctly shows "The Thief" instead of "The Atronach"
  - Ensures each build page displays the actual mundus stone used by that specific player

### Added (2025-10-05 - Staggered Trial Scanning)
- **Staggered Trial Scanning**: Each trial now runs on its own schedule (14 trials, 1 hour apart starting Sunday 1am UTC)
- **Incremental Data Storage**: Trial build data persists in `output/builds.json` between runs
- **CLI Arguments**: Support for `--trial-id`, `--trial`, and `--test` arguments
- **Timestamp Display**: Each trial section shows when it was last updated
- **GitHub Actions Auto-Detection**: Workflow automatically determines which trial to scan based on current hour
- **Data Persistence Module**: New `data_store.py` module for JSON serialization/deserialization

### Changed (2025-10-05 - Staggered Trial Scanning)
- **Scanning Schedule**: From weekly full-scan to daily staggered per-trial scanning
- **Page Generation**: Index page now shows last-updated timestamps for each trial
- **Workflow Architecture**: Single workflow with 14 cron schedules instead of separate files
- **Data Flow**: Added incremental storage layer between scanning and page generation

### Added (2025-10-05 - Code Quality Improvements)
- **Code Quality Enhancements**: Comprehensive improvements to code maintainability and reliability
  - Extracted magic numbers to named constants (MINIMUM_SET_PIECES, DEFAULT_MIN_REQUEST_DELAY, etc.)
  - Added comprehensive input validation for all public API methods
  - Improved error handling with specific exception types (KeyError, ValueError, TypeError)
  - Enhanced type annotations with proper `Any` type usage
  - Fixed async/await warnings in test suite
  - Fixed failing test_common_build_identification test
- **Test Improvements**: 100% test pass rate with faster execution
  - All 7 unit tests now passing consistently
  - No async warnings in test suite
  - Improved test reliability and maintainability

### Added (2025-10-05 - Rate Limiting Update)
- **API Rate Limiting**: Added automatic rate limiting to API client
  - Configurable minimum delay between requests (default: 0.5s)
  - Automatic retry with exponential backoff on HTTP 429 errors (60s, 120s, 180s)
  - Transparent integration - no code changes needed in existing code
  - All API methods wrapped with retry logic
- Updated `trials.json`: Removed redundant `encounters` field
  - Encounter counts now derived from `trial_bosses.json` when needed
  - Added Maw of Lorkhaj (zone ID 5) and Ossein Cage (zone ID 19)
- Created `test_sunspire.py` for single-trial testing

### Changed (2025-10-05)
- `ESOLogsAPIClient` now accepts rate limiting parameters in constructor
- `TrialScanner.close()` now properly awaits the async close method

### Fixed (2025-10-05)
- Fixed async/await handling in trial scanner cleanup
- Improved error handling for rate limit scenarios

### Added (Earlier)
- Initial project setup with README and .gitignore
- Requirements and design documentation (`docs/requirements_and_design.md`)
- Project plan with architecture and implementation phases (`docs/project_plan.md`)
- Open questions document for research items (`docs/open_questions.md`)
- TODO list with 12 major tasks for project completion
- CHANGELOG.md to track project changes
- API research documentation (`docs/api_research.md`)

### Research Completed
- ✅ ESO Logs API structure and authentication (OAuth 2.0 Client Credentials)
- ✅ Found and analyzed reference project (`top-builds`)
- ✅ Located subclass detection algorithm
- ✅ Identified `esologs-python` library for API access
- ✅ Documented 13 ESO trials to scan (found 12 in API, 1 missing)
- ✅ Mapped out GraphQL query structure for rankings and reports
- ✅ Confirmed 2H weapons count as 2 pieces
- ✅ Found working examples of gear/ability extraction
- ✅ **CRITICAL**: Ability bars available via API with `includeCombatantInfo=True`
- ✅ Resolved API-only constraint conflict
- Answered 12+ of 30+ open questions

### Implementation Complete (Phases 1-3)
- ✅ Created Python project structure (src/eso_build_o_rama/)
- ✅ Set up virtual environment with all dependencies
- ✅ Implemented working API client (`api_client.py`)
- ✅ Successfully tested API authentication
- ✅ Retrieved 18 zones including 12 trials from ESO Logs API
- ✅ Built comprehensive data models (`models.py`)
- ✅ Implemented subclass analyzer (`subclass_analyzer.py`)
- ✅ Created build analyzer (`build_analyzer.py`)
- ✅ Built data parser (`data_parser.py`)
- ✅ Implemented trial scanner (`trial_scanner.py`)
- ✅ Created static page generator (`page_generator.py`)
- ✅ Designed responsive HTML templates (base, build page, index)
- ✅ Main orchestration script (`main.py`)
- Created `requirements.txt` with all dependencies
- Created `data/trials.json` with trial zone IDs and encounter counts
- Comprehensive test suite with 7 passing tests

### Infrastructure
- Created private GitHub repository at https://github.com/brainsnorkel/eso-build-o-rama
- Initialized git repository with main branch
- API credentials configured in `.env`
- Virtual environment configured with Python 3.9.6

## [0.0.1] - 2025-10-05

### Added
- Initial commit with project structure
