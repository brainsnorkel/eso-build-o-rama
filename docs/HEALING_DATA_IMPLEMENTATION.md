# Implementation Guide: Real Healing Per Second (HPS)

## Current State (Placeholder Implementation)

The current implementation in `feature/role-specific-metrics` branch is a **placeholder** that attempts to extract healing data from the `DamageDone` table:

```python
# In data_parser.py - Current fallback approach
if 'total' in player_data and player_data.get('type') == 'healing':
    effective_healing = player_data.get('total', 0)
    overheal = player_data.get('overheal', 0)
    total_healing_output = effective_healing + overheal
```

**Problem:** The `DamageDone` table primarily contains damage metrics. Healing data in this table is incomplete or absent for most healers.

---

## Required Implementation: Proper HPS from Healing Table

To get **accurate, real healing per second**, you need to:

1. **Query the Healing table separately** from the API
2. **Match healing data to players** by player ID
3. **Merge healing stats** into PlayerBuild objects
4. **Handle missing data** gracefully (some players may not have healing data)

---

## Implementation Steps

### Step 1: Fetch Healing Table (in `trial_scanner.py`)

**Location:** `src/eso_build_o_rama/trial_scanner.py`, in the `_process_single_fight()` method

**Current code** (around line 118-133):
```python
# Fetch table data with combatant info
summary_data = await self.api_client.get_report_table(
    report_code=report_code,
    start_time=fight_info.get('startTime'),
    end_time=fight_info.get('endTime'),
    data_type="Summary",
    include_combatant_info=True
)

damage_data = await self.api_client.get_report_table(
    report_code=report_code,
    start_time=fight_info.get('startTime'),
    end_time=fight_info.get('endTime'),
    data_type="DamageDone",
    include_combatant_info=True
)
```

**Required addition:**
```python
# Add this AFTER fetching damage_data
healing_data = await self.api_client.get_report_table(
    report_code=report_code,
    start_time=fight_info.get('startTime'),
    end_time=fight_info.get('endTime'),
    data_type="Healing",  # <-- Key: Use Healing table
    include_combatant_info=False  # We already got gear/abilities from DamageDone
)

if healing_data:
    logger.info(f"✓ Fetched healing data for {report_code}")
else:
    logger.warning(f"No healing data available for {report_code}")
```

---

### Step 2: Pass Healing Data to Parser

**Current code** (around line 136-149):
```python
if not damage_data:
    logger.error(f"Failed to fetch damage data for report {report_code}")
    return None

# Parse player data
players = self.data_parser.parse_report_data(
    report_data=report_data,
    table_data=damage_data,
    fight_id=fight_id,
    player_details_data=summary_data
)
```

**Required change:**
```python
if not damage_data:
    logger.error(f"Failed to fetch damage data for report {report_code}")
    return None

# Parse player data with healing data included
players = self.data_parser.parse_report_data(
    report_data=report_data,
    table_data=damage_data,
    fight_id=fight_id,
    player_details_data=summary_data,
    healing_data=healing_data  # <-- NEW: Pass healing table data
)
```

---

### Step 3: Update Parser Method Signature

**Location:** `src/eso_build_o_rama/data_parser.py`

**Current signature** (around line 142):
```python
def parse_report_data(
    self,
    report_data: Dict[str, Any],
    table_data: Any,
    fight_id: int,
    player_details_data: Any = None
) -> List[PlayerBuild]:
```

**Required change:**
```python
def parse_report_data(
    self,
    report_data: Dict[str, Any],
    table_data: Any,
    fight_id: int,
    player_details_data: Any = None,
    healing_data: Any = None  # <-- NEW parameter
) -> List[PlayerBuild]:
```

---

### Step 4: Extract Healing Metrics from Healing Table

**Add this code** in `parse_report_data()`, after parsing players from damage table but before returning:

