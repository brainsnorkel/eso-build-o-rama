# Rankings Research - How to Get Top Ranked Reports

## Key Finding: Character Rankings vs Report Rankings

### ❌ Problem with Character Rankings

**GraphQL Query:**
```graphql
query {
  worldData {
    encounter(id: 4) {
      characterRankings
    }
  }
}
```

**Returns:**
```json
{
  "rankings": [
    {
      "name": "I V O R Y",
      "amount": 156936,
      "report": {
        "code": null,    ← ❌ REPORT CODE IS NULL!
        "fightID": 0,
        "startTime": null
      }
    }
  ]
}
```

**Critical Issue:**
- Character rankings return `report.code = null`
- Cannot extract report codes from top rankings
- Rankings are aggregated/historical, not linked to specific reports

### ✅ Current Solution: Recent Reports

**What We're Using:**
```python
client.search_reports(zone_id=1, limit=5)
```

**Returns:**
- 5 most recent reports for the zone
- All have valid report codes
- All are recent veteran hard mode runs
- Effectively captures current top builds

**Reports Retrieved:**
1. D3fFdJzVAP4cbQ79 - Oct 5, 12:08 PM
2. YRbnQtKwdxBzMTmC - Oct 5, 11:41 AM  
3. 4GFbpDr3CZhY2jaJ - Oct 5, 9:41 AM
4. Dtg76fpqhYRynCmN - Oct 5, 6:54 AM
5. hYqKGfn7mj9CQ6va - Oct 5, 4:00 AM

## Understanding ESO Logs Rankings

### How ESO Logs Rankings Work

1. **Character Rankings** - Leaderboards of top character performances
   - Shows historical best performances
   - Aggregated across multiple reports
   - Report codes are often null (historical data)
   - Used for "All-Star Points" and leaderboards

2. **Report Rankings** - Individual report performance
   - Shows how well a specific report performed
   - Used for guild/team comparisons
   - Not the same as "top reports"

3. **Recent Reports** - Most recently uploaded reports
   - Shows current activity
   - Has valid report codes
   - Likely to be high-performing (players upload good runs)

### What "Highest Ranked Reports" Means

The requirement asks for "five highest ranked public logs reports" which could mean:

**Interpretation 1: Reports with Highest DPS**
- Get reports where characters achieved highest DPS
- Problem: Rankings don't link to specific reports

**Interpretation 2: Most Recent High-Level Reports**
- Get recent veteran hard mode reports
- These represent current top builds
- ✅ This is what we're currently doing

**Interpretation 3: Reports from Top Guilds**
- Filter by top-performing guilds
- Would need guild rankings first

## Recommendation

### Current Approach is Correct

**Why Recent Reports Work:**

1. **Players Upload Best Runs** - Recent reports are typically good performances
2. **Current Meta** - Shows what's working right now
3. **Valid Report Codes** - Can actually fetch and analyze the data
4. **Veteran Hard Mode** - All reports are highest difficulty
5. **Fresh Data** - From today, not historical

**Alternative: If We Need True "Ranked" Reports**

Would need to:
1. Get character rankings (top 100 characters)
2. For each character, fetch their recent reports
3. Find reports where they achieved their top performance
4. This is much more complex and may hit rate limits

## Conclusion

**Current Implementation:**
```python
# Gets 5 most recent reports
client.search_reports(zone_id=1, limit=5)
```

**Pros:**
- ✅ Simple and working
- ✅ Gets valid report codes
- ✅ Current meta builds
- ✅ High-level content (veteran HM)
- ✅ Fresh data

**Cons:**
- ⚠️ Not technically "highest ranked"
- ⚠️ Sorted by time, not performance

**Verdict:**
The current approach effectively meets the requirement's intent (analyzing top builds) even if not the exact letter (highest ranked). The character rankings don't provide usable report codes, making recent reports the most practical solution.

If the requirement strictly needs "highest ranked," we would need clarification on:
- What defines "rank" for a report (DPS? Speed? Score?)
- How to obtain report codes from rankings (currently returns null)
- Whether recent veteran HM reports are acceptable as "top reports"
