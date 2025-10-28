# ESO Logs API Metric Investigation Results

## Test Date: 2025-10-28

## Summary

Tested all available fightRankings metrics on Lucent Citadel to determine if any metric returns usable leaderboard data.

## Valid Metrics in ESO Logs API

✅ **Working Metrics**:
- `speed` - Speed/time-based rankings
- `execution` - Execution score rankings  
- `feats` - Achievement/feat-based rankings
- `progress` - Progress-based rankings
- `default` - Default leaderboard (in-game leaderboard data)
- `score` - Score-based rankings

❌ **Invalid Metrics** (not in FightRankingMetricType enum):
- `points`, `dps`, `hps`, `rdps`, `ndps`, `playerscore`

## Lucent Citadel Test Results

### Encounter: Xoryn (Final Boss, ID: 60)

| Metric      | Rankings Found | Report Codes | Usable? |
|-------------|----------------|--------------|---------|
| `speed`     | 0              | N/A          | ❌ No   |
| `execution` | 0              | N/A          | ❌ No   |
| `feats`     | 0              | N/A          | ❌ No   |
| `progress`  | 0              | N/A          | ❌ No   |
| `default`   | 2              | Empty ("")   | ❌ No   |
| `score`     | 2              | Empty ("")   | ❌ No   |

### Key Finding: In-Game Leaderboard vs ESO Logs

The `default` and `score` metrics returned **2 rankings** with this data:

**Ranking 1** (NA):
- Guild: "Knot Again"
- Duration: 1,670,618ms (27.8 minutes)
- Score: 251,304
- Composition: 2 tanks, 2 healers, 8 melee
- **Report Code: EMPTY ("")**

**Ranking 2** (EU):
- Guild: "Capybara Squadron"  
- Duration: 1,928,385ms (32.1 minutes)
- Score: 222,810
- Composition: 2 tanks, 2 healers, 8 melee
- **Report Code: EMPTY ("")**

### Analysis

The `default` and `score` metrics pull from **ESO's in-game leaderboards**, not ESO Logs uploads. This data shows:

1. ✅ **In-game runs exist**: Guilds have completed Lucent Citadel and appear on leaderboards
2. ❌ **No ESO Logs reports**: The `report.code` field is empty (no logs uploaded)
3. ❌ **Unusable for build analysis**: Without report codes, cannot fetch combat logs

### Why Report Codes Are Empty

- **In-game leaderboard** tracks runs automatically (no logging required)
- **ESO Logs leaderboard** requires players to upload combat logs manually
- These guilds cleared the content but didn't upload logs to ESO Logs

## Comparison: Trial with Data vs Lucent Citadel

### Dreadsail Reef - Tideborn Taleria (Has Data)

| Metric    | Rankings | Has Report Codes? |
|-----------|----------|-------------------|
| `speed`   | 2        | ✅ Yes            |
| `default` | 2        | ✅ Yes            |
| `score`   | 2        | ✅ Yes            |

### Lucent Citadel - Xoryn (No Usable Data)

| Metric    | Rankings | Has Report Codes? |
|-----------|----------|-------------------|
| `speed`   | 0        | N/A               |
| `default` | 2        | ❌ Empty          |
| `score`   | 2        | ❌ Empty          |

## Conclusion

**Lucent Citadel has NO usable leaderboard data in ESO Logs** regardless of metric used:

1. `speed`, `execution`, `feats`, `progress` → **0 rankings**
2. `default`, `score` → **2 rankings but no report codes**

### Why This Matters

The application requires **report codes** to:
- Fetch full combat log data via `reportData.report(code: "ABC123")`
- Extract player builds, gear, abilities, performance
- Generate build pages

Without report codes, we cannot access the underlying data needed for build analysis.

### Current Implementation is Correct

The application uses `metric: speed` which is appropriate because:
- ✅ It's the standard metric for speed-based rankings
- ✅ It filters to only uploaded logs (has report codes)
- ✅ Other metrics don't provide additional usable data

Using `default` or `score` would give false positives - showing "data available" when we actually cannot access the combat logs.

## Recommendation

**No changes needed.** Continue using `metric: speed` and correctly show "No leaderboard data (yet)" for Lucent Citadel.

Once players upload combat logs to ESO Logs, they will appear in the `speed` metric rankings and the system will automatically pick them up.
