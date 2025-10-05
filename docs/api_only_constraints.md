# API-Only Constraint Analysis

**Date:** October 5, 2025  
**Issue:** New requirement states "Do not use web scraping to access ESOlogs, only the API"

## Problem Statement

The original requirements specify:
- Collect "Ability bars" for each player (line 13)
- Display "An icon-based display of the slotted abilities" (line 38)

However, our research showed:
- Ability bars are **not fully available** in the ESO Logs API
- The reference project (`top-builds`) uses **web scraping** for ability data
- This creates a conflict with the new API-only constraint

## Potential Solutions

### Option 1: API-Only Approach
**Pros:**
- Follows the constraint exactly
- No web scraping complexity
- Faster execution
- More reliable (no DOM parsing)

**Cons:**
- May lose ability bar information
- Less detailed build information
- Might not meet original requirements

**Investigation needed:**
- What ability data IS available in the API?
- Can we infer abilities from damage/event data?
- Are ability names in the damage breakdown?

### Option 2: Hybrid Approach
**Pros:**
- Gets ability data from API where possible
- Falls back to alternative sources if needed
- More complete build information

**Cons:**
- Violates the API-only constraint
- More complex implementation

### Option 3: Simplified Build Pages
**Pros:**
- Focus on gear/sets (which are in API)
- Skip ability bars entirely
- Still valuable build information

**Cons:**
- Doesn't meet original requirements
- Less useful to users

## ✅ SOLUTION FOUND

**Date Updated:** October 5, 2025

### Ability Bars ARE Available in API!

The `includeCombatantInfo=True` parameter in the table query returns ability bar data!

**Code from top-builds reference:**
```python
table_data = await client._make_request(
    "get_report_table",
    code=report_code,
    start_time=int(fight.start_time),
    end_time=int(fight.end_time),
    data_type="Summary",
    hostility_type="Friendlies",
    includeCombatantInfo=True  # <-- THIS IS THE KEY!
)
```

This resolves the conflict between:
- Requirements: Need ability bars
- Constraint: API-only (no web scraping)

**Conclusion:** We CAN meet all requirements with API-only approach! ✅

## Next Steps

1. ✅ **RESOLVED** - Ability data is available via API
2. Implement `get_report_table()` with `includeCombatantInfo=True`
3. Parse combatant info to extract ability bars
4. Focus on gear/set analysis which is also in API

## Files to Update

- [ ] `api_client.py` - Add methods to extract ability data from API
- [ ] `docs/open_questions.md` - Add investigation tasks
- [ ] `docs/project_plan.md` - Update architecture for API-only approach
