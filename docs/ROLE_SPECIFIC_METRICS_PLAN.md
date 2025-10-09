# Plan: Accurate Role-Specific Metrics (DPS, HPS, CPM)

## Overview

This plan outlines how to implement accurate role-specific performance metrics:
- **DPS**: Damage Per Second (for DPS players)
- **HPS**: Healing Per Second (for healers) 
- **CPM**: Casts Per Minute (for tanks)

## Current State Analysis

### ✅ What's Working
- DPS calculation from DamageDone table is accurate
- Role detection is working (dps/healer/tank classification)
- Template updates are in place to show role-specific metrics
- Number formatting (K/M suffixes) is implemented

### ❌ What Needs Implementation
- **HPS**: Currently placeholder - needs Healing table integration
- **CPM**: Not implemented - needs casts frequency calculation for tanks
- **Data merging**: Need to combine multiple API table responses

---

## Implementation Plan

### Phase 1: Accurate HPS for Healers

#### 1.1 API Data Requirements
**Tables needed:**
- `DamageDone` table (for gear, abilities, roles)
- `Healing` table (for HPS data)
- `Summary` table (for player details/roles)

#### 1.2 HPS Calculation Formula
```python
# From Healing table:
effective_healing = entry.get('total', 0)        # Actual healing done
overheal = entry.get('overheal', 0)              # Wasted healing
active_time_ms = entry.get('activeTime', 1)      # Active time in milliseconds

# Total healing output (including overheal)
total_healing = effective_healing + overheal

# HPS calculation
hps = (total_healing / active_time_ms) * 1000
```

#### 1.3 Implementation Steps
1. **Modify `trial_scanner.py`** to fetch Healing table
2. **Update `data_parser.py`** to extract and merge healing data
3. **Test with known healer builds**

---

### Phase 2: CPM for Tanks

#### 2.1 CPM Definition
**Casts Per Minute** should measure:
- **Total ability casts per minute**: All ability usage frequency
- **Active casting rate**: How frequently the tank is using abilities
- **Combat engagement**: Overall activity level in combat

#### 2.2 Data Sources for CPS
**Potential API tables:**
- `Casts` table - Track ability usage (taunts, interrupts)
- `DamageTaken` table - Track mitigation events
- `Buffs` table - Track defensive buff uptime

#### 2.3 CPM Calculation Strategy
```python
# Casts Per Minute = Total ability casts / fight duration in minutes
total_casts = sum(ability.get('total', 0) for ability in player_abilities)
fight_duration_minutes = fight_duration_ms / (1000 * 60)
cpm = total_casts / fight_duration_minutes

# Example:
# Tank used 120 abilities total in a 180-second (3-minute) fight
# CPM = 120 / 3 = 40 casts per minute
```

---

### Phase 3: Data Integration Architecture

#### 3.1 Multi-Table Data Flow
```
1. Fetch Summary table (roles, player details)
2. Fetch DamageDone table (DPS, gear, abilities)
3. Fetch Healing table (HPS data)
4. Fetch Casts table (CPS data for tanks)
5. Merge all data into PlayerBuild objects
```

#### 3.2 Performance Considerations
- **API calls per fight**: 4 tables × 12 reports × 8 bosses = 384 calls
- **Current**: 2 tables × 12 reports × 8 bosses = 192 calls
- **Increase**: 100% more API calls
- **Mitigation**: Caching, rate limiting, parallel requests

---

## Detailed Implementation Steps

### Step 1: HPS Implementation

#### 1.1 Update `trial_scanner.py`
```python
async def _process_single_fight(self, ...):
    # Existing calls
    summary_data = await self.api_client.get_report_table(...)
    damage_data = await self.api_client.get_report_table(...)
    
    # NEW: Fetch healing data
    healing_data = await self.api_client.get_report_table(
        report_code=report_code,
        start_time=fight_info.get('startTime'),
        end_time=fight_info.get('endTime'),
        data_type="Healing",
        include_combatant_info=False
    )
    
    # Pass to parser
    players = self.data_parser.parse_report_data(
        report_data=report_data,
        table_data=damage_data,
        fight_id=fight_id,
        player_details_data=summary_data,
        healing_data=healing_data  # NEW
    )
```

