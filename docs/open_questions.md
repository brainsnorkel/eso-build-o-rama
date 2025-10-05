# Open Questions & Research Items

## ESO Logs API
- [ ] What is the exact API endpoint structure for fetching top logs?
- [ ] How to filter for public logs only?
- [ ] Rate limiting constraints and best practices?
- [ ] Authentication requirements (API key, OAuth, etc.)?
- [ ] What trials are currently active in the game?
- [ ] How to get the current game update version from the API?
- [ ] Data format for abilities, gear, and buffs in API responses?
- [ ] How to identify "blue CP" (Champion Points) from the API?

## Build Detection
- [ ] Review ESO-Log-Build-and-Buff-Summary subclass detection algorithm
- [ ] How are two-handed weapons counted (1 or 2 slots)?
- [ ] How to handle "weaponless" or special setups?
- [ ] What constitutes a "5-piece set" for mythic items or special sets?
- [ ] How to handle arena weapons (which can be front or back bar)?

## Data Sources & External Resources
- [ ] Best format to use from LibSets (XLSM vs Lua)?
- [ ] Can we programmatically access UESP ability URLs?
- [ ] Where to get official ESO ability icons?
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
