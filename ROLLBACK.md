# Rollback Procedure: Update Versioning Migration

## When to Use

If the update versioning migration (U48 path prefix, root router, etc.) causes issues and the site needs to be restored to the previous flat structure.

## Rollback Tag

```
pre-u48-migration
```

This tag marks the last commit before any migration changes were applied. The site at this tag is the flat structure with all content at the root level and GitHub Actions running on schedule.

## Rollback Steps

### 1. Reset to pre-migration state

```bash
git checkout main
git reset --hard pre-u48-migration
```

### 2. Re-enable GitHub Actions schedule

The migration disables the scheduled workflows. After rollback, verify the schedule triggers are present in `.github/workflows/generate-builds.yml`:

```yaml
on:
  schedule:
    - cron: '0,40 0-23/2 * * *'
    - cron: '20 1-23/2 * * *'
```

These should already be present in the pre-migration code.

### 3. Force push to restore

```bash
git push --force origin main
```

### 4. Push the rollback tag (if not already pushed)

```bash
git push origin pre-u48-migration
```

### 5. Verify site restoration

- [ ] Visit `esobuild.com` — should load the flat home page directly (no redirect)
- [ ] Visit `esobuild.com/builds.json` — should return build data at root
- [ ] Check GitHub Actions tab — scheduled runs should resume within 40 minutes
- [ ] Wait for one scheduled run to complete and verify it deploys successfully

## Notes

- The force push rewrites main branch history. All migration commits will be removed.
- If other branches were created from post-migration main, they may need rebasing.
- The rollback tag itself is preserved and can be used again if needed.