#### 1.2 Update `data_parser.py`
```python
def parse_report_data(
    self,
    report_data: Dict[str, Any],
    table_data: Any,
    fight_id: int,
    player_details_data: Any = None,
    healing_data: Any = None  # NEW
) -> List[PlayerBuild]:
    
    # Parse players from damage table (existing)
    players = self._parse_players_from_damage_table(...)
    
    # NEW: Extract healing data
    if healing_data:
        healing_lookup = self._extract_healing_data(healing_data)
        self._merge_healing_data(players, healing_lookup)
    
    return players

def _extract_healing_data(self, healing_data):
    """Extract healing metrics from Healing table."""
    healing_lookup = {}
    
    if hasattr(healing_data, 'report_data'):
        healing_table = healing_data.report_data.report.table
        entries = healing_table['data'].get('entries', [])
        
        for entry in entries:
            player_id = entry.get('id')
            if player_id:
                effective_healing = entry.get('total', 0)
                overheal = entry.get('overheal', 0)
                active_time_ms = entry.get('activeTime', 1)
                
                total_healing = effective_healing + overheal
                hps = (total_healing / active_time_ms) * 1000 if active_time_ms > 0 else 0
                
                healing_lookup[player_id] = hps
    
    return healing_lookup

def _merge_healing_data(self, players, healing_lookup):
    """Merge healing data into player objects."""
    for player in players:
        if player.player_id in healing_lookup:
            player.healing = healing_lookup[player.player_id]
```

### Step 2: CPS Implementation

#### 2.1 Update `trial_scanner.py` for CPS
```python
async def _process_single_fight(self, ...):
    # Existing calls
    summary_data = await self.api_client.get_report_table(...)
    damage_data = await self.api_client.get_report_table(...)
    healing_data = await self.api_client.get_report_table(...)
    
    # NEW: Fetch casts data for tank CPS
    casts_data = await self.api_client.get_report_table(
        report_code=report_code,
        start_time=fight_info.get('startTime'),
        end_time=fight_info.get('endTime'),
        data_type="Casts",
        include_combatant_info=False
    )
    
    # Pass to parser
    players = self.data_parser.parse_report_data(
        report_data=report_data,
        table_data=damage_data,
        fight_id=fight_id,
        player_details_data=summary_data,
        healing_data=healing_data,
        casts_data=casts_data  # NEW
    )
```

#### 2.2 CPM Calculation in `data_parser.py`
```python
def _extract_cpm_data(self, casts_data, fight_duration_minutes):
    """Extract CPM data from Casts table."""
    cpm_lookup = {}
    
    if hasattr(casts_data, 'report_data'):
        casts_table = casts_data.report_data.report.table
        entries = casts_table['data'].get('entries', [])
        
        for entry in entries:
            player_id = entry.get('id')
            if player_id:
                # Count total ability casts (all abilities)
                total_casts = 0
                for ability in entry.get('abilities', []):
                    total_casts += ability.get('total', 0)
                
                # Calculate CPM = total casts / fight duration in minutes
                cpm = total_casts / fight_duration_minutes if fight_duration_minutes > 0 else 0
                cpm_lookup[player_id] = cpm
    
    return cpm_lookup
```

### Step 3: Enhanced Model Methods

#### 3.1 Update `PlayerBuild.get_primary_metric()`
```python
def get_primary_metric(self) -> float:
    """Get role-appropriate performance metric."""
    if self.role.lower() == "healer" and self.healing > 0:
        return self.healing
    elif self.role.lower() == "tank" and self.crowd_control > 0:
        return self.crowd_control
    return self.dps

def get_primary_metric_name(self) -> str:
    """Get role-appropriate metric name."""
    if self.role.lower() == "healer" and self.healing > 0:
        return "HPS"
    elif self.role.lower() == "tank" and self.crowd_control > 0:
        return "CPS"
    return "DPS"
```

---

## Testing Strategy

### Phase 1 Testing: HPS
1. **Find a trial with known healers**
   ```bash
   # Dreadsail Reef (trial ID 60) typically has healers
   python3 -m src.eso_build_o_rama.main --trial-id 60
   ```

2. **Verify HPS values**
   - Check logs for "Fetched healing data"
   - Verify healer builds show HPS > 0
   - Typical HPS range: 100K-400K for trial healers

3. **Compare with ESO Logs**
   - Manually check a few reports on ESO Logs website
   - Verify our HPS matches their healing values

### Phase 2 Testing: CPS
1. **Find a trial with known tanks**
   ```bash
   # Any trial should have tanks
   python3 -m src.eso_build_o_rama.main --trial-id 18  # Aetherian Archive
   ```

