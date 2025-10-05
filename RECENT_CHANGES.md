# Recent Changes - October 5, 2025

## API Rate Limiting Implementation ✅

### What Changed
Added comprehensive rate limiting to the ESO Logs API client to prevent hitting API limits during bulk operations.

### Features Added

1. **Automatic Rate Limiting**
   - Minimum delay between requests (default: 0.5 seconds)
   - Prevents rapid-fire API calls that trigger rate limits
   - Configurable per client instance

2. **Smart Retry Logic**
   - Automatically catches HTTP 429 (Too Many Requests) errors
   - Exponential backoff: 60s, 120s, 180s
   - Up to 3 retries before giving up
   - Logs retry attempts for debugging

3. **Zero Code Changes Required**
   - Existing code continues to work without modifications
   - Rate limiting is transparent to calling code
   - All API methods automatically protected

### Code Example

```python
# Default settings (conservative)
client = ESOLogsAPIClient()

# Custom settings for high-volume processing
client = ESOLogsAPIClient(
    min_request_delay=1.0,  # 1 second between requests
    max_retries=3,          # retry up to 3 times
    retry_delay=60.0        # start with 60s delay on rate limit
)
```

### Technical Details

**Modified File**: `src/eso_build_o_rama/api_client.py`

**New Methods**:
- `_wait_for_rate_limit()`: Enforces minimum delay between requests
- `_retry_on_rate_limit(func, *args, **kwargs)`: Wraps API calls with retry logic

**Protected Methods**:
- `get_zones()` - Get all available zones
- `get_top_logs()` - Fetch rankings for encounters
- `get_report()` - Get detailed report information
- `get_report_table()` - Get table data with combatant info

**Error Handling**:
- Catches `GraphQLClientHttpError` with HTTP 429 status
- Logs warnings on retry attempts
- Logs errors when max retries exceeded
- Re-raises other exceptions immediately

### Testing

Rate limiting was tested with consecutive API calls:
```bash
python test_rate_limit.py
```

Results:
- ✅ Automatic delay enforced between requests
- ✅ Rate limit errors detected and retry attempted
- ✅ Exponential backoff working correctly
- ✅ No unintended side effects on API responses

### Data Structure Updates

**File**: `data/trials.json`
- Removed `encounters` field (redundant with `trial_bosses.json`)
- Added Maw of Lorkhaj (ID: 5)
- Added Ossein Cage (ID: 19)

Encounter counts can now be computed on-demand from `trial_bosses.json`, eliminating data duplication.

### Bug Fixes

**File**: `src/eso_build_o_rama/trial_scanner.py`
- Fixed `close()` method to properly await async API client close
- Prevents "coroutine was never awaited" warnings

### Next Steps

1. **Wait for rate limit reset** (~10-15 minutes from last run)
2. **Test Sunspire script**: `python test_sunspire.py`
3. **Run full production scan** with rate limiting protection
4. **Monitor and adjust** rate limit settings based on real-world usage

### Impact

- **Reliability**: Prevents failed runs due to rate limiting
- **Automation**: Can now safely run scheduled jobs without manual intervention
- **Performance**: Optimized delays balance speed with API respect
- **Maintainability**: Centralized rate limiting logic, easy to adjust

---

**Previous Run Stats** (before rate limiting):
- ✅ Processed 6 trials successfully
- ✅ Generated 30 HTML files
- ❌ Hit rate limits after ~40 API calls

**Expected with Rate Limiting**:
- ✅ Process all 14 trials without errors
- ✅ Automatic recovery from transient rate limits
- ✅ Longer runtime but 100% reliability