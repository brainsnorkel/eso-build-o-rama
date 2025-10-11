# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed (2025-10-11 - Build Requirements and About Page)
- **Build Requirements**: Changed minimum build requirements for healers and tanks from 2 to 3 occurrences
- **About Page**: Added comprehensive about page with site banner background image
- **Navigation**: Added About link to top right of site header
- **Home Page**: Removed "About This Data" section from home page (replaced with dedicated About page)
- **Documentation**: Updated home page text and design documentation to reflect new build requirements

### Fixed (2025-10-11 - Trial Box Layout Consistency)
- **Trial Box Heights**: Fixed inconsistent trial box heights on home page for uniform grid layout
  - Changed from `min-height: 240px` to fixed `height: 320px` for all trial boxes
  - Added `justify-content: space-between` for better content distribution
  - Restructured content layout with flexbox for consistent spacing
  - Ensures all trial boxes have the same height regardless of content length
  - Creates clean, professional grid appearance across all trial cards

### Removed (2025-10-11 - Caching System)
- **Caching System**: Completely removed the caching system to simplify the codebase and ensure fresh data on every run
  - Deleted `cache_manager.py` module
  - Removed all cache-related parameters from `ESOLogsAPIClient`, `TrialScanner`, and `ESOBuildORM`
  - Removed `--use-cache`, `--no-cache`, `--clear-cache`, and `--cache-stats` command-line arguments
  - Removed `cache/` directory and its .gitignore entries
  - Removed cache statistics from builds data structure
  - System now always fetches fresh data from ESO Logs API

### Added (2025-10-11 - About Page Features)
- **About Page Template**: Created `templates/about.html` with comprehensive site information
- **About Banner**: Processed `site_banner_characterload.png` for about page background (1920x1080px, 25% opacity)
- **Page Generation**: Integrated about page generation into `PageGenerator.generate_all_pages()`
- **Navigation Link**: Added styled About link in site header with hover effects

### Added (2025-10-11 - CSV Data Export)
- **CSV Exporter Module**: Created `csv_exporter.py` to export comprehensive player data for analysis
- **Download CSV Button**: Added styled download button to trial pages for accessing raw data
- **Player Data Export**: CSV includes all players from all scanned fights with:
  - Player identification (handle, character name, ESO Logs link)
  - Build information (slug, subclasses, signature sets)
  - Performance metrics (DPS, HPS, CPM, primary metric)
  - Complete gear slots with set names
  - Full ability bars (front and back)
  - Mundus stone information
- **Automated Generation**: CSV files are automatically generated during trial scanning
- **File Naming**: CSVs are named `{trial-slug}-data.csv` (e.g., `aetherian-archive-data.csv`)

### Technical Changes (2025-10-11)
- **Build Filtering**: Implemented role-specific build filtering in `BuildAnalyzer`:
  - DPS builds: minimum 5 occurrences
  - Healer/Tank builds: minimum 2 occurrences
- **Constants**: Added `MINIMUM_HEALER_TANK_BUILD_OCCURRENCES = 2` to `BuildAnalyzer`
- **Filtering Logic**: Enhanced `analyze_trial_report()` to filter builds based on role and count
- **Debug Logging**: Added detailed logging for build filtering decisions

### Fixed (2025-10-11)
- **Build Consolidation Threshold**: Fixed `CommonBuild.meets_threshold()` in `models.py` to use 2 occurrences for healers/tanks (was incorrectly still using 3), ensuring consistency with `BuildAnalyzer` filtering logic
- **Build Consolidation Logic**: **CRITICAL FIX** - Removed per-fight filtering from `BuildAnalyzer.analyze_trial_report()`. Previously, builds were filtered by minimum occurrence count (5 for DPS, 2 for healers/tanks) BEFORE consolidation across reports, which prevented builds from accumulating. Now ALL builds are passed to consolidation, and filtering only happens AFTER aggregating players across all reports. This resulted in finding 30 builds for Aetherian Archive vs only 1 build previously.
- **About Page Breadcrumb**: Added breadcrumb navigation link at top of about page to return to home
- **Missing Return Statements**: Fixed missing return statements in `api_client.py` methods (`get_top_logs`, `get_report`) that were accidentally removed during cache cleanup

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2025-10-10 - Trial Graphics and Site Banner)
- **Trial Background Images**: Added alpha-blended background images to trial boxes on home page
  - Processed 14 trial artwork images for optimal display
  - Created trial-specific backgrounds at 600px width with 35% opacity (increased for better visibility)
  - Images positioned as backgrounds with dark overlay (50% opacity) for text readability
  - Added `trial_background_image` Jinja2 filter for trial name to image mapping
  - Updated `home.html` template to include background images in trial cards
  - Trial images used for trial link boxes on home page AND trial page headers
- **Social Card Backgrounds**: Prepared 1200x630px social card backgrounds for each trial
  - Center-cropped and resized to social media dimensions
  - 30% opacity for visibility while maintaining branding
  - Ready for future social media preview integration
