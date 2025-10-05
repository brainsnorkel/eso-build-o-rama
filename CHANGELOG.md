# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
