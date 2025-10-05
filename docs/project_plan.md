# ESO Build-O-Rama - Project Plan

## Overview
Weekly automated scan of ESO Logs to identify and publish top-performing trial builds as static web pages.

## Architecture

### Components
1. **Data Collection Module** - Fetches logs from ESO Logs API
2. **Build Analysis Module** - Processes player data, identifies subclasses and common builds
3. **Page Generation Module** - Creates static HTML pages for builds
4. **Deployment Module** - Publishes to static hosting (S3/Cloudflare)
5. **Scheduler** - Weekly Lambda/Worker execution

### Data Flow
```
ESO Logs API → Data Collection → Build Analysis → Page Generation → Static Hosting
                                                         ↓
                                              Build State Storage
                                              (track published builds)
```

## Implementation Phases

### Phase 1: Core Data Collection
- Set up Python project structure
- Implement ESO Logs API client
- Fetch top 5 logs per trial
- Extract player build data (gear, abilities, mundus, CP)
- Filter out incomplete builds

### Phase 2: Build Analysis
- Port/implement subclass detection from ESO-Log-Build-and-Buff-Summary
- Calculate set piece distribution across bars
- Generate build slugs
- Identify common builds (5+ occurrences)
- Select highest DPS example for each common build

### Phase 3: Static Site Generation
- Design responsive HTML/CSS templates
- Implement ability icon display with UESP links
- Create gear table generators
- Build index page with trial/boss organization
- Add proper credits and attributions

### Phase 4: Deployment Infrastructure
- Set up GitHub Actions for weekly execution
- Configure GitHub Pages for static site hosting
- Implement weekly scheduling via GitHub Actions
- Set up test branch (gh-pages-test) and production (gh-pages)
- Configure custom domain (optional)

### Phase 5: Testing & Polish
- Create comprehensive test suite
- Document testing procedures
- Implement error handling and logging
- Performance optimization
- Documentation completion

## Technology Stack

### Backend
- **Language**: Python 3.9+
- **API Client**: requests or httpx
- **Scheduling**: AWS Lambda (with EventBridge) or Cloudflare Workers (with Cron Triggers)
- **Data Processing**: pandas (optional, for analysis)

### Frontend
- **Static HTML/CSS/JS** - minimal JavaScript for better performance
- **Icons**: From esoskillbarbuilder or cached locally
- **Styling**: Modern, responsive CSS (consider Tailwind CSS)

### Infrastructure
- **Hosting**: GitHub Pages (preferred per requirements)
- **Domain**: TBD (custom domain can be added to GitHub Pages)
- **CI/CD**: GitHub Actions
- **Secrets**: GitHub Secrets for API credentials

## Key Design Decisions

### Build Identification
- **Build Slug Format**: `{update}-{sorted-subclasses}-{sorted-sets}`
- Example: `u48-ass-ardent-herald-ansuuls-torment-deadly-strike`
- Use abbreviated subclass names for compact URLs

### Deduplication Strategy
- Store published builds in a JSON/database with update + slug as key
- Only publish new builds per game update
- Track last scan date to avoid re-processing

### Performance Optimization
- Cache ESO Logs API responses during development
- Minimize API calls (batch requests where possible)
- Generate only changed/new pages
- Use CDN for asset delivery

## Open Questions & Research Needed

See `open_questions.md` for detailed list of items requiring investigation.

## Success Criteria
- [ ] Successfully fetches top 5 logs for all trials weekly
- [ ] Accurately identifies subclasses and common builds
- [ ] Generates clean, accessible static pages
- [ ] Deploys automatically on schedule
- [ ] Runs within cost budget (<$5/month)
- [ ] Includes comprehensive tests
- [ ] Well-documented for maintenance

## Timeline Estimate
- Phase 1: 1-2 weeks
- Phase 2: 1-2 weeks  
- Phase 3: 1 week
- Phase 4: 1 week
- Phase 5: Ongoing

**Total**: 4-6 weeks to MVP, ongoing refinements