```python
# Extract healing data if available
healing_lookup = {}
if healing_data:
    try:
        # Extract healing table entries
        if hasattr(healing_data, 'report_data') and hasattr(healing_data.report_data, 'report'):
            healing_table = healing_data.report_data.report.table
            healing_entries = healing_table['data'].get('entries', [])
            
            # Build lookup: player_id -> healing stats
            for entry in healing_entries:
                player_id = entry.get('id')
                if player_id:
                    # Calculate HPS including overheal
                    effective_healing = entry.get('total', 0)  # Actual healing done
                    overheal = entry.get('overheal', 0)  # Wasted healing
                    active_time_ms = entry.get('activeTime', 1)
                    
                    # Total healing output = effective + overheal
                    total_healing_output = effective_healing + overheal
                    hps = (total_healing_output / active_time_ms) * 1000 if active_time_ms > 0 else 0
                    
                    healing_lookup[player_id] = {
                        'healing': hps,
                        'effective_healing': effective_healing,
                        'overheal': overheal,
                        'total_healing': total_healing_output
                    }
            
            logger.info(f"Extracted healing data for {len(healing_lookup)} players")
    
    except Exception as e:
        logger.warning(f"Failed to parse healing data: {e}")
```

---

### Step 5: Merge Healing Data into PlayerBuild Objects

**Add this code** after creating the healing_lookup:

```python
# Merge healing data into player objects
for player in players:
    if player.player_id in healing_lookup:
        healing_info = healing_lookup[player.player_id]
        player.healing = healing_info['healing']
        
        # Optional: Calculate healing percentage (healing / total healing in fight)
        # player.healing_percentage = ...
        
        logger.debug(f"Added {healing_info['healing']:,.0f} HPS to {player.character_name}")
    elif player.role.lower() == "healer":
        logger.debug(f"No healing data found for healer {player.character_name}")
```

---

### Step 6: Remove Placeholder Code

**In `_parse_player()` method**, remove or comment out the placeholder healing extraction:

```python
# REMOVE THIS SECTION (it's the placeholder):
# Get Healing stats
# healing = 0
# healing_percentage = 0
# if role == "healer":
#     if 'total' in player_data and player_data.get('type') == 'healing':
#         ...

# REPLACE WITH:
# Healing data will be populated separately from Healing table
healing = 0
healing_percentage = 0
# Actual healing will be added after parsing from Healing table
```

---

## API Query Details

### GraphQL Query Structure

The API already supports this via the existing `get_report_table()` method. The query is:

```graphql
query GetReportTable(
  $code: String!
  $startTime: Float
  $endTime: Float
  $dataType: TableDataType!
  $fightIDs: [Int]
) {
  reportData {
    report(code: $code) {
      table(
        startTime: $startTime
        endTime: $endTime
        dataType: $dataType
        fightIDs: $fightIDs
      )
    }
  }
}
```

**Variables for Healing:**
```json
{
  "code": "abc123XYZ",
  "startTime": 1234567890,
  "endTime": 1234567999,
  "dataType": "Healing",    // <-- The key parameter
  "fightIDs": [1]
}
```

### Healing Table Response Structure

The Healing table returns data in this format:

```python
{
  'data': {
    'entries': [
      {
        'id': 12345,           # Player source ID
        'name': 'CharacterName',
        'type': 'Warden',      # Class
        'total': 45000000,     # Effective healing (healed wounds)
        'overheal': 12000000,  # Wasted healing (overhealing)
        'activeTime': 180000,  # Active time in ms
        'abilities': [...]     # Breakdown by spell
      },
      # ... more players
    ]
  }
}
```

### HPS Calculation Formula

```python
# Total healing output (including overheal)
total_healing = effective_healing + overheal

# Healing per second
hps = (total_healing / active_time_ms) * 1000

# Example:
# effective_healing = 45,000,000
# overheal = 12,000,000
# active_time = 180,000 ms (3 minutes)
# hps = (45M + 12M) / 180,000 * 1000 = 316,666 HPS = 317K HPS
```

---

## Performance Considerations

### API Rate Limiting
- Each fight requires **3 API calls** instead of 2:
  - Summary table (for roles/names)
  - DamageDone table (for DPS/gear/abilities)
  - **Healing table** (for HPS) - NEW
  
- This increases API usage by **50%**
- Ensure rate limiting is properly configured in `api_client.py`
- Current default: 2 seconds between requests
- **Recommendation:** Keep the 2-second delay, but monitor for rate limit errors

### Caching
- The `get_report_table()` method already supports caching
- Healing table results will be cached with key: `table_{report_code}_Healing_False_{time}_{fights}`
- Cache hit rate should be high for repeated trials
- **Benefit:** Subsequent runs won't re-fetch healing data

