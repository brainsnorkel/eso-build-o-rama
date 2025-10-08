# Enforcement Setup Checklist

## ✅ Step 1: Code Deployed (COMPLETE)

The deployment check workflow is now live on `main`:
- ✅ `scripts/deployment_check.py` - Validation script
- ✅ `.github/workflows/deployment-check.yml` - GitHub Actions workflow
- ✅ `docs/BRANCH_PROTECTION.md` - Comprehensive guide

## 🔧 Step 2: Enable Branch Protection (ACTION REQUIRED)

**You must complete this step in the GitHub UI to enforce the checks.**

### Quick Setup (5 minutes)

1. **Go to Repository Settings**
   - Navigate to: https://github.com/brainsnorkel/eso-build-o-rama/settings/branches
   - Or: Repository → Settings → Branches (left sidebar)

2. **Click "Add branch protection rule"**

3. **Configure the Rule**

   **Branch name pattern:**
   ```
   main
   ```

   **Enable these settings:**
   
   ✅ **Require status checks to pass before merging**
   - ✅ Check: "Require branches to be up to date before merging"
   - Search for: `Validate Generated Site`
   - Click to add it to required checks
   
   ✅ **Require a pull request before merging**
   - Set "Required approvals": `0` (or `1` if you want manual review)
   - ✅ Check: "Dismiss stale pull request approvals when new commits are pushed"
   
   ⬜ **Require conversation resolution before merging** (optional)
   
   ⬜ **Require linear history** (optional, keeps git clean)
   
   ✅ **Include administrators** (RECOMMENDED - applies rules to repo owners too)
   
   ✅ **Do not allow bypassing the above settings** (RECOMMENDED - strict enforcement)

4. **Click "Create" or "Save changes"**

## ⚠️ Important Notes

### First-Time Setup

The workflow needs to run at least once before GitHub can recognize it as a status check:

1. Create a test branch and PR:
   ```bash
   git checkout develop
   git checkout -b test/enforcement-check
   git push origin test/enforcement-check
   ```

2. Open a PR against `main` via GitHub UI

3. Wait for the "Validate Generated Site" check to appear

4. Now you can add it to branch protection rules (Step 2 above)

### What Happens After Enforcement

**On every PR to main:**
1. GitHub Actions automatically runs
2. Generates a test build (Aetherian Archive)
3. Runs `scripts/deployment_check.py`
4. Posts comment on PR:
   - ✅ "All checks passed! Ready to merge" (if passing)
   - ❌ "Deployment check failed" (if failing)
5. PR shows green ✅ or red ❌ checkmark
6. **Merge button disabled if checks fail**

## 🧪 Step 3: Test the Enforcement (RECOMMENDED)

### Test 1: Passing Check

```bash
# Create a clean test PR
git checkout develop
git pull origin develop
git checkout -b test/passing-deployment-check
echo "# Test PR" >> TEST.md
git add TEST.md
git commit -m "Test: Verify deployment check passes"
git push origin test/passing-deployment-check
```

**Open PR on GitHub → Expected result:**
- ✅ Green checkmark
- ✅ Comment: "All checks passed!"
- ✅ Merge button enabled

### Test 2: Failing Check (Optional)

```bash
# Create a PR that will fail validation
git checkout develop
git checkout -b test/failing-deployment-check
echo "broken" > output/index.html
git add output/index.html
git commit -m "Test: Intentional failure"
git push origin test/failing-deployment-check
```

**Open PR on GitHub → Expected result:**
- ❌ Red X
- ❌ Comment: "Deployment check failed"
- ❌ Merge button disabled (if branch protection enabled)

## 📋 Verification Checklist

After setup, verify these items:

- [ ] Branch protection rule exists for `main`
- [ ] "Validate Generated Site" is listed as required check
- [ ] Test PR shows the check running
- [ ] PR comment appears after check completes
- [ ] Merge button is disabled when check fails
- [ ] Merge button is enabled when check passes
- [ ] Admins cannot bypass (if "Include administrators" enabled)

## 🔍 Troubleshooting

### "Can't find 'Validate Generated Site' check"

**Problem:** The check hasn't run yet, so GitHub doesn't know about it.

**Solution:**
1. Create and push any branch
2. Open a PR to `main`
3. Wait for workflow to complete
4. The check will now appear in branch protection settings

### "Check is always skipped"

**Problem:** Workflow may have path filters or conditions.

**Solution:** Check `.github/workflows/deployment-check.yml` for any `paths:` or `if:` conditions.

### "Secrets not found error"

**Problem:** `ESO_LOGS_CLIENT_ID` and `ESO_LOGS_CLIENT_SECRET` not set.

**Solution:**
1. Go to Settings → Secrets and variables → Actions
2. Add repository secrets:
   - `ESO_LOGS_CLIENT_ID`
   - `ESO_LOGS_CLIENT_SECRET`

### "Check fails but I can still merge"

**Problem:** Branch protection not enabled or configured incorrectly.

**Solution:** Re-check Step 2 above, ensure:
- Rule is for `main` branch
- "Require status checks to pass" is checked
- "Validate Generated Site" is in the required checks list
- Rule is saved

## 🎯 Success Criteria

You'll know it's working when:

1. ✅ Every PR to `main` shows "Validate Generated Site" check
2. ✅ PR gets automated comment with check results
3. ✅ Failed checks prevent merging
4. ✅ Passed checks allow merging
5. ✅ Local test: `python scripts/deployment_check.py output-dev` works

## 📚 Additional Resources

- **Full Documentation**: `docs/BRANCH_PROTECTION.md`
- **Script Usage**: `scripts/README.md`
- **GitHub Docs**: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches

## 🚀 Next Steps After Enforcement

Once enforcement is working:

1. **Update CHANGELOG.md** with deployment check feature
2. **Add badge to README.md** showing workflow status
3. **Consider adding more checks** (linting, tests, etc.)
4. **Monitor for false positives** and adjust validation rules

## Support

If you encounter issues:
1. Check workflow runs: https://github.com/brainsnorkel/eso-build-o-rama/actions
2. Review logs from failed checks
3. Test locally: `python scripts/deployment_check.py output-dev`
4. Refer to `docs/BRANCH_PROTECTION.md` for detailed troubleshooting

---

**Status**: ✅ Code deployed, ⏳ Branch protection setup required

