# Lucent Citadel API Call Details

## How encounterID is Discovered

### Step 1: Fetch All Zones and Encounters

The application first queries the ESO Logs API to get all available zones (trials) and their encounters (bosses).

**GraphQL Query** (`api_client.py:117-133`):
```graphql
query GetZones {
  worldData {
    zones {
      id
      name
      encounters {
        id
        name
      }
    }
  }
}
```

**Response for Lucent Citadel**:
```json
{
  "data": {
    "worldData": {
      "zones": [
        {
          "id": 18,
          "name": "Lucent Citadel",
          "encounters": [
            {
              "id": 58,
              "name": "Count Ryelaz and Zilyesset"
            },
            {
              "id": 59,
              "name": "Orphic Shattered Shard"
            },
            {
              "id": 60,
              "name": "Xoryn"
            }
          ]
        }
      ]
    }
  }
}
```

### Step 2: Select Final Boss

The application (`trial_scanner.py:95-105`) selects the **last encounter** in the list as the final boss:

```python
encounters = zone.get('encounters', [])
if not encounters:
    logger.warning(f"No encounters found for {trial['name']}")
    continue

final_boss = encounters[-1]  # Last encounter = final boss
final_boss_id = final_boss.get('id')
final_boss_name = final_boss.get('name')

logger.info(f"Getting top reports from final boss: {final_boss_name} (ID: {final_boss_id})")
```

**For Lucent Citadel**:
- Zone ID: 18
- Zone Name: "Lucent Citadel"
- Encounters: 3 bosses
- **Final Boss**: Xoryn (ID: 60) ← This becomes our encounterID

### Step 3: Query Rankings for Final Boss

Now the encounterID (60) is used in the fightRankings query.

### Visual Flow

```
Trial Selection (data/trials.json)
        ↓
    trial_id: 18
    trial_name: "Lucent Citadel"
        ↓
Get Zones Query (api_client.py:get_zones)
        ↓
    {
      id: 18,
      name: "Lucent Citadel",
      encounters: [
        {id: 58, name: "Count Ryelaz and Zilyesset"},
        {id: 59, name: "Orphic Shattered Shard"},
        {id: 60, name: "Xoryn"}  ← Final boss (last in array)
      ]
    }
        ↓
Select Final Boss (trial_scanner.py)
        ↓
    encounters[-1]
    → encounterID: 60
    → encounterName: "Xoryn"
        ↓
Query Rankings (api_client.py:get_top_ranked_reports)
        ↓
    fightRankings(encounterID: 60, metric: speed)
        ↓
    Response: {"rankings": []}  ← Empty (no data)
```

## GraphQL Query for Rankings

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

## Variables Used for Lucent Citadel

```json
{
  "encounterID": 60
}
```

**Breakdown**:
- `encounterID`: 60 = Xoryn (final boss of Lucent Citadel)
- `metric`: speed = Rankings based on fastest clear time
- No difficulty filter (gets all difficulties)
- No leaderboard type filter (defaults to all available rankings)

## Expected Response Structure

```json
{
  "data": {
    "worldData": {
      "encounter": {
        "fightRankings": {
          "rankings": [
            {
              "report": {
                "code": "ABC123xyz",
                "fightID": 1,
                "startTime": 1234567890
              },
              "duration": 180000,
              "score": 95.5,
              "guild": {
                "name": "Example Guild"
              },
              "server": {
                "name": "NA"
              },
              "tanks": 2,
              "healers": 2,
              "melee": 4,
              "ranged": 4
            }
          ]
        }
      }
    }
  }
}
```

## Actual Response for Lucent Citadel

```json
{
  "data": {
    "worldData": {
      "encounter": {
        "fightRankings": {
          "rankings": []
        }
      }
    }
  }
}
```

**Result**: Empty rankings array = No leaderboard data available

## How the System Processes This

1. **API Client** (`api_client.py:206-210`):
   - Calls ESO Logs GraphQL API with encounterID=60
   - Uses metric=speed for fastest clear times

2. **Response Parsing** (`api_client.py:222-231`):
   ```python
   fight_rankings = data['data']['worldData']['encounter']['fightRankings']

   if isinstance(fight_rankings, dict):
       rankings = fight_rankings.get('rankings', [])
   elif isinstance(fight_rankings, list):
       rankings = fight_rankings
   ```

3. **Report Extraction** (`api_client.py:235-255`):
   ```python
   top_reports = []
   for ranking in rankings[:limit]:  # rankings is empty for Lucent Citadel
       report = ranking.get('report', {})
       code = report.get('code')
       # ... extract report metadata
   ```

4. **Result**:
   - `top_reports` = [] (empty list)
   - Logged as: "Found 0 top-ranked reports"

## Why No Data?

The ESO Logs API is returning an empty `rankings` array for Lucent Citadel Encounter 60 (Xoryn). This means:

1. **No Ranked Logs**: Players haven't uploaded logs that qualify for rankings
2. **New Content**: Trial may be too recent for leaderboard data
3. **Ranking Criteria**: Logs may not meet ESO Logs' ranking requirements
4. **Participation**: Trial may have low player participation

## Alternative Checks We Could Do

1. **Check other bosses**:
   - Encounter 58: Count Ryelaz and Zilyesset
   - Encounter 59: Orphic Shattered Shard

2. **Try different metrics**:
   - `metric: dps` - DPS-based rankings
   - `metric: hps` - Healing-based rankings

3. **Check for ANY reports** (not just ranked):
   - Would require a different query to fetch recent reports regardless of ranking

## Current Implementation

The application uses `fightRankings(metric: speed)` which only returns reports that:
- Have been successfully parsed by ESO Logs
- Meet the ranking criteria (valid completion, proper logging, etc.)
- Are submitted to the public leaderboard

If no reports meet these criteria, the API returns an empty array, which is exactly what we're seeing for Lucent Citadel.
