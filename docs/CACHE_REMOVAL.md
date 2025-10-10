# Cache System Removal

## Date: 2025-10-11

## Decision

The entire caching system has been removed from ESO Build-O-Rama to simplify the codebase and ensure data freshness.

## Rationale

1. **Complexity**: The caching system added significant complexity across multiple modules
2. **Stale Data Issues**: Schema changes in cached data caused "Invalid table data structure" errors
3. **Maintenance Burden**: Required manual `--clear-cache` operations after code updates
4. **Fresh Data Priority**: For a daily-updated site showing current meta, fresh API data is more valuable than cache performance
5. **Rate Limiting Sufficient**: The 2-second rate limiting between API requests provides adequate performance

## What Was Removed

### Files Deleted
- `src/eso_build_o_rama/cache_manager.py` - Cache manager module
- `cache/` - Entire cache directory with subdirectories (reports/, tables/, buffs/, rankings/)
- `docs/CACHE_ANALYSIS.md` - Cache analysis documentation
- `docs/cache_system.md` - Cache system documentation
- `docs/cache_improvements_summary.md` - Cache improvements summary
- `docs/cache_effectiveness_test.md` - Cache testing documentation  
- `docs/AUTOMATIC_CACHE_INVALIDATION.md` - Auto-invalidation feature doc (was in progress)

### Code Changes

**`api_client.py`**:
- Removed `CacheManager` import
- Removed `cache_manager` parameter from `__init__()`
- Removed `use_cache` parameter from all methods (`get_zones`, `get_top_logs`, `get_report`, `get_report_table`)
- Removed all cache key creation logic
- Removed all cache check blocks (`if use_cache and self.cache_manager:`)
- Removed all cache save blocks (`if self.cache_manager: self.cache_manager.save_cached_response()`)

**`trial_scanner.py`**:
- Removed `cache_manager` parameter from `__init__()`
- Removed cache_manager pass-through to `ESOLogsAPIClient`
- Removed cache invalidation error handling (was in progress, now unnecessary)

**`main.py`**:
- Removed `CacheManager` import
- Removed `use_cache` and `clear_cache` parameters from `ESOBuildORM.__init__()`
- Removed cache manager instantiation
- Removed `cache_stats` variable and all usage
- Removed command-line arguments: `--use-cache`, `--no-cache`, `--clear-cache`, `--cache-stats`
- Removed cache statistics display logic
- Removed cache performance logging

**`data_store.py`**:
- Removed `cache_stats` parameter from `save_trial_builds()`
- Removed `cache_stats` from builds JSON data structure
- Removed `cache_stats` from trial metadata

**`data_parser.py`**:
- Reverted schema error to return empty list instead of raising ValueError

**.gitignore**:
- Removed cache/ directory entries

**`templates/home.html`**:
- Removed "About This Data" card (content now in dedicated About page)

## Impact

### Positive
- ✅ **Simpler codebase**: ~300 lines of cache-related code removed
- ✅ **No stale data**: Always fetches fresh data from API
- ✅ **No manual cache clearing**: No more `--clear-cache` needed after updates
- ✅ **Easier debugging**: Fewer moving parts to troubleshoot
- ✅ **Always current**: Ensures users see the latest meta immediately

### Considerations
- ⚠️ **Longer execution time**: Every run fetches all data from API (no cache hits)
- ⚠️ **More API calls**: Increased API usage (mitigated by rate limiting)
- ⚠️ **Network dependency**: No offline operation capability

### Performance Impact

**Before (with cache)**:
- First run: ~5-10 minutes (all API calls)
- Subsequent runs: ~30-60 seconds (mostly cache hits)

**After (without cache)**:
- Every run: ~5-10 minutes (all API calls)
- Consistent, predictable performance

**Mitigation**:
- Rate limiting (2s between requests) prevents API abuse
- GitHub Actions runs one trial at a time (spread throughout the day)
- Local development can use small test runs (`--trial-id 1`)

## Testing

After removal, verify:

```bash
# Test single trial generation
python3 -m src.eso_build_o_rama.main --trial-id 1

# Verify no cache-related errors
# Verify fresh data is fetched
# Verify HTML pages generate correctly
```

## Migration Notes

For users/deployments:

1. **No action required** - cache directory can be safely deleted
2. **Faster first page load** - no need to wait for cache warmup
3. **Command-line changes**: Remove any `--cache` flags from scripts/workflows

## Future Considerations

If performance becomes an issue, alternatives to consider:

1. **In-memory caching**: Session-only cache (cleared between runs)
2. **Selective caching**: Only cache immutable data (zones, old reports)
3. **Database**: Use SQLite for persistent, queryable storage
4. **CDN**: Cache at HTTP level (Cloudflare already does this for production)

For now, the simplicity and data freshness benefits outweigh the performance cost.