- **Site Banner**: Added character artwork as background for entire site
  - Processed `site_banner_characterload.png` to 120px height
  - Right-aligned crop to preserve character positioning
  - 35% opacity for better visibility (increased from 20%)
  - Applied as fixed background to body element across all pages
  - Used for header, build pages, trial pages, and home page
  - Creates consistent visual theme throughout the site
- **Image Processing Script**: Created `process_trial_art.py` for automated image optimization
  - Handles resizing, cropping, and alpha transparency adjustments
  - Generates three versions: trial backgrounds, social backgrounds, and site banner
  - Uses PIL/Pillow for high-quality image processing
  - Output organized in `static/trial-backgrounds/`, `static/social-backgrounds/`, and `static/banners/`
- **Trial Image Mapping**: Complete mapping of 14 trials to artwork filenames
  - Aetherian Archive, Hel Ra Citadel, Sanctum Ophidia
  - Maw of Lorkhaj, Halls of Fabrication, Asylum Sanctorium
  - Cloudrest, Sunspire, Kyne's Aegis
  - Rockgrove, Dreadsail Reef, Sanity's Edge
  - Lucent Citadel, Ossein Cage

### Changed (2025-10-09 - Site Subtitle Update)
- **Updated Site Subtitle**: Changed subtitle from "Common builds found in top esologs" to "The latest ESO meta trial builds from ESOLogs. Updated every day."
  - Updated in base.html header (line 796)
  - Updated in meta description tag (line 6)
  - Updated in Open Graph description (line 12)
  - Updated in Twitter Card description (line 25)
  - More accurate description of site functionality and update frequency
  - Better SEO with clear messaging about content freshness

