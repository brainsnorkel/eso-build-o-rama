# ESO Build-O-Rama Utilities

Utility scripts for testing and debugging.

## Query Tester

Test different GraphQL query configurations to see what reports are returned.

### Quick Start

```bash
# Test with default encounter (The Mage, ID: 4)
python3 utils/query_tester.py

# Test with a specific encounter ID
python3 utils/query_tester.py 12  # The Serpent
```

### Features

- **Test different query types**: characterRankings, fightRankings, etc.
- **Test different metrics**: dps, hps, playerscore, etc.
- **Test different leaderboards**: LogsOnly, etc.
- **Compare queries side-by-side**
- **See report codes and URLs**
- **Count unique reports returned**

### Example Output

```
================================================================================
Testing: characterRankings | metric: dps | leaderboard: LogsOnly
================================================================================

Query:
        query GetRankings($encounterID: Int!) {
          worldData {
            encounter(id: $encounterID) {
              characterRankings(
                metric: dps
                leaderboard: LogsOnly
              )
            }
          }
        }

Variables: {'encounterID': 4}

✅ Query Successful!

Data Type: <class 'list'>

📊 Found 10 rankings

Showing top 10 results:

1. Character Name
   Class: Sorcerer (Daedric Summoning)
   Amount: 156,936
   ✅ Report Code: ABC123XYZ456 (Fight 7)
      URL: https://www.esologs.com/reports/ABC123XYZ456#7
...

📋 Summary:
   Total rankings: 10
   With report codes: 10
   Without codes: 0
   Unique reports: 8
```

### Customizing Queries

Edit `query_tester.py` to test different configurations:

```python
# Test a specific query
await tester.test_query(
    query_type="characterRankings",
    encounter_id=4,
    metric="dps",
    leaderboard="LogsOnly",
    limit=10
)

# Compare multiple queries
await tester.compare_queries(encounter_id=4, limit=5)
```

### Common Encounter IDs

- **Aetherian Archive**
  - 1: Lightning Storm Atronach
  - 2: Foundation Stone Atronach
  - 3: Varlariel
  - 4: The Mage
  
- **Hel Ra Citadel**
  - 5: Ra Kotu
  - 6: The Yokedas
  - 8: The Warrior

- **Sanctum Ophidia**
  - 9: Possessed Mantikora
  - 10: Stonebreaker
  - 11: Ozara
  - 12: The Serpent

See `data/trial_bosses.json` for complete list.

### What We Learned

From our experiments:

✅ **Works:**
- `characterRankings` with `metric: dps` and `leaderboard: LogsOnly`

❌ **Doesn't Work:**
- `reportRankings` - doesn't exist in API
- `fightRankings` with `metric: playerscore` - metric not supported