### Processing Time
- Additional API call adds ~2-3 seconds per fight
- For 12 reports × avg 8 bosses = 96 fights
- Total additional time: ~3-5 minutes per trial scan
- **Mitigation:** Cache effectiveness reduces this on subsequent runs

---

## Data Quality Considerations

### When Healing Data May Be Missing
1. **Very old logs** - ESO Logs may not have healing data for ancient reports
2. **Private reports** - API may restrict access to certain data
3. **API errors** - Network issues or rate limiting
4. **No healers in fight** - Solo arena runs, DPS-only groups

### Fallback Behavior
If healing data is unavailable:
- Healers will show `0 HPS` or fall back to `DPS`
- Build pages should still render correctly
- Log a warning for debugging

**Recommended approach:**
```python
# In get_primary_metric()
def get_primary_metric(self) -> float:
    if self.role.lower() == "healer":
        if self.healing > 0:
            return self.healing
        else:
            # Fallback: show DPS if no healing data
            return self.dps
    return self.dps
```

---

## Testing the Implementation

### Test with a Known Healer Build

```bash
# 1. Implement the changes above
# 2. Generate builds for a trial with healers (e.g., Dreadsail Reef)
python3 -m src.eso_build_o_rama.main --trial-id 60

# 3. Check logs for healing data
grep "Fetched healing data" *.log
grep "HPS" *.log

# 4. Serve and verify
cd output-dev && python3 -m http.server 8080

# 5. Look for healer builds showing non-zero HPS
# Navigate to a healer build page and verify:
# - Model Player shows "XXX.XK HPS" (not DPS)
# - HPS value is reasonable (100K-400K range typical)
# - Other Example Players table shows HPS
```

### Verify API Response

Add debug logging to see the healing table structure:

```python
# In parse_report_data(), after fetching healing_data
if healing_data:
    logger.debug(f"Healing table structure: {healing_table['data'].keys()}")
    logger.debug(f"Sample healing entry: {healing_entries[0] if healing_entries else 'None'}")
```

---

## Expected Results

### Before Implementation (Current)
- Healers show 0 HPS or fall back to DPS
- Or show incorrect/incomplete healing values from DamageDone table

### After Implementation (Proper)
- **Healers show accurate HPS** from Healing table
- HPS includes both effective healing and overheal
- Build pages clearly distinguish healers (HPS) from DPS (DPS)
- Example: "Model Player: 287.5K HPS"

### Typical HPS Ranges (for reference)
- **Top healers:** 200K - 400K HPS
- **Good healers:** 150K - 250K HPS  
- **Average healers:** 100K - 180K HPS
- **Varies by:** Trial difficulty, group damage taken, fight length

---

## Summary of Files to Modify

1. **`src/eso_build_o_rama/trial_scanner.py`**
   - Add healing table fetch after damage table
   - Pass healing_data to parser

2. **`src/eso_build_o_rama/data_parser.py`**
   - Add healing_data parameter to parse_report_data()
   - Extract healing metrics from Healing table
   - Merge healing data into PlayerBuild objects
   - Remove/update placeholder healing extraction

3. **Testing**
   - Run with trial containing healers
   - Verify HPS values appear on build pages
   - Check logs for successful healing data extraction

---

## Additional Enhancements (Optional)

Once basic HPS is working, consider adding:

1. **Overheal Percentage Display**
   ```
   Model Player: 287.5K HPS (18% overheal)
   ```

2. **Separate Effective Healing Display**
   ```
   Effective Healing: 235K HPS
   Total Output: 287K HPS
   Overheal: 52K (18%)
   ```

3. **Healing Breakdown by Ability**
   - Top healing spells
   - HPS contribution per ability
   - Requires parsing the 'abilities' array from Healing table

4. **Healer-Specific Sorting**
   - Sort healers by HPS (not DPS) for "best player" selection
   - Update `build_analyzer.py` to use get_primary_metric()

---

## Conclusion

The **current implementation is a placeholder**. To get real HPS:

1. ✅ Query the **Healing table** separately (data_type="Healing")
2. ✅ Extract healing + overheal from the Healing table response
3. ✅ Match by player ID and merge into PlayerBuild objects
4. ✅ Calculate HPS = (healing + overheal) / active_time * 1000

This requires modifying 2 files (`trial_scanner.py` and `data_parser.py`) and will add ~2-3 seconds per fight due to the additional API call, mitigated by caching.