### Added (2025-10-09 - Role-Specific Performance Metrics)
- **Feature: HPS Display for Healers**
  - **Overview**: Healers now show HPS (Healing Per Second) instead of DPS in build displays
  - **Implementation Details**:
    - Added `healing` and `healing_percentage` fields to `PlayerBuild` model (already existed but weren't populated)
    - Updated `data_parser.py` to extract healing data from API responses for healer roles
    - **HPS calculation includes both effective healing AND overheal** for complete healing output
    - Added `get_primary_metric()` and `get_primary_metric_name()` methods to `PlayerBuild` class
    - Created `format_metric` Jinja2 filter for formatting both DPS and HPS values
    - Updated all templates to show role-appropriate metrics:
      - `build_page.html`: Model Player and Other Example Players sections
      - `trial.html`: Performance column shows DPS/HPS based on role
      - `home.html`: Top build displays show appropriate metric
  - **Display Changes**:
    - Healers: Shows "X.XK HPS" or "X.XM HPS" (total healing output including overheal)
    - Tanks: Will show "X.X CPM" (casts per minute) when implemented, currently shows DPS
    - DPS: Shows "X.XK DPS" or "X.XM DPS" as before
  - **Benefits**:
    - More meaningful metrics for non-DPS roles
    - Better representation of healer performance
    - Clearer role distinction in build comparisons
  - **Known Limitations**:
    - Healing data may not be available in all API responses
    - Falls back to DPS if healing data is unavailable
    - Tank CPM (casts per minute) not yet implemented - requires Casts table integration
  - **Branch**: `feature/role-specific-metrics`

### Fixed (2025-10-09 - Mundus Stone Display Fix)
- **Issue #2: Mundus collected but not showing**
  - **Root Cause**: When pages were generated, freshly scanned builds (with mundus data) were saved to builds.json, but then ALL builds were reloaded from disk (including old trials without mundus). This caused newly scanned trials to show empty mundus fields.
  - **Solution**: Implemented build merging logic that replaces loaded builds with fresh builds where available, ensuring mundus data from new scans persists through the page generation process.
  - **Impact**: Mundus stones now display correctly on all newly scanned trial builds.
  - **Note**: Old trials in builds.json may still have empty mundus until they are re-scanned by the 14-hour update cycle.

### Changed (2025-10-08 - GitHub Actions Schedule Update)
- **Reduced Deployment Frequency**: Changed from 7-hour to 14-hour update cycle
  - Updated cron schedule from every 30 minutes to every hour
  - Changed trial determination logic from minutes to hours since reference
  - Each trial now updates every 14 hours instead of every 7 hours
  - Reference time: 20:00 UTC (8:00 PM UTC) for Aetherian Archive
  - Reduces GitHub Actions usage and API load
  - Updated README.md with new schedule timings

### Added (2025-10-08 - ESO-Hub Tooltip Integration)
- **Interactive Gear Tooltips**: Integrated ESO-Hub's tooltip system for rich hover information
  - Added ESO-Hub external CSS and JavaScript to all pages
  - Created Jinja2 filter functions for ESO-Hub URL generation
  - Made all gear set names clickable with ESO-Hub links
  - Made mundus stone names clickable with tooltip support
  - Added tooltips to gear table set names
  - Added tooltips to "Sets Used" summary boxes
  - Added tooltips to signature sets in trial page tables
  - Automatic tooltip display on hover (no user configuration needed)
  - URL slugification handles "Perfected" prefix removal
  - Links open ESO-Hub pages in new tabs for detailed information
  - Zero-maintenance solution (ESO-Hub maintains the data)
  - Improves user experience with instant access to set bonuses

### Added (2025-10-08 - SEO Improvements)
- **Comprehensive SEO Implementation**: Major improvements for search engine discoverability
  - Added automatic sitemap.xml generation with all pages (home, trials, builds)
  - Added robots.txt generation with crawler directives and sitemap reference
  - Implemented Schema.org JSON-LD structured data on all pages:
    - WebSite schema on home page with Elder Scrolls Online context
    - BreadcrumbList schema on all pages for navigation hierarchy
    - HowTo schema on build pages with gear supplies and ability steps
  - Added canonical URLs to all pages to prevent duplicate content issues
  - Enhanced meta descriptions with keyword-rich, role-specific content
  - Added keywords meta tag with relevant ESO search terms
  - Improved page titles with role and location context
  - Updated all templates (base.html, home.html, trial.html, build_page.html) with SEO blocks
  - Added SEO validation section to TESTING.md with validation tools and procedures
  - Documented SEO features in README.md with submission instructions
- **Home Page Cleanup**: Removed cache effectiveness statistics from trial boxes for cleaner UI

### Changed (2025-10-08 - Cache Organization & Performance Monitoring)
- **Improved Cache Organization**: Reorganized cache directory structure for better maintainability
  - Created subdirectories for different cache types: `buffs/`, `tables/`, `rankings/`, `reports/`
  - Fixed cache key prefix mismatch: `fight_rankings_` → `rankings_` for proper subdirectory routing
  - Buffs queries now stored in `cache/buffs/` (previously root) - 1,224 files
  - Table queries now stored in `cache/tables/` (previously root) - 310 files
  - Rankings now properly stored in `cache/rankings/` subdirectory - 4 files
  - Reports remain in `cache/reports/` subdirectory - 45 files
  - Added migration utility script: `utils/migrate_cache.py` (supports dry-run mode)
- **Enhanced Cache Performance Monitoring**: Added comprehensive cache hit/miss tracking
  - Cache manager now tracks hits and misses during runtime
  - Added `log_cache_performance()` method to display statistics at end of run
  - Enhanced `--cache-stats` command to show detailed breakdown by cache type
  - Added hit rate calculation and display in cache statistics
  - Shows cache effectiveness metrics: total requests, hits, misses, hit rate percentage
- **Benefits**: 
  - Easier cache management and debugging
  - Better visibility into cache effectiveness
  - Cleaner directory structure with 46+ MB cache properly organized
  - Cache effectiveness score: 95% (all API methods properly cached)

### Changed (2025-10-08 - Optimized Mundus Queries)
- **Optimized Mundus Stone API Queries**: Reduced mundus API calls by 80-90% for improved performance
  - Problem: Mundus stones were queried for EVERY build during fight processing (100s of queries)
  - Solution: Moved mundus queries to happen AFTER build consolidation and threshold filtering
  - Now only queries mundus for publishable builds that meet role-based thresholds (5+ for DPS, 3+ for healer/tank)
  - Added fight context fields to CommonBuild model (report_code, fight_start_time, fight_end_time)
  - Created dedicated `fetch_mundus_for_builds()` method with deduplication logic
  - Example: For Sunspire scan, reduced from ~100+ queries to 18 optimized queries
  - Benefits: Faster processing, fewer network round-trips, better cache utilization
  - Quality: Same accurate per-player mundus data, just fetched more efficiently

### Changed (2025-10-07 - Site Title Rebranding)
- **Site Title Update**: Changed site name from "ESO Build-o-rama" to "ESOBuild.com"
  - Updated all template meta tags (Open Graph, Twitter Card)
  - Updated page titles and headers in base.html and home.html
  - Updated social preview generator class docstrings
  - Updated README.md main title
  - Consistent branding across all pages and documentation

### Added (2025-10-07 - Screen Reader Accessibility)
- **WCAG 2.1 Level AA Compliance**: Comprehensive accessibility improvements for screen reader users
  - Added skip-to-main-content link for keyboard navigation
  - Added ARIA landmarks (banner, main, contentinfo) to all templates
  - Added `.sr-only` utility class for screen-reader-only content
  - Added enhanced focus indicators (3px solid outline with 2px offset) for keyboard navigation
  - Added table captions to all data tables (visually hidden but accessible)
  - Added `scope="col"` attributes to all table headers
  - Added screen reader text for role indicators (DPS, Healer, Tank) alongside visual emojis
  - Added `aria-label` attributes to navigation links for better context
  - Added semantic breadcrumb navigation with proper ARIA structure
  - Added meaningful alt text to ability icons including skill line information
  - Added `rel="noopener noreferrer"` to all external links for security
  - Created comprehensive `docs/accessibility.md` with testing results and known limitations
  - Improved link text with descriptive aria-labels for "View Build" links
  - Implemented proper heading hierarchy throughout all pages
  - Used `aria-hidden="true"` for decorative elements and visual separators

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
