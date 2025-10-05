# Testing Guide

## Overview

This guide covers testing the ESO Build-O-Rama system from end to end.

## Prerequisites

- Python 3.9+ installed
- Virtual environment activated
- API credentials configured in `.env`
- All dependencies installed (`pip install -r requirements.txt`)

## Test Components

### 1. Unit Tests

Run the existing test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_build_analysis.py -v

# Run with coverage
pytest tests/ --cov=src/eso_build_o_rama --cov-report=html
```

**Expected Results:**
- All 7 tests should pass
- API authentication successful
- Zone retrieval working
- Build analysis functional

### 2. API Client Test

Test the API client independently:

```bash
source venv/bin/activate
python tests/test_api_client.py
```

**Expected Output:**
```
Testing ESO Logs API client...
✅ API authentication successful
✅ Found 18 zones
✅ Identified 12 trial zones with encounter counts
```

### 3. Build Analysis Test

Test build analysis components:

```bash
source venv/bin/activate
python tests/test_build_analysis.py
```

**Expected Output:**
```
Testing build analysis...
Abilities: ["Assassin's Blade", 'Shadow Cloak', 'Siphoning Strikes']
Detected subclasses: ['Ass', 'Shadow', 'Siphon']
Player subclasses: ['Ass', 'Shadow', 'x']
Build slug: ass-shadow-x-unknown-unknown
✅ Build analysis tests complete!
```

### 4. End-to-End Test (Test Mode)

Run the main application in test mode (processes only first trial):

```bash
source venv/bin/activate
cd src
python -m eso_build_o_rama.main
```

**What This Tests:**
1. Loading trial data from `data/trials.json`
2. API authentication and connection
3. Fetching top 5 logs for a trial
4. Processing report data
5. Extracting player builds
6. Analyzing subclasses and gear
7. Identifying common builds
8. Generating HTML pages

**Expected Behavior:**
- Logs showing scan progress
- Successful API calls
- Player builds extracted
- Common builds identified (if any)
- HTML files generated in `output/` directory

**Potential Issues:**
- **No common builds found**: Normal for test mode with only 1 trial
- **API rate limits**: Wait if hit rate limits
- **Missing data**: Some reports may lack complete build info

### 5. HTML Output Validation

After running the main script, check generated files:

```bash
# List generated files
ls -lh output/

# Open in browser (macOS)
open output/index.html

# Open in browser (Linux)
xdg-open output/index.html
```

**Validate:**
- [ ] `index.html` exists and opens
- [ ] Build pages exist (if common builds found)
- [ ] Styling renders correctly
- [ ] Tables display properly
- [ ] Links work
- [ ] Mobile responsive

### 6. Full System Test

Run without test mode to process all trials:

```bash
source venv/bin/activate
cd src

# Edit main.py to set test_mode=False
# Then run:
python -m eso_build_o_rama.main
```

**Warning:** This will:
- Make many API calls (watch rate limits)
- Take several minutes to complete
- Process all 12 trials
- Generate many HTML pages

## Manual Testing Checklist

### API Integration
- [ ] API authentication successful
- [ ] Can fetch zone list
- [ ] Can fetch report by code
- [ ] Can get table data with `includeCombatantInfo=True`
- [ ] Handles API errors gracefully

### Data Parsing
- [ ] Player names extracted correctly
- [ ] Gear pieces parsed with sets/traits
- [ ] Abilities extracted from both bars
- [ ] Buffs parsed (Mundus, CP)
- [ ] Performance data (DPS) captured

### Build Analysis
- [ ] Subclasses detected from abilities
- [ ] Build slugs generated correctly
- [ ] 2H weapons counted as 2 pieces
- [ ] Common builds identified (5+ threshold)
- [ ] Highest DPS player selected per build

### Page Generation
- [ ] Index page generated
- [ ] Build pages generated for each common build
- [ ] Templates render without errors
- [ ] Styling loads correctly
- [ ] Data displays accurately
- [ ] Links functional
- [ ] Credits section present

## Debugging

### Enable Debug Logging

Edit the logging level in `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Common Issues

**1. API Authentication Fails**
```
Solution: Check .env file has correct credentials
- ESOLOGS_ID=your-id
- ESOLOGS_SECRET=your-secret
```

**2. No Builds Found**
```
Possible causes:
- Top logs don't have 5+ players with same build
- Incomplete data in reports
- Too few reports analyzed

Solution: Run with more trials or lower threshold
```

**3. Template Not Found**
```
Error: jinja2.exceptions.TemplateNotFound: 'build_page.html'

Solution: Ensure templates/ directory exists in working directory
or update template_dir parameter in PageGenerator
```

**4. Module Import Errors**
```
Error: ModuleNotFoundError: No module named 'src'

Solution: 
- Make sure virtual environment is activated
- Run from project root: python -m src.eso_build_o_rama.main
```

## Performance Testing

### Measure Execution Time

```bash
time python -m eso_build_o_rama.main
```

**Expected Times:**
- Test mode (1 trial): 10-30 seconds
- Full run (12 trials): 2-5 minutes

### Memory Usage

```bash
# Install memory-profiler
pip install memory-profiler

# Run with profiling
python -m memory_profiler -m eso_build_o_rama.main
```

## Test Data

### Sample Report Codes

For manual testing with specific reports:

```python
# Edit trial_scanner.py to use specific report codes
test_reports = [
    {'code': 'ABC123', 'fightID': 1},  # Replace with real codes
]
```

### Mock Data Testing

Create mock data for testing without API:

```python
# In tests/test_integration.py
def test_with_mock_data():
    # Create mock PlayerBuild objects
    # Test build analysis
    # Validate HTML generation
```

## Continuous Integration

Future: GitHub Actions workflow

```yaml
# .github/workflows/test.yml
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/
```

## Next Steps

After successful testing:

1. **Review output HTML** - Check for data accuracy
2. **Test with more trials** - Increase coverage
3. **Refine thresholds** - Adjust "common build" criteria
4. **Add more tests** - Edge cases, error conditions
5. **Deploy** - Set up GitHub Actions + Pages
