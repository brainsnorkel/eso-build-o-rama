# Feature: Role-Specific Performance Metrics

**Branch:** `feature/role-specific-metrics`  
**Status:** Exploration/Proof of Concept  
**Date:** 2025-10-09

## Overview

This feature adds support for displaying role-appropriate performance metrics in build displays:
- **Healers**: Show HPS (Healing Per Second) instead of DPS
- **Tanks**: Still show DPS (could be extended to show tank-specific metrics like damage mitigation)
- **DPS**: Show DPS as before

## Changes Made

### 1. Data Layer (`src/eso_build_o_rama/data_parser.py`)
- Added healing data extraction from API responses
- Populated `healing` and `healing_percentage` fields in `PlayerBuild` model
- Falls back to using `overheal` data if direct healing metrics unavailable

### 2. Model Layer (`src/eso_build_o_rama/models.py`)
- Added `get_primary_metric()` method to `PlayerBuild` class
  - Returns HPS for healers, DPS for others
- Added `get_primary_metric_name()` method to `PlayerBuild` class
  - Returns "HPS" for healers, "DPS" for others

### 3. Presentation Layer (`src/eso_build_o_rama/page_generator.py`)
- Added `format_metric` Jinja2 filter
- Formats both DPS and HPS values consistently (e.g., "125.4K", "2.3M")

### 4. Templates
Updated all templates to use role-specific metrics:
- **`templates/build_page.html`**:
  - Model Player info box: Shows appropriate metric
  - Other Example Players table: Shows appropriate metric with dynamic column header
- **`templates/trial.html`**:
  - Changed "DPS" column to "Performance" column
  - Shows appropriate metric based on player role
- **`templates/home.html`**:
  - Changed "Highest DPS Build" to "Top Performing Build"
  - Shows appropriate metric for top build

## Benefits

1. **More Meaningful Metrics**: Healers are now evaluated by their healing output, not damage
2. **Better Role Representation**: Each role shows the metric most relevant to their performance
3. **Clearer Comparisons**: When comparing builds, you see the metric that matters for that role
4. **Extensible Design**: Easy to add tank-specific metrics (damage taken, mitigation, etc.) in the future

## Known Limitations

1. **Healing Data Availability**: 
   - Healing data may not always be available in API responses
   - Falls back to DPS if healing data is missing
   - May need separate API call to get healing table data

2. **Tank Metrics Not Implemented**:
   - Tanks still show DPS
   - Could be extended to show:
     - Damage taken
     - Damage mitigated
     - Block uptime
     - Taunt uptime

3. **Sorting Considerations**:
   - Currently still sorts by DPS for "best player" selection
   - May need to sort by primary metric instead for healers

## Testing Recommendations

1. **Generate builds for a trial with healers**:
   ```bash
   python3 -m src.eso_build_o_rama.main --trial-id <trial_with_healers>
   ```

2. **Verify healer builds show HPS**:
   - Check build pages for healer builds
   - Verify "Model Player" shows HPS
   - Verify "Other Example Players" table shows HPS

3. **Verify DPS builds still show DPS**:
   - Check that DPS builds are unaffected
   - Verify column headers are correct

4. **Check API data**:
   - Verify that healing data is being captured from API
   - Check if separate Healing table query is needed for more accurate data

## Future Enhancements

1. **Tank-Specific Metrics**:
   - Query for damage taken data
   - Calculate mitigation percentage
   - Show block/taunt uptime

2. **Enhanced Healer Metrics**:
   - Query dedicated Healing table for more accurate HPS
   - Show overheal percentage
   - Show healing breakdown by spell

3. **Sorting by Role Metric**:
   - Sort healers by HPS for "best player"
   - Sort tanks by survival metrics
   - Keep DPS sorted by DPS

4. **Role-Specific Build Comparison**:
   - Allow filtering by role
   - Compare healers to healers, tanks to tanks
   - Show role-specific rankings

## Deployment Considerations

### Before Merging to Main:

1. ✅ Test with real trial data containing healers
2. ✅ Verify API provides healing data
3. ✅ Run deployment check: `./scripts/pre-merge-check.sh output-dev`
4. ✅ Ensure all builds display correctly
5. ✅ Check that pages generate without errors
6. ✅ Verify mobile responsiveness (metrics still fit on small screens)

### API Considerations:

- The current implementation uses data from the main DamageDone table
- For more accurate healing metrics, may need to query the Healing table separately
- This would require additional API calls (consider rate limiting)

## Files Changed

- `src/eso_build_o_rama/data_parser.py` - Healing data extraction
- `src/eso_build_o_rama/models.py` - Primary metric methods
- `src/eso_build_o_rama/page_generator.py` - Format metric filter
- `templates/build_page.html` - Role-specific metrics display
- `templates/trial.html` - Performance column update
- `templates/home.html` - Top build metric update
- `CHANGELOG.md` - Feature documentation

## How to Test

```bash
# Switch to feature branch
git checkout feature/role-specific-metrics

# Generate builds for a trial (example: Dreadsail Reef has healers)
python3 -m src.eso_build_o_rama.main --trial-id 60

# Serve locally
cd output-dev && python3 -m http.server 8080

# Visit http://localhost:8080 and check:
# - Home page shows role-appropriate metrics
# - Trial pages show "Performance" column with HPS for healers
# - Build pages show HPS for healer builds
# - DPS builds still show DPS
```

## Notes

- This is an exploratory feature branch to evaluate the feasibility and impact of role-specific metrics
- Feedback needed on whether HPS data is consistently available from the API
- May need to adjust data extraction strategy based on API response structure

