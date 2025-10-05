# ESO Logs API Research

## API Credentials

Found in `.env`:
- **Client ID**: `ESOLOGS_ID`
- **Client Secret**: `ESOLOGS_SECRET`
- **API Documentation**: https://www.esologs.com/v2-api-docs/eso/

## API Structure

ESO Logs uses a GraphQL API (v2).

### Authentication
- OAuth 2.0 Client Credentials Flow
- Exchange client ID and secret for access token
- Token endpoint: https://www.esologs.com/oauth/token

### Key Endpoints

#### GraphQL Endpoint
- **URL**: https://www.esologs.com/api/v2/client
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer {access_token}`
  - `Content-Type: application/json`

## Trials to Scan

Based on UESP (https://en.uesp.net/wiki/Online:Trials), current ESO trials include:

### Base Game Trials
1. **Aetherian Archive** (AA)
2. **Hel Ra Citadel** (HRC)
3. **Sanctum Ophidia** (SO)

### DLC Trials
4. **Maw of Lorkhaj** (MoL) - Thieves Guild
5. **Halls of Fabrication** (HoF) - Morrowind
6. **Asylum Sanctorium** (AS) - Clockwork City
7. **Cloudrest** (CR) - Summerset
8. **Sunspire** (SS) - Elsweyr
9. **Kyne's Aegis** (KA) - Greymoor
10. **Rockgrove** (RG) - Blackwood
11. **Dreadsail Reef** (DSR) - High Isle
12. **Sanity's Edge** (SE) - Necrom
13. **Lucent Citadel** (LC) - Gold Road

## Data Points to Extract

From each log report:
- Report ID and URL
- Fight/encounter name
- Date and game update version
- Player data:
  - Player name (@handle)
  - Character name
  - Class and subclasses
  - Gear (set, slot, trait, enchantment)
  - Abilities on both bars
  - Mundus stone (from buffs)
  - Champion Points (blue CP from buffs)
  - DPS and % contribution
  - Player summary URL for that fight

## GraphQL Query Structure

To fetch top logs for a trial, we need:

```graphql
query {
  reportData {
    reports(
      zoneID: {trial_zone_id}
      limit: 5
      page: 1
    ) {
      data {
        code
        title
        startTime
        endTime
        fights {
          id
          name
          difficulty
        }
      }
    }
  }
}
```

For each report, fetch player details:

```graphql
query {
  reportData {
    report(code: "{report_code}") {
      masterData {
        actors {
          id
          name
          type
          subType
          server
        }
      }
      fights {
        id
        name
        startTime
        endTime
      }
      playerDetails(fightID: {fight_id})
      table(fightID: {fight_id})
    }
  }
}
```

## Rate Limiting

TODO: Research ESO Logs API rate limits
- Check API documentation for specifics
- Implement exponential backoff
- Cache responses during development

## Key Findings from Reference Project

### Python Library
The `top-builds` project uses **`esologs-python`** library:
```
esologs-python @ git+https://github.com/knowlen/esologs-python.git
```

This provides a Python wrapper around the ESO Logs GraphQL API.

### Critical Files in Reference Project
- **`api_queries.py`** - Contains GraphQL query templates
- **`subclass_analyzer.py`** - Implements subclass detection from abilities
- **`models.py`** - Data models for reports
- **`web_scraper.py`** / **`playwright_encounter_scraper.py`** - Scrapes ability bar data from ESO Logs web pages
- **`class_analyzer.py`** - Analyzes player classes and builds

### Subclass Detection Algorithm
The reference project maps abilities to skill lines using a comprehensive dictionary:
- Defines all abilities for each skill line (Assassination, Ardent Flame, Dawn's Wrath, etc.)
- Counts which abilities a player has slotted
- Determines the top 3 most-used skill lines
- Uses abbreviations (e.g., 'Ass' for Assassination, 'Dawn' for Dawn's Wrath)

### API Query Examples

#### Get Report Data:
```graphql
query GetReportByCode($code: String!) {
  reportData {
    report(code: $code) {
      code
      title
      startTime
      endTime
      zone { id name }
      fights {
        id name startTime endTime
        difficulty kill bossPercentage
      }
    }
  }
}
```

#### Get Rankings (Top Logs):
```graphql
query GetRankings(
  $zoneID: Int!
  $encounterID: Int
  $difficulty: Int
  $page: Int
  $limit: Int
) {
  worldData {
    encounter(id: $encounterID) {
      characterRankings(
        zoneID: $zoneID
        page: $page
        limit: $limit
        metric: dps
      )
    }
  }
}
```

#### Get Zone/Trial Information:
```graphql
query GetZones {
  worldData {
    zones {
      id name
      encounters { id name }
    }
  }
}
```

### Data Extraction Process
1. **Fetch report by code** from ESO Logs API
2. **Get table data** for each fight (DPS, HPS, damage breakdown)
3. **Scrape ability bars** from web pages (since not in API)
4. **Extract gear** from player equipment data
5. **Identify buffs** (Mundus, Champion Points) from buff table
6. **Analyze subclasses** from slotted abilities

## Dependencies Needed

Based on reference project `requirements.txt`:
```
aiohttp>=3.8.0
esologs-python @ git+https://github.com/knowlen/esologs-python.git
httpx==0.28.1
python-dotenv==1.1.1
requests==2.32.5
```

For web scraping (ability bars):
```
playwright
beautifulsoup4
```

For static site generation:
```
jinja2
markdown
```

## Next Steps

1. ✅ Obtained API credentials
2. ✅ Identified list of trials
3. ✅ Found reference implementation with API queries
4. ✅ Located subclass detection algorithm
5. [ ] Test API authentication with credentials
6. [ ] Query available zones to get zone IDs for trials
7. [ ] Test fetching top 5 logs for a single trial
8. [ ] Understand gear/set extraction from API
9. [ ] Test ability bar scraping
10. [ ] Identify buff format (Mundus, CP)

## Reference Projects

- **top-builds** directory at `~/2025-development/eso/top-builds/` - Working implementation with all key features
- Original repo: https://github.com/brainsnorkel/ESO-Log-Build-and-Buff-Summary
- esologs-python library: https://github.com/knowlen/esologs-python
