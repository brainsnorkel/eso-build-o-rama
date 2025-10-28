# fightRankings vs characterRankings Comparison

## 🎯 Key Discovery

**characterRankings returns SIGNIFICANTLY MORE DATA than fightRankings!**

For Lucent Citadel:
- ❌ `fightRankings`: **0 results**
- ✅ `characterRankings`: **36 results** with report codes!

## Test Results Summary

| Trial                  | fightRankings | characterRankings | Difference |
|------------------------|---------------|-------------------|------------|
| Lucent Citadel         | 0             | 36                | +36        |
| Dreadsail Reef         | 2             | 36                | +34        |
| Sanity's Edge          | 0             | 12                | +12        |

## What's the Difference?

### fightRankings (Current Implementation)

**Returns**: Team/group performance rankings

**Criteria**:
- One ranking per report
- Based on fastest clear time (`metric: speed`)
- Represents the entire team's performance
- Only includes "ranked" reports (submitted for leaderboard)

**Example Result**:
```json
{
  "guild": "Clown Consortium",
  "duration": 327100,
  "report": {
    "code": "zB9d31qxZJA4XGDn",
    "fightID": 1
  }
}
```

**Use Case**: Finding the fastest team clears

---

### characterRankings (Alternative)

**Returns**: Individual player performance rankings

**Criteria**:
- One ranking per player (across all reports)
- Based on individual metrics (`dps`, `hps`, `bossdps`, `tankhps`)
- Ranks top performers regardless of team speed
- Includes reports from any source (not just speed leaderboard)

**Example Result**:
```json
{
  "name": "Anonymous",
  "class": "Arcanist",
  "spec": "StaminaDPS",
  "amount": 160475,
  "report": {
    "code": "a:NK4cCQRxfwgpT8XD"
  }
}
```

**Use Case**: Finding top individual player performances

## Lucent Citadel Detailed Results

### Using characterRankings (DPS metric)

**Found 36 player rankings!**

Top 5 Players:

1. **Anonymous** (Arcanist - StaminaDPS)
   - DPS: 160,475
   - Report: `a:NK4cCQRxfwgpT8XD`

2. **Miss Jenna** (Arcanist - StaminaDPS)
   - DPS: 148,191
   - Report: `aqx7Vr9jvZT6bKJ2`

3. **Faranist** (Arcanist - StaminaDPS)
   - DPS: 141,443
   - Report: `aqx7Vr9jvZT6bKJ2`

4. **Valac Miraulus** (Templar - StaminaDPS)
   - DPS: 140,085
   - Report: `2w4kz6KWapd8VjTc`

5. **Mit'Suri** (Arcanist - StaminaDPS)
   - DPS: 131,962
   - Report: `aqx7Vr9jvZT6bKJ2`

### Key Observations

✅ **All rankings have valid report codes!**
- These are actual ESO Logs reports we can fetch
- We can extract full combat log data
- We can analyze builds, gear, abilities

✅ **Multiple unique reports found:**
- `a:NK4cCQRxfwgpT8XD`
- `aqx7Vr9jvZT6bKJ2` (appears 3 times in top 5)
- `2w4kz6KWapd8VjTc`

## GraphQL Query Comparison

### Current: fightRankings

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

**Variables**: `{"encounterID": 60}`

**Result**: 0 rankings (empty array)

---

### Alternative: characterRankings

```graphql
query GetCharacterRankings($encounterID: Int!, $metric: CharacterRankingMetricType!) {
  worldData {
    encounter(id: $encounterID) {
      characterRankings(
        metric: $metric
      )
    }
  }
}
```

**Variables**: `{"encounterID": 60, "metric": "dps"}`

**Result**: 36 rankings!

## Why characterRankings Returns More Data

1. **Different Leaderboard Source**:
   - `fightRankings`: Only reports explicitly ranked on speed leaderboard
   - `characterRankings`: Any report with valid combat data

2. **Granularity**:
   - `fightRankings`: One entry per team/report
   - `characterRankings`: One entry per player (up to 12 per report)

3. **Ranking Criteria**:
   - `fightRankings`: Team must submit for speed ranking
   - `characterRankings`: Individual performance across all reports

4. **Data Volume**:
   - `fightRankings`: Limited by team submissions
   - `characterRankings`: All players from all reports

## Available Metrics

### characterRankings Metrics

- `dps` - Damage per second
- `hps` - Healing per second
- `bossdps` - Damage to boss only
- `tankhps` - Tank healing per second

## Implications for Build Analysis

### Using fightRankings (Current)

**Pros**:
- ✅ Focuses on fastest/best teams
- ✅ Represents meta strategies
- ✅ One report per ranking = less duplicate processing

**Cons**:
- ❌ Misses content without speed rankings
- ❌ Limited data for newer trials
- ❌ May show 0 results when data exists

### Using characterRankings (Proposed)

**Pros**:
- ✅ Much more data available
- ✅ Works for trials without speed rankings
- ✅ Captures individual top performers
- ✅ Multiple reports per trial

**Cons**:
- ⚠️ May include outlier/non-meta builds
- ⚠️ More data to process (36 vs 10-12 reports)
- ⚠️ Need to deduplicate builds across reports

## Recommendation

### Option 1: Hybrid Approach (Best of Both)

Use **fightRankings first**, fall back to **characterRankings** if empty:

```python
# Try team rankings first
rankings = await get_fight_rankings(encounter_id)

# If no team data, get individual player data
if not rankings:
    rankings = await get_character_rankings(encounter_id, metric='dps')
```

**Benefits**:
- Prioritizes meta/fastest teams when available
- Falls back to individual data for newer trials
- Maximizes data coverage

### Option 2: Use characterRankings Only

Switch entirely to `characterRankings(metric: dps)`:

**Benefits**:
- ✅ Consistent data for all trials
- ✅ More comprehensive build coverage
- ✅ Works for new content immediately

**Trade-offs**:
- ⚠️ More data processing required
- ⚠️ May need stricter build filtering

## Implementation Changes Required

### For characterRankings

**Query Change** (`api_client.py:194-204`):
```graphql
# Replace this:
fightRankings(metric: speed)

# With this:
characterRankings(metric: dps)
```

**Response Parsing** (`api_client.py:222-255`):
```python
# Current: extract from fight_rankings
fight_rankings = data['data']['worldData']['encounter']['fightRankings']

# New: extract from character_rankings
char_rankings = data['data']['worldData']['encounter']['characterRankings']
rankings = char_rankings.get('rankings', [])

# Each ranking has:
# - name: player name
# - class: character class
# - spec: specialization
# - amount: DPS value
# - report: {code, fightID, startTime}
```

**Report Extraction**:
```python
top_reports = []
seen_reports = set()

for ranking in rankings[:50]:  # Process top 50 players
    report = ranking.get('report', {})
    code = report.get('code')

    # Avoid duplicate reports
    if code and code not in seen_reports:
        seen_reports.add(code)
        top_reports.append({
            "code": code,
            "fightID": report.get('fightID', 1),
            # ... metadata
        })
```

## Conclusion

**characterRankings provides significantly more data** and would resolve the "No leaderboard data (yet)" issue for Lucent Citadel and other trials.

**Recommended Action**:
Implement hybrid approach - try `fightRankings` first, fall back to `characterRankings(metric: dps)` when no team data exists.

This ensures:
- ✅ Maximum data coverage
- ✅ Prioritizes meta builds from fastest teams
- ✅ Captures data for newer trials
- ✅ Backwards compatible with existing trials
