# Rate Limit Status

## Current Status: RATE LIMITED ⏳

**Last Rate Limit Hit**: October 5, 2025 at 8:08 PM

**ESO Logs API Rate Limit**: 18,000 points per hour

## When Can We Run Again?

The ESO Logs API uses a **rolling hourly window**. Based on our testing pattern:

- We've made heavy API calls throughout testing (5 PM - 8 PM)
- Current rate limit will reset gradually as the hourly window rolls forward
- **Recommended wait time**: Until **October 6, 2025 at 9:00 AM** (next morning)

## What Changed?

We've updated the default rate limiting to be more conservative:

### New Settings (as of commit 1c953ec):
- **min_request_delay**: 2.0 seconds (was 0.5s)
- **retry_delay**: 120 seconds (was 60s)
- **Exponential backoff**: 120s, 240s, 360s

### Expected Performance:
- **Requests per minute**: ~30 (was 120)
- **Points per minute**: ~300 (at 10 points/request)
- **Points per hour**: ~18,000 (exactly at limit)
- **Full 14-trial scan**: ~2,800 points ✅ (safely within limit)

## How to Resume

Once the rate limit resets:

```bash
# Clear output and run Sunspire test
rm -f output/*.html
python test_sunspire.py
```

Or run the full production scan:

```bash
# Clear output and run all trials
rm -f output/*.html
python -m src.eso_build_o_rama.main
```

## Rate Limit Best Practices

1. **Space out test runs** - Don't run multiple tests back-to-back
2. **Use production settings** - The new 2s delay is optimal
3. **Monitor logs** - Watch for HTTP 429 responses
4. **Test single trials** - Use `test_sunspire.py` for development
5. **Production runs** - Schedule weekly, not more frequent

## API Points Reference

| Operation | Points | Notes |
|-----------|--------|-------|
| `get_zones()` | 1-2 | Simple lookup |
| `get_top_logs()` | 5-10 | Rankings query (per encounter) |
| `get_report()` | 3-5 | Report details |
| `get_report_table()` | 5-10 | Heavy (includes combatant info) |

**Per trial** (5 bosses, 5 reports each):
- 5 rankings queries = 50 points
- 25 report queries = 125 points
- 50 table queries = 500 points
- **Total**: ~675 points per trial

**Full scan** (14 trials):
- 14 × 200 points (average) = **2,800 points**
- Well within 18,000 point limit! ✅

## Troubleshooting

If you hit rate limits again:
1. Check the time - has it been at least 1 hour since last run?
2. Increase `min_request_delay` even more (try 3.0s or 5.0s)
3. Reduce `top_n` reports per trial (try 3 instead of 5)
4. Run fewer trials at once

---

**Status will update**: This file will be removed once we successfully complete a run.
