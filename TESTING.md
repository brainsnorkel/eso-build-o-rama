# Testing Guide for ESO Build-O-Rama

This guide explains how to test the staggered trial scanning system, social media previews, and verify that incremental updates work correctly.

## Test Setup

### Prerequisites
1. ESO Logs API credentials configured in `.env` file
2. Python virtual environment activated
3. Dependencies installed: `pip install -r requirements.txt`
4. Pillow installed for social media preview generation

### Environment Variables
Make sure these are set in your `.env` file:
```
ESOLOGS_ID=your_client_id
ESOLOGS_SECRET=your_client_secret
```

## Social Media Preview Testing

### Generate Preview Images
```bash
# Generate production previews
python generate_social_previews.py

# Generate development previews  
python generate_social_previews.py --dev

# Test preview generation
python test_social_previews.py
```

### Test Social Media Links
1. **Facebook/Meta**: Use [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/)
2. **Twitter/X**: Use [Twitter Card Validator](https://cards-dev.twitter.com/validator)
3. **LinkedIn**: Use [LinkedIn Post Inspector](https://www.linkedin.com/post-inspector/)
4. **Discord**: Share a link in Discord to see the preview

### Verify Meta Tags
Check that pages include proper Open Graph and Twitter Card meta tags:
- `og:title`, `og:description`, `og:image`
- `twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`

## Test Cases

### 1. Single Trial Scan Test

Test scanning a single trial to verify CLI arguments work:

```bash
# Test Sunspire (ID 12)
python -m src.eso_build_o_rama.main --trial-id 12

# Test by name
python -m src.eso_build_o_rama.main --trial "Sunspire"

# Test mode (first trial only)
python -m src.eso_build_o_rama.main --test
```

**Expected Results**:
- ✅ Only specified trial is scanned
- ✅ `output/builds.json` is created with trial data
- ✅ Index page shows only the scanned trial with timestamp
- ✅ Individual build pages are generated for the trial

### 2. Incremental Update Test

Test that multiple trials can be scanned and data persists:

```bash
# Scan first trial
python -m src.eso_build_o_rama.main --trial-id 1

# Verify builds.json contains AA data
cat output/builds.json

# Scan second trial
python -m src.eso_build_o_rama.main --trial-id 12

# Verify builds.json contains both AA and Sunspire data
cat output/builds.json
```

**Expected Results**:
- ✅ First trial data persists after second scan
- ✅ Second trial data is added without overwriting first
- ✅ Index page shows both trials with different timestamps
- ✅ Each trial shows correct "Last updated" time

### 3. Data Persistence Test

Test that data survives between runs:

```bash
# Scan a trial
python -m src.eso_build_o_rama.main --trial-id 8

# Check builds.json exists and has data
ls -la output/builds.json
cat output/builds.json | jq '.trials | keys'

# Run again with different trial
python -m src.eso_build_o_rama.main --trial-id 19

# Verify both trials are in builds.json
cat output/builds.json | jq '.trials | keys'
```

**Expected Results**:
- ✅ `output/builds.json` file persists between runs
- ✅ Previous trial data is preserved
- ✅ New trial data is added incrementally
- ✅ Each trial has correct timestamp metadata

### 4. Full Scan Test

Test scanning all trials at once:

```bash
# Full scan (no arguments)
python -m src.eso_build_o_rama.main
```

**Expected Results**:
- ✅ All 14 trials are scanned
- ✅ `output/builds.json` contains all trial data
- ✅ Index page shows all trials with timestamps
- ✅ All individual build pages are generated

### 5. GitHub Actions Workflow Test

Test the automated workflow manually:

1. Go to GitHub repository Actions tab
2. Click "Generate ESO Builds (Staggered)" workflow
3. Click "Run workflow"
4. Select a trial ID (e.g., 12 for Sunspire)
5. Click "Run workflow"

**Expected Results**:
- ✅ Workflow runs successfully
- ✅ Trial is scanned and data saved
- ✅ GitHub Pages is updated with new data
- ✅ Index page shows updated timestamp for the trial

### 6. Auto-Detection Test

Test the auto-detection logic by manually triggering at different hours:

```bash
# Simulate different hours by setting environment variable
HOUR=8 python -m src.eso_build_o_rama.main --trial-id 12  # Should work
HOUR=15 python -m src.eso_build_o_rama.main --trial-id 12  # Should default to AA
```

**Expected Results**:
- ✅ Auto-detection logic works correctly
- ✅ Unknown hours default to AA (trial ID 1)
- ✅ Manual trial-id overrides auto-detection

## Verification Commands

### Check Data Structure
```bash
# View builds.json structure
cat output/builds.json | jq '.'

# Check trial count
cat output/builds.json | jq '.trials | length'

# Check specific trial data
cat output/builds.json | jq '.trials["Sunspire"]'

# Check last updated times
cat output/builds.json | jq '.trials | to_entries | map({trial: .key, last_updated: .value.last_updated})'
```

### Check Generated Files
```bash
# List all generated HTML files
ls -la output/*.html

# Check index page for timestamps
grep -i "last updated" output/index.html

# Count build pages
ls output/*.html | grep -v index.html | wc -l
```

### Check API Rate Limiting
```bash
# Monitor API calls (should see delays between requests)
python -m src.eso_build_o_rama.main --trial-id 12 2>&1 | grep -i "delay\|retry\|rate"
```

## Troubleshooting

### Common Issues

1. **"Trial with ID X not found"**
   - Check trial ID in `data/trials.json`
   - Verify trial exists in ESO Logs API

2. **"No reports found"**
   - Check API credentials in `.env`
   - Verify trial has recent logs in ESO Logs
   - Check rate limiting - may need to wait

3. **"Error saving builds file"**
   - Check write permissions in `output/` directory
   - Ensure `output/` directory exists

4. **Template errors**
   - Verify Jinja2 templates are in `templates/` directory
   - Check template syntax for timestamp filters

### Debug Mode

Enable debug logging for detailed output:

```bash
# Set logging level to DEBUG
export PYTHONPATH=.
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from src.eso_build_o_rama.main import main
asyncio.run(main())
" --trial-id 12
```

## Performance Expectations

### Single Trial Scan
- **Duration**: 2-5 minutes (depending on trial popularity)
- **API Calls**: ~20-40 requests
- **Rate Limit Usage**: ~200-400 points
- **Output**: 1-5 build pages + updated index

### Full Scan
- **Duration**: 30-60 minutes (with rate limiting)
- **API Calls**: ~300-600 requests
- **Rate Limit Usage**: ~3000-6000 points
- **Output**: 20-100 build pages + updated index

### GitHub Actions
- **Duration**: 5-10 minutes per trial
- **Frequency**: 14 times per week (once per trial)
- **Schedule**: Sunday 1am-2pm UTC (1 hour intervals)

## Success Criteria

A successful test should verify:
- ✅ Single trial scanning works with CLI arguments
- ✅ Data persists between runs in `output/builds.json`
- ✅ Multiple trials can be scanned incrementally
- ✅ Index page shows timestamps for each trial
- ✅ GitHub Actions workflow can run manually
- ✅ Auto-detection logic works for different hours
- ✅ No API rate limit violations
- ✅ All generated HTML files are valid
