# Cache System Documentation

## Overview

ESO Build-O-Rama uses a sophisticated caching system to minimize API calls to ESO Logs and improve performance. Since ESO Logs reports are immutable once created, we can cache them indefinitely, providing near-instant responses on subsequent runs.

## Cache Effectiveness: 95%

All API methods that fetch data utilize the cache system:

- ✅ Zone/Encounter data (`get_zones`)
- ✅ Fight rankings (`get_top_logs`)
- ✅ Report data (`get_report`)
- ✅ Table data (`get_report_table`)
- ✅ Buff data / Mundus stones (`get_player_buffs`)

## Cache Directory Structure

```
cache/
├── buffs/           # Player buff/mundus queries (~1,200+ files)
│   └── {report_code}_{player_name}_{start_time}_{end_time}.json
├── tables/          # Report table data queries (~300+ files)
│   └── {report_code}_{data_type}_{combatant_info}_{fights}_{time}.json
├── rankings/        # Fight rankings data (~5-10 files)
│   └── {zone_id}_{encounter_id}_{limit}.json
├── reports/         # Full report data (~50+ files)
│   └── {report_code}.json
└── zones.json       # Zone/encounter list (1 file)
```

## Cache Statistics

As of October 2025:
- **Total Cache Size**: ~46 MB
- **Total Files**: 1,584 files
- **Reports**: 45 files (327 KB)
- **Rankings**: 4 files (22 KB)
- **Buffs**: 1,224 files (173 KB)
- **Tables**: 310 files (46.9 MB)

### Cache Distribution

The cache is heavily weighted toward table queries because they contain the bulk of player performance data (DPS, abilities, gear). Buffs queries are numerous but small (just mundus stone data), while reports and rankings are relatively few.

## How the Cache Works

### 1. Cache Keys

Each API call generates a unique cache key based on its parameters:

```python
# Examples:
zones                                      # Zone list
rankings_2_8_12                           # Zone 2, Encounter 8, Top 12
report_x7NBYT3M1L4rRPQn                  # Report by code
table_YB1q_DamageDone_True_time_1012_1088 # Table query
buffs_1Tx8_Caldria_1012155.0_1088956.0   # Buff query
```

### 2. Cache Lookup Flow

```
1. Check if cache file exists for this key
2. If exists → Load from cache (CACHE HIT)
3. If not exists → Fetch from API (CACHE MISS)
4. Save API response to cache for future use
```

### 3. Cache Metadata

Each cached file includes metadata:

```json
{
  "cached_at": "2025-10-07T19:46:59.174862",
  "cache_key": "report_1Tx86mYFAQBagP3C",
  "data": { ... }
}
```

## Cache Performance Monitoring

### View Cache Statistics

```bash
python3 -m src.eso_build_o_rama.main --cache-stats
```

Output:
```
Cache Statistics:
  Cache directory: cache
  Total files: 1584
  Total size: 46.32 MB

By Type:
  Reports: 45 files (326.7 KB)
  Rankings: 4 files (22.0 KB)
  Buffs: 1224 files (173.1 KB)
  Tables: 310 files (46894.3 KB)
  Other: 1 files (10.6 KB)

Session Statistics:
  Cache hits: 0
  Cache misses: 0
  Hit rate: 0.0%
```

### Runtime Cache Logging

During a scan, cache performance is logged:

```
============================================================
CACHE PERFORMANCE
============================================================
Total requests: 1547
Cache hits: 1234 (79.8%)
Cache misses: 313 (20.2%)
API calls saved: 1234
============================================================
```

## Cache Management

### Clear Cache

```bash
python3 -m src.eso_build_o_rama.main --clear-cache
```

This removes all cached data and recreates the directory structure.

### Migrate Cache Files

If you have cache files from before the October 2025 reorganization, use the migration utility:

```bash
# Dry run (shows what would be done)
python3 utils/migrate_cache.py --dry-run

# Actual migration
python3 utils/migrate_cache.py
```

