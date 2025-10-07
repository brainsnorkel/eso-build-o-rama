# Fight Rankings Experiment - Complete Summary

Branch: `experiment-report-rankings`

## What We Built

A completely new approach to discovering common builds from ESO Logs using **fightRankings** instead of **characterRankings**.

## The Key Insight

**Final boss rankings represent FULL trial runs** - those reports contain fights for ALL intermediate bosses too!

## New Architecture

### Before (characterRankings approach)
```
For each boss:
  Get top 10 character DPS rankings
  Extract report codes
  Process that specific fight
```

**Problems:**
- Many report codes were null
- Had to query each boss separately
- Fetched same reports multiple times

### After (fightRankings approach)
```
1. Get top 12 reports from FINAL BOSS using fightRankings (speed metric)
2. For each report, extract fights for ALL bosses
3. For each boss, find the shortest/fastest attempt
4. Analyze ALL players from those fights
5. Aggregate to find common builds
```

**Benefits:**
- ✅ Get builds for ALL bosses from same elite reports
- ✅ Much more efficient (1 API call vs 4+ per trial)
- ✅ Consistent data (same top groups across all bosses)
- ✅ Analyzes entire groups, not just top DPS individuals
- ✅ Deduplicates reports automatically

## Technical Discoveries

### API Research

1. **`reportRankings`** - Doesn't exist in ESO Logs API
2. **`fightRankings`** - EXISTS! Returns report-level rankings
   - Uses `speed` metric (not `dps` or `playerscore`)
   - Returns ~32 unique reports per boss
   - Includes full report metadata (guild, composition, score)

3. **`characterRankings`** - Works but different use case
   - Uses `dps` metric with `leaderboard: LogsOnly`
   - Returns ~64 unique reports
   - Focused on individual player performance

### Fight Validation

Discovered that ESO Logs fight data:
- `kill: false` for most boss attempts (unreliable)
- `difficulty: 121/122` indicates boss fights (reliable!)
- Must match by `name` AND presence of `difficulty`

## Implementation Details

### 1. Modified `api_client.py`

`get_top_logs()` now uses fightRankings:

```graphql
query GetTopRankedReports($encounterID: Int!) {
  worldData {
    encounter(id: $encounterID) {
      fightRankings(
        metric: speed
      )
    }
  }
}
```

Returns report metadata including:
- code, fightID
- duration, score
- guild info
- group composition (tanks/healers/melee/ranged)

### 2. Optimized `trial_scanner.py`

**Key methods:**

```python
# Find shortest fight for a boss in a report
_find_best_fight_for_encounter(report_data, encounter_name)

# Process a single fight from already-fetched report
_process_single_fight(report_data, report_code, fight_id, trial_name, encounter_name)

# Main scanning logic in scan_all_trials()
1. Get top 12 reports from final boss only
2. Fetch each report once
3. Extract all relevant boss fights
4. Process shortest attempt for each boss
```

**Deduplication:**
- Collects reports across all encounters
- Deduplicates before fetching
- Fetches each unique report only once

### 3. Output Directory Logic

Changed to:
- `main` branch → `output/` (production)
- All other branches → `output-dev/` (development)

## Results

### Sanctum Ophidia Test

**12 top reports** from The Serpent (final boss)

**Per report, processed:**
- Possessed Mantikora (1-3 attempts each, chose fastest)
- Stonebreaker (1-2 attempts, chose fastest)  
- Ozara (1 attempt typically)
- The Serpent (1-3 attempts, chose fastest)

**Total:**
- 12 reports × 4 bosses = 48 boss fights processed
- 48 fights × 12 players = 576 player builds analyzed
- Output: 2 publishable builds (met 5+ player threshold)

## Query Testing Utility

Created `utils/query_tester.py`:
- Test different query types
- Compare metrics and leaderboards
- See report codes and URLs
- Count unique reports
- Inspect full report contents

**Usage:**
```bash
python3 utils/query_tester.py [encounter_id]
```

## Efficiency Gains

**Example: Aetherian Archive (4 bosses)**

**Old approach:**
- 4 bosses × 10 rankings queries = 40 API calls
- Same reports fetched multiple times

**New approach:**
- 1 rankings query (final boss only)
- 12 unique reports fetched once each
- **~70% fewer API calls**

## Files Created/Modified

### New Files
- `utils/query_tester.py` - Query testing utility
- `utils/README.md` - Utility documentation
- `utils/QUERY_EXAMPLES.md` - Query reference guide
- `docs/fight_rankings_experiment.md` - This document

### Modified Files
- `src/eso_build_o_rama/api_client.py` - New fightRankings query
- `src/eso_build_o_rama/trial_scanner.py` - Complete refactor for report-based approach
- `src/eso_build_o_rama/main.py` - Output directory logic + 12 report limit

## Commits on Branch

```
eee6571 Fix fight matching to use difficulty field instead of kill flag
811d346 Extract ALL boss fights from final boss rankings (major improvement)
c75bd0a Increase report limit from 10 to 12
0253951 Optimize report fetching - deduplicate and process once per report
96a44ad Add fight validation to ensure we only process correct encounters
3bf9e10 Switch to fightRankings approach for top reports
02570ce Add query testing utility for experimenting with leaderboard queries
b20bae4 Revert to original working query (characterRankings with dps)
71811d5 Switch to fightRankings based on API error suggestion
bd53ebe Change output directory logic: only main branch uses output/
3ef3b48 Experiment: Switch from characterRankings to reportRankings with playerscore metric
```

## Next Steps

### Option 1: Merge to develop
The new approach works and is more efficient. Consider merging after:
- Testing with more trials
- Verifying all bosses generate properly
- Comparing build quality with old approach

### Option 2: More Experimentation
- Test with different metrics
- Try hybrid approach (fightRankings + characterRankings)
- Adjust thresholds for publishable builds
- Test with all 14 trials

### Option 3: Keep Both Approaches
- Use fightRankings for trials (whole team analysis)
- Use characterRankings for individual player focus
- Let users toggle between views

## Conclusion

The experiment was successful! We discovered:

1. ✅ fightRankings provides better report coverage
2. ✅ Extracting all bosses from final boss reports is highly efficient
3. ✅ Finding shortest attempts gives best performance data
4. ✅ Analyzing full groups reveals common team compositions
5. ✅ Query testing utility makes future experiments easy

The new architecture is cleaner, more efficient, and provides comprehensive build data across all bosses from elite groups.
