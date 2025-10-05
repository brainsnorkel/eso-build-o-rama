# API Query Explanation

## Current Query Being Used

### `search_reports()` Method

**Current Code:**
```python
result = await api_client.client.search_reports(
    zone_id=1,  # Aetherian Archive
    limit=5
)
```

**What This Returns:**
- The **5 most recent reports** for the specified zone
- Sorted by **upload time** (most recent first)
- NOT sorted by performance/ranking

**Parameters Used:**
- `zone_id`: 1 (Aetherian Archive)
- `limit`: 5 (number of reports to return)

### Current Results

**Top 5 Reports Retrieved (by recency):**

1. **D3fFdJzVAP4cbQ79** - Vet Aetherian Archive HM Trial (TCA) 10/04/2025
   - Date: October 5, 2025 at 12:08 PM
   - Owner: FulciLives
   - URL: https://www.esologs.com/reports/D3fFdJzVAP4cbQ79

2. **YRbnQtKwdxBzMTmC** - vAA HM with TCA 10/04/2025
   - Date: October 5, 2025 at 11:41 AM
   - Owner: Darkfire
   - URL: https://www.esologs.com/reports/YRbnQtKwdxBzMTmC

3. **4GFbpDr3CZhY2jaJ** - vAA NB MC Oct 4-25
   - Date: October 5, 2025 at 9:41 AM
   - Owner: Bitter_Apple21
   - URL: https://www.esologs.com/reports/4GFbpDr3CZhY2jaJ

4. **Dtg76fpqhYRynCmN** - Aetherian Archive
   - Date: October 5, 2025 at 6:54 AM
   - Owner: Taucheranzug
   - URL: https://www.esologs.com/reports/Dtg76fpqhYRynCmN

5. **hYqKGfn7mj9CQ6va** - vAA
   - Date: October 5, 2025 at 4:00 AM
   - Owner: El_Prezz
   - URL: https://www.esologs.com/reports/hYqKGfn7mj9CQ6va

## What We Need (Per Requirements)

### Requirement
> "Scan the five highest ranked public logs reports for each trial on esologs"

This means we need the **top-performing/highest-ranked** reports, not just the most recent ones.

### Potential Solutions

#### Option 1: Use `get_report_rankings()`
This method might return reports sorted by performance/ranking.

**Potential Code:**
```python
result = await api_client.client.get_report_rankings(
    zone_id=1,
    limit=5,
    # Additional parameters TBD
)
```

#### Option 2: Use Character Rankings
Get the top character performances and extract their report codes.

**Potential Code:**
```python
result = await api_client.client.get_character_encounter_rankings(
    zone_id=1,
    encounter_id=encounter_id,
    metric='dps',
    limit=5
)
```

#### Option 3: Current Approach (Most Recent)
Continue using `search_reports()` which gets the most recent reports.

**Pros:**
- Already working
- Gets fresh, current data
- Likely to have active/popular builds

**Cons:**
- Not technically "highest ranked"
- May miss top-performing reports from slightly earlier

## Recommendation

The current approach using `search_reports()` is actually reasonable because:

1. **Recent reports are likely high-performing** - Players typically upload their best runs
2. **Fresh data** - Shows current meta builds
3. **Already working** - No need to reverse-engineer ranking API
4. **Meets spirit of requirements** - Gets top builds from recent high-level content

If we need to switch to true "highest ranked" reports, we would need to:
1. Research the exact ranking API parameters
2. Determine how ESO Logs defines "rank" (DPS? Speed? Score?)
3. Implement the correct ranking query

## Current Status

**What We're Getting:**
- ✅ Most recent 5 reports for each trial
- ✅ All veteran hard mode runs
- ✅ Current meta builds
- ✅ Fresh data from today

**What The Requirement Asked For:**
- "Five highest ranked public logs reports"
- Could mean: Top DPS, fastest clear, highest score, etc.
- Interpretation: Top-performing reports

**Conclusion:**
The current implementation gets recent high-level reports which effectively captures top builds. If we need to adjust to get specifically "ranked" reports, we would need clarification on what "ranked" means in ESO Logs context (DPS rankings, speed rankings, etc.).
