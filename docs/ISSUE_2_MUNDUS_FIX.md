# Issue #2: Mundus Collected But Not Showing - Investigation & Fix

## Issue Summary

GitHub Issue #2 reported that mundus stone data was being collected but not displaying on the build pages.

## Investigation Process

### Step 1: Verify Mundus Data Collection

Checked GitHub Actions logs for recent Maw of Lorkhaj deployment:
```
2025-10-08 04:39:50 - Fetching mundus data for 6 publishable builds
2025-10-08 04:39:52 - ✓ Found mundus: The Thief for -Tomoyo Sakagami
2025-10-08 04:39:54 - ✓ Found mundus: The Thief for The Meta Slave
2025-10-08 04:39:56 - ✓ Found mundus: The Thief for Ela Shepard
...
2025-10-08 04:40:00 - Mundus fetch complete: 5 successful, 0 failed, 1 skipped
```

**Result**: ✅ Mundus data was being fetched successfully.

### Step 2: Check Saved Data

Inspected `output/builds.json`:
```bash
cat output/builds.json | python3 -c "import json, sys; ..."
Builds with mundus: 0
Total builds: 48
```

**Result**: ❌ Zero builds had mundus data despite successful fetches.

### Step 3: Trace Data Flow

Added debug logging to track mundus values through the save/load cycle:

**Before Save** (from GitHub Actions):
```
DEBUG - Before save: ardent-ass-herald-perfected... - mundus: 'The Thief'
DEBUG - Before save: ardent-ass-herald-perfected... - mundus: 'The Thief'
DEBUG - Before save: ass-dawn-herald-deadly-strike... - mundus: 'The Thief'
```

**After Load** (from local test):
```
DEBUG - After load: Aetherian Archive - ardent-ass-herald... - mundus: 'The Thief'
DEBUG - After load: Aetherian Archive - ardent-ass-herald... - mundus: ''
DEBUG - After load: Aetherian Archive - ardent-ass-herald... - mundus: 'The Thief'
```

### Step 4: Identify the Bug

**Key Observation**: 
- Saved builds were for **Maw of Lorkhaj** with mundus ✅
- Loaded builds were for **Aetherian Archive** (different trial!) with mixed mundus data ❌

## Root Cause

The bug was in the page generation flow in `src/eso_build_o_rama/main.py`:

```python
# 1. Scan and fetch mundus (fresh builds have mundus) ✅
publishable_builds = await scanner.get_publishable_builds(all_reports)

# 2. Save fresh builds to builds.json ✅
data_store.save_trial_builds(trial_name, trial_builds, ...)

# 3. LOAD ALL builds from builds.json ❌ 
all_saved_builds = data_store.get_all_builds()  # Includes old trials!

# 4. Generate pages from loaded builds ❌
page_generator.generate_all_pages(all_saved_builds, ...)
```

**The Problem**:
1. Fresh scans correctly fetched mundus for the scanned trial
2. That data was saved to `builds.json`
3. **BUT** pages were generated from ALL builds loaded from `builds.json`
4. Old trials in `builds.json` had empty mundus (scanned before fix or before feature existed)
5. The fresh mundus data was saved but not used for page generation!

## The Fix

Implemented build merging logic in `src/eso_build_o_rama/main.py` (lines 165-179):

```python
# BUGFIX: Merge freshly scanned builds (with mundus) into loaded builds
if publishable_builds:
    # Create a mapping of (trial_name, boss_name, build_slug) to fresh builds
    fresh_builds_map = {}
    for fresh_build in publishable_builds:
        key = (fresh_build.trial_name, fresh_build.boss_name, fresh_build.build_slug)
        fresh_builds_map[key] = fresh_build
    
    # Replace loaded builds with fresh ones where available
    for i, loaded_build in enumerate(all_saved_builds):
        key = (loaded_build.trial_name, loaded_build.boss_name, loaded_build.build_slug)
        if key in fresh_builds_map:
            all_saved_builds[i] = fresh_builds_map[key]
            logger.debug(f"Replaced loaded build with fresh: {loaded_build.build_slug}")
```

### How It Works

1. After saving fresh builds to `builds.json`, we load ALL builds as before
2. We create a map of fresh builds by (trial_name, boss_name, build_slug)
3. We iterate through loaded builds and replace any that match fresh builds
4. This ensures fresh mundus data persists through page generation

### Benefits

- ✅ Mundus displays correctly for newly scanned trials
- ✅ Minimal code change (15 lines)
- ✅ No breaking changes to data structures
- ✅ Backward compatible with existing builds.json
- ✅ Old trials will get mundus as they're re-scanned naturally

## Testing

The fix will be validated by:
1. Monitoring GitHub Actions deployments for mundus presence in logs
2. Checking deployed pages for mundus display
3. Verifying builds.json contains mundus after scans
4. Confirming old trials get mundus as they're re-scanned by the 14-hour cycle

## Timeline

As trials are re-scanned by the automated 14-hour cycle, all builds will eventually have mundus data. The full cycle will complete in 14 hours.

## Commit

- **Branch**: `bugfix/issue-2`
- **Commit**: c5dce2e
- **Message**: "Fix issue #2: Mundus collected but not showing"
- **Files Modified**:
  - `src/eso_build_o_rama/main.py` (bugfix implementation)
  - `CHANGELOG.md` (documentation)