2. **Verify CPM values**
   - Check logs for "Fetched casts data"
   - Verify tank builds show CPM > 0
   - Typical CPM range: 30-90 for active tanks

3. **Validate against ability usage**
   - Check that tanks with more active ability usage show higher CPM
   - Verify tanks with longer fights have proportionally higher total casts

### Phase 3 Testing: Integration
1. **Mixed role testing**
   - Generate builds for a full trial with all roles
   - Verify DPS shows DPS, healers show HPS, tanks show CPM

2. **Fallback testing**
   - Test with incomplete data (missing healing/casts tables)
   - Verify graceful fallback to DPS

---

## Performance Optimization

### API Call Optimization
1. **Parallel requests** where possible
2. **Smart caching** - cache tables separately
3. **Conditional fetching** - only fetch Healing table if healers detected
4. **Rate limiting** - maintain 2-second delay between requests

### Caching Strategy
```python
# Cache keys for different tables
summary_cache_key = f"table_{report_code}_Summary_True_{time}_{fights}"
damage_cache_key = f"table_{report_code}_DamageDone_True_{time}_{fights}"
healing_cache_key = f"table_{report_code}_Healing_False_{time}_{fights}"
casts_cache_key = f"table_{report_code}_Casts_False_{time}_{fights}"
```

### Memory Optimization
- Stream large table responses
- Clear unused data after parsing
- Use generators for large player lists

---

## Rollout Plan

### Phase 1: HPS Implementation (Week 1)
1. Implement Healing table fetching
2. Update data parser for HPS extraction
3. Test with known healer builds
4. Deploy to feature branch

### Phase 2: CPS Implementation (Week 2)
1. Implement Casts table fetching
2. Add CPS calculation logic
3. Test with known tank builds
4. Integrate with existing HPS code

### Phase 3: Integration & Testing (Week 3)
1. Full integration testing
2. Performance optimization
3. Fallback handling
4. Documentation updates

### Phase 4: Production Deployment (Week 4)
1. Deploy to develop branch
2. Run full trial scans
3. Monitor API usage
4. Merge to main branch

---

## Risk Mitigation

### API Rate Limiting
- **Risk**: 100% increase in API calls
- **Mitigation**: Implement exponential backoff, monitor rate limits

### Data Quality
- **Risk**: Missing or incomplete table data
- **Mitigation**: Graceful fallbacks, extensive logging

### Performance Impact
- **Risk**: 2-3x longer scan times
- **Mitigation**: Parallel requests, aggressive caching

### Backward Compatibility
- **Risk**: Breaking existing functionality
- **Mitigation**: Feature flags, gradual rollout

---

## Success Metrics

### Functional Metrics
- ✅ Healers show accurate HPS (100K-400K range)
- ✅ Tanks show meaningful CPM (30-90 range)
- ✅ DPS continues to show accurate DPS
- ✅ All builds display correct role-specific metrics

### Performance Metrics
- ✅ API calls complete within rate limits
- ✅ Scan times increase by <200% (target: <150%)
- ✅ Cache hit rate >80% on subsequent runs
- ✅ Zero data parsing errors

### User Experience Metrics
- ✅ Build pages load correctly with new metrics
- ✅ Tables display role-appropriate labels
- ✅ Mobile responsiveness maintained
- ✅ No broken links or missing data

---

## Future Enhancements

### Advanced Tank Metrics
- **Damage mitigation per second** (from DamageTaken table)
- **Block/taunt uptime percentage**
- **Survival metrics** (damage taken vs healing received)
- **Ability efficiency** (casts per second vs damage output)

### Advanced Healer Metrics
- **Overheal percentage** display
- **Healing efficiency** (effective vs total healing)
- **Ability breakdown** (top healing spells)

### Advanced DPS Metrics
- **Damage breakdown** by damage type
- **Critical hit percentage**
- **Ability rotation efficiency**

---

## Conclusion

This plan provides a comprehensive roadmap for implementing accurate role-specific metrics. The phased approach allows for incremental testing and validation while minimizing risk. The key success factors are:

1. **Proper API table integration** (Healing, Casts tables)
2. **Accurate metric calculations** (HPS, CPS formulas)
3. **Performance optimization** (caching, rate limiting)
4. **Robust fallback handling** (graceful degradation)

Implementation should begin with HPS (most straightforward) followed by CPS (more complex) with thorough testing at each phase.
