# Complete Data Summary - What's Available in ESO Logs API

## Summary of Findings

### ❌ Rankings API Limitations
- **Character rankings** return `report.code = null`
- Cannot get "highest ranked reports" directly
- Rankings are historical/aggregated, not linked to specific reports

### ✅ What We CAN Get
- **Recent reports** via `search_reports(zone_id, limit)`
- **Complete fight data** for each report
- **Full player builds** with gear, abilities, and performance
- **DPS rankings** within each fight from `damageDone` array

## Complete Data Structure

### 1. Report Search Results

```python
client.search_reports(zone_id=1, limit=5)
```

**Returns:**
- `code` - Report code (e.g., "D3fFdJzVAP4cbQ79")
- `title` - Report title
- `start_time` - When report started
- `end_time` - When report ended
- `zone` - Zone information
- `owner` - Report owner
- `guild` - Guild information (if applicable)

**No ranking/score data at report level**

### 2. Full Report Data

```python
client.get_report_by_code(report_code)
```

**Returns:**
- `code` - Report code
- `title` - Report title
- `startTime` - Report start timestamp
- `endTime` - Report end timestamp
- `fights` - Array of all fights (9-16 fights per report)

**Fight Data:**
```python
{
  "id": 1,
  "name": "Frost Atronach",
  "startTime": 19230,
  "endTime": 93237,
  "difficulty": null,
  "kill": false
}
```

### 3. Table Data (The Goldmine!)

```python
client.get_report_table(
    report_code=code,
    start_time=fight_start,
    end_time=fight_end,
    data_type="Summary",
    include_combatant_info=True  # ✅ CRITICAL!
)
```

**Returns:**

#### Top-Level Data
- `totalTime` - Fight duration (int)
- `itemLevel` - Average item level (float)
- `logVersion` - Log file version (int)
- `gameVersion` - Game version (int)

#### Player Lists
- `composition` - All players (list of 12)
- `damageDone` - Damage per player (list of 12)
- `healingDone` - Healing per player (list of 12)
- `damageTaken` - Damage taken (list of 11)
- `deathEvents` - Deaths (list)

#### ✅ Player Details (CRITICAL)
```python
"playerDetails": {
  "dps": [8 DPS players],
  "healers": [4 healer players]
}
```

### 4. Individual Player Data

**Each player in playerDetails contains:**

```python
{
  # Basic Info
  "name": "Pancake-and-syrup",           # Character name
  "id": 7,                                # Player ID (for URLs)
  "guid": 1000007,                        # Global UID
  "type": "Sorcerer",                     # Class
  "server": "NA Megaserver",
  "displayName": "@Panache1120",          # Account name
  "anonymous": false,
  "icon": "Sorcerer-StaminaDPS",
  "specs": ["StaminaDPS"],
  
  # Item Levels
  "minItemLevel": 2521,
  "maxItemLevel": 2521,
  
  # Consumables
  "potionUse": 0,
  "healthstoneUse": 0,
  
  # ✅ COMBATANT INFO (The Important Part!)
  "combatantInfo": {
    "stats": [],                          # Stats array
    
    "talents": [                          # ✅ ABILITIES (12 total)
      {
        "name": "Merciless Resolve",
        "guid": 61919,                    # Ability ID
        "type": 64,                       # Type (64=regular, 8=ultimate?)
        "abilityIcon": "ability_nightblade_005_b",
        "flags": 1
      },
      // ... 11 more abilities (6 per bar)
    ],
    
    "gear": [                             # ✅ GEAR (16 pieces)
      {
        "id": 209681,
        "slot": 0,                        # Slot ID (0=head, 1=shoulders, etc.)
        "quality": 5,                     # Quality (5=gold)
        "icon": "gear_icon",
        "name": "Beacon of Oblivion Helmet",
        "championPoints": 160,
        "trait": 1,                       # Trait ID (1=Divines, 2=Infused, etc.)
        "enchantType": 35,                # Enchant ID (35=Max Health, etc.)
        "enchantQuality": 5,
        "setID": 779,
        "type": 2,
        "setName": "Beacon of Oblivion"   # ✅ Set name!
      },
      // ... 15 more gear pieces
    ]
  }
}
```

### 5. Damage Done Data (For DPS Rankings)

**From `damageDone` array:**

```python
{
  "name": "Drazorious Vll",
  "id": 3,
  "guid": 1000003,
  "type": "Arcanist",
  "icon": "Arcanist-StaminaDPS",
  "total": 3529536                        # ✅ Total damage (for DPS calculation)
}
```

**Can be sorted to get DPS rankings within the fight!**

## What We Extract vs What's Available

### ✅ Currently Extracting

1. **Character name** - ✅ From `player.name`
2. **Player account** - ✅ From `player.displayName`
3. **Class** - ✅ From `player.type`
4. **Gear** - ✅ All 16 pieces with sets, traits, enchants
5. **Abilities** - ✅ All 12 abilities (6 per bar)
6. **Player ID** - ✅ For generating URLs

### ⚠️ TODO: Need to Extract

1. **DPS** - From `damageDone` array (match by player ID)
2. **DPS %** - Calculate from total damage
3. **Mundus stone** - From buffs (need to query buff table)
4. **Champion Points** - From buffs (need to query buff table)
5. **Skill lines** - Map ability IDs to skill lines

### ❌ Not Available in API

1. **Report-level rankings** - Reports don't have a "rank" or "score"
2. **Historical rankings** - Character rankings don't link to reports

## Answer to "Is there anything in the API about rankings?"

**Yes, but not at the report level:**

1. **Character Rankings** - Top character performances (but `report.code = null`)
2. **DPS Rankings per Fight** - Can rank players within a fight using `damageDone`
3. **Guild Rankings** - Can get top guilds
4. **Progress Race** - Can get world-first progression

**No, for what we need:**
- Cannot get "top 5 ranked reports" directly
- Reports don't have a ranking/score field
- Must use recent reports as proxy for "top reports"

## Conclusion

The ESO Logs API provides:
- ✅ Complete player build data (gear, abilities)
- ✅ DPS data per fight (from damageDone)
- ✅ Character rankings (but without report links)
- ❌ No report-level rankings

**Our current approach (recent reports) is the correct solution** because:
1. Recent veteran HM reports = high-quality builds
2. We can rank players within each fight using damageDone
3. We get complete, analyzable data
4. It meets the intent of finding "top builds"