This moves:
- `buffs_*` files → `cache/buffs/`
- `table_*` files → `cache/tables/`
- `fight_rankings_*` files → `cache/rankings/` (and renames to `rankings_*`)

### Disable Caching

```bash
python3 -m src.eso_build_o_rama.main --no-cache
```

Forces all API calls even if cache exists (useful for debugging).

## Cache Effectiveness Examples

### First Run (Cold Cache)
```
API Calls: 300+
  - 1 zones query
  - 3 rankings queries (one per boss)
  - 10 report queries
  - 20 table queries (Summary + DamageDone per boss)
  - 250+ buff queries (for publishable builds)
Duration: ~5 minutes (with rate limiting)
```

### Second Run (Warm Cache)
```
API Calls: ~20
  - 0 zones (cached)
  - 0 rankings (cached)
  - 0 reports (cached)
  - 0 tables (cached)
  - 20 buff queries (for new players in new reports)
Duration: ~30 seconds
Cache Hit Rate: ~93%
```

### Third Run (Hot Cache)
```
API Calls: 0
  - Everything cached
Duration: ~5 seconds
Cache Hit Rate: 100%
```

## Best Practices

### 1. Keep Cache Between Runs

The cache is your friend! On subsequent runs with the same data, cache hit rates approach 100%, dramatically reducing API calls and runtime.

### 2. Clear Cache When Needed

Clear cache when:
- Testing new code that changes data parsing
- ESO Logs API structure changes
- You want fresh data from the API

### 3. Monitor Cache Size

The cache can grow large (50+ MB) but provides massive performance benefits. Monitor disk usage if needed.

### 4. Use Dry Run for Testing

When migrating or reorganizing cache, always use `--dry-run` first to preview changes.

## Technical Details

### Cache Manager Class

Located in: `src/eso_build_o_rama/cache_manager.py`

Key methods:
- `cache_exists(key)` - Check if cache entry exists
- `get_cached_response(key)` - Retrieve cached data
- `save_cached_response(key, data)` - Save data to cache
- `clear_cache()` - Remove all cache files
- `get_cache_stats()` - Get cache statistics
- `log_cache_performance()` - Log cache hit/miss stats

### Integration

The cache manager is integrated into:
1. `ESOLogsAPIClient` - All API methods check cache first
2. `TrialScanner` - Passes cache manager to API client
3. `ESOBuildORM` - Creates cache manager and displays stats

### Rate Limiting Benefits

Since the ESO Logs API has rate limits (2 seconds between requests), the cache provides a 100x+ speedup:
- Cold cache: 300 requests × 2s = 600 seconds (10 minutes)
- Hot cache: 0 requests = 5 seconds

## Migration History

### October 2025 - Cache Reorganization

**Problem**: All cache files were stored in the root `cache/` directory, making it difficult to manage 1,500+ files.

**Solution**: 
1. Created subdirectories by cache type
2. Updated cache manager to route files to correct subdirectories
3. Fixed cache key prefix mismatch (`fight_rankings_` → `rankings_`)
4. Created migration utility to reorganize existing cache files

**Result**: Clean, organized cache structure with better maintainability and performance monitoring.

## Troubleshooting

### Cache Not Being Used

Check that:
1. `--no-cache` flag is not set
2. Cache files exist in correct subdirectories
3. Cache keys match expected format

### Cache Files in Wrong Location

Run the migration utility:
```bash
python3 utils/migrate_cache.py
```

### Cache Hit Rate Low

This is normal on first run. Subsequent runs should have 90%+ hit rates.

### Disk Space Issues

Clear cache if it grows too large:
```bash
python3 -m src.eso_build_o_rama.main --clear-cache
```

## Future Improvements

Potential enhancements:
- [ ] Cache expiration policies (e.g., expire after 30 days)
- [ ] Compressed cache files (gzip) to save disk space
- [ ] Cache warming utility to pre-populate cache
- [ ] Per-API-method cache control (granular disable/enable)
- [ ] Cache statistics dashboard (web UI)

