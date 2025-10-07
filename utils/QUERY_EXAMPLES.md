# Query Testing Examples

Quick reference for testing different query configurations.

## How to Modify Queries

Edit the `main()` function in `query_tester.py` to test different queries:

### Test a Single Query

```python
await tester.test_query(
    query_type="characterRankings",  # Type of ranking
    encounter_id=4,                  # Encounter ID to query
    metric="dps",                    # Metric to use
    leaderboard="LogsOnly",          # Leaderboard type (or None)
    limit=10                         # How many results to show
)
```

### Available Options

#### Query Types
- `characterRankings` ✅ (works)
- `fightRankings` ⚠️  (exists but limited metrics)
- `reportRankings` ❌ (doesn't exist)

#### Metrics for characterRankings
- `dps` ✅ (works)
- `hps` ✅ (works for healers)
- `playerscore` ✅ (works but no report codes without LogsOnly)

#### Metrics for fightRankings
- `dps` ⚠️  (untested)
- `playerscore` ❌ (doesn't exist)

#### Leaderboard Types
- `LogsOnly` ✅ (returns report codes!)
- `None` (default, may not return codes)

### Example Tests

#### Test without LogsOnly (to see the difference)
```python
await tester.test_query(
    query_type="characterRankings",
    encounter_id=4,
    metric="dps",
    leaderboard=None,  # No leaderboard filter
    limit=10
)
```

#### Test with HPS (healer rankings)
```python
await tester.test_query(
    query_type="characterRankings",
    encounter_id=4,
    metric="hps",
    leaderboard="LogsOnly",
    limit=10
)
```

#### Test fightRankings with DPS
```python
await tester.test_query(
    query_type="fightRankings",
    encounter_id=4,
    metric="dps",
    leaderboard=None,
    limit=10
)
```

### Compare Multiple Queries

Uncomment the comparison section in `main()`:

```python
# Uncomment to compare multiple queries
await tester.compare_queries(encounter_id, limit=5)
```

This will run multiple query configurations side-by-side.

### Add Custom Tests

Add to the `tests` list in `compare_queries()`:

```python
tests = [
    {
        "name": "My custom test",
        "query_type": "characterRankings",
        "metric": "dps",
        "leaderboard": "LogsOnly"
    },
    {
        "name": "Another test",
        "query_type": "characterRankings",
        "metric": "hps",
        "leaderboard": None
    },
]
```

## What to Look For

When testing queries, check:

1. **Does it return data?** (no errors)
2. **Does it include report codes?** (✅ vs ❌)
3. **How many unique reports?** (more is better)
4. **Are the reports recent?** (click URLs to check)

## Key Finding

**The winning combination:**
```python
query_type="characterRankings"
metric="dps"
leaderboard="LogsOnly"
```

This returns:
- ✅ Valid report codes
- ✅ Multiple unique reports (60+ for popular bosses)
- ✅ Top DPS performances
- ✅ Clickable URLs to view reports
