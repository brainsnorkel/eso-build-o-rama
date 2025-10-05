# Open Questions & Research Items

## ESO Logs API
- [x] **What is the exact API endpoint structure for fetching top logs?**
  - **Answer**: GraphQL API at `https://www.esologs.com/api/v2/client`
  - Use `characterRankings` query with `zoneID`, `encounterID`, `limit`, and `metric: dps`
  - See `docs/api_research.md` for query examples
- [x] **How to filter for public logs only?**
  - **Answer**: ESO Logs API returns public logs by default in rankings
- [ ] **Rate limiting constraints and best practices?**
  - TODO: Test and document from actual API usage
  - Implement exponential backoff and caching
- [x] **Authentication requirements (API key, OAuth, etc.)?**
  - **Answer**: OAuth 2.0 Client Credentials flow
  - Exchange ESOLOGS_ID and ESOLOGS_SECRET for bearer token
  - Use `esologs-python` library which handles this automatically
- [x] **What trials are currently active in the game?**
  - **Answer**: 13 trials total (see `docs/api_research.md`)
  - Can query `worldData.zones` to get current zone IDs
- [ ] **How to get the current game update version from the API?**
  - TODO: Check report metadata or zone data
  - May need to infer from report date
- [x] **Data format for abilities, gear, and buffs in API responses?**
  - **Answer**: Table data returns DPS/damage breakdown
  - Gear from player equipment in report data
  - Abilities require web scraping (not fully in API)
  - Reference: `top-builds/src/eso_builds/` modules
- [ ] **How to identify "blue CP" (Champion Points) from the API?**
  - TODO: Examine buff table in API responses
  - Likely in player buffs/debuffs data 

## Build Detection
- [x] **Review ESO-Log-Build-and-Buff-Summary subclass detection algorithm**
  - **Answer**: Found in `top-builds/src/eso_builds/subclass_analyzer.py`
  - Maps each slotted ability to its skill line
  - Counts frequency of abilities from each skill line
  - Returns top 3 skill lines as subclasses
  - Uses abbreviations (Ass, Dawn, Herald, etc.)
- [x] **How are two-handed weapons counted (1 or 2 slots)?**
  - **Answer**: 2-handed weapons and staves count as 2 pieces
  - Confirmed in top-builds project README
- [ ] **How to handle "weaponless" or special setups?**
  - TODO: Review edge cases in reference implementation
- [ ] **What constitutes a "5-piece set" for mythic items or special sets?**
  - **Answer**: Uses LibSets database for dynamic set requirements
  - Some sets have different piece counts (monster sets = 2pc)
  - TODO: Integrate LibSets data
- [x] **How to handle arena weapons (which can be front or back bar)?**
  - **Answer**: Reference project handles arena weapons
  - Track which bar each piece is equipped on

## Data Sources & External Resources
- [ ] Best format to use from LibSets (XLSM vs Lua)?
- [ ] Can we programmatically access UESP ability URLs?
- [ ] Where to get official ESO ability icons?
  - https://github.com/sheumais/esoskillbarbuilder
- [ ] License restrictions on using esoskillbarbuilder icons?
- [ ] How to map ESO Logs ability IDs to UESP URLs?

## Hosting & Infrastructure
- [ ] AWS Lambda vs Cloudflare Workers - which is more cost-effective?
- [ ] Estimated data transfer costs for S3/Cloudflare?
- [ ] Domain name options and registration service?
- [ ] SSL certificate setup (free via Let's Encrypt/Cloudflare)?
- [ ] Best way to implement test.domain vs production domain?

## Build Publishing
- [ ] How to track which builds have been published for each update?
  - Options: JSON file in S3, DynamoDB table, SQLite in Lambda layer
- [ ] Should we archive old builds or only show current update?
- [ ] How to handle builds that appear in multiple trials/bosses?
- [ ] Versioning strategy for page templates?

## Testing
- [ ] How to get sample ESO Logs data for testing without hitting API?
- [ ] Should we mock the API or cache real responses?
- [ ] Test coverage requirements?
- [ ] Integration test strategy for deployment pipeline?

## User Experience
- [ ] Search functionality needed on index page?
- [ ] Mobile-responsive design priorities?
- [ ] Dark mode support?
- [ ] Analytics to track popular builds? (privacy-respecting)

## Legal & Attribution
- [ ] Verify terms of service for ESO Logs API usage
- [ ] Proper attribution format for all data sources
- [ ] Copyright notice requirements
- [ ] Link back requirements for ESO Logs, UESP, etc.

## Performance & Scaling
- [ ] Maximum number of builds to publish per update?
- [ ] How long can Lambda run (timeout limits)?
- [ ] Should processing be split across multiple Lambda invocations?
- [ ] Caching strategy for static assets (icons, CSS)?

## Maintenance
- [ ] How to handle game updates that change ability IDs?
- [ ] Process for updating set data when new sets are added?
- [ ] Notification system if weekly scan fails?
- [ ] Logging and monitoring strategy?
