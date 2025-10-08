# Local Pre-Merge Enforcement

## Overview

This project uses **local git hooks** to enforce deployment checks before merging to `main`, rather than GitHub Actions. This gives you faster feedback and works offline.

## ✅ What's Set Up

### 1. Git Pre-Push Hook (`.git/hooks/pre-push`)

**Automatically runs** when you push to `main`:
- Detects push to main branch
- Runs deployment check on `output-dev/`
- Blocks push if checks fail
- Shows detailed error messages

### 2. Pre-Merge Check Script (`scripts/pre-merge-check.sh`)

**Run manually** before merging:
```bash
./scripts/pre-merge-check.sh output-dev
```

Features:
- Generates test build if needed
- Runs full deployment validation
- Shows clear pass/fail status
- Provides merge commands on success

### 3. Cursor AI Rules (`.cursorrules`)

**Reminds Cursor** to run checks before merging to main. Cursor will see this file and reference it when working with the codebase.

## 🚀 Usage

### Method 1: Automatic (Recommended)

The pre-push hook runs automatically:

```bash
# Make changes on develop
git checkout develop
git add .
git commit -m "My changes"

# Merge to main
git checkout main
git merge develop

# Push to main - hook runs automatically!
git push origin main
```

If checks fail, the push is blocked:
```
❌ Deployment check FAILED!
Please fix the issues before pushing to main.
To bypass this check (not recommended), use: git push --no-verify
```

### Method 2: Manual Check Before Merge

Run the check before merging:

```bash
# On your feature/develop branch
./scripts/pre-merge-check.sh output-dev

# If it passes:
✅ ALL CHECKS PASSED
You can safely merge to main:
  git checkout main
  git merge develop
  git push origin main
```

### Method 3: Ask Cursor

When using Cursor AI, simply say:
- "Check if I can merge to main"
- "Run the pre-merge check"
- "Validate before merging"

Cursor will see `.cursorrules` and know to run `./scripts/pre-merge-check.sh`

## 🔍 What Gets Checked

Every check validates:

✅ **Check 0**: Home page loads
✅ **Check 1**: Trials have build information  
✅ **Check 2**: Trial pages have ≥1 boss and ≥1 build
✅ **Check 3**: Build pages have:
  - Best player name (not "Unknown")
  - Mundus stone populated (not "Unknown")
  - No missing ability icons

## ⚠️ Bypassing Checks (Emergency Only)

If you absolutely need to push without checks:

```bash
# Bypass pre-push hook
git push origin main --no-verify

# NOT RECOMMENDED - Only use in emergencies!
```

**When to bypass:**
- Critical hotfix needed immediately
- Checks are broken (false positives)
- You've manually verified everything works

**After bypassing:**
- Fix the issues ASAP
- Create a bugfix branch
- Re-run checks to verify

## 🔧 Troubleshooting

### "Permission denied" Error

Make scripts executable:
```bash
chmod +x .git/hooks/pre-push
chmod +x scripts/pre-merge-check.sh
```

### "output-dev directory not found"

Generate test build first:
```bash
python3 -m src.eso_build_o_rama.main --trial-id 1
```

Or let the script generate it:
```bash
./scripts/pre-merge-check.sh output-dev
# (it will prompt to generate)
```

### Hook Not Running

Check if hook exists and is executable:
```bash
ls -la .git/hooks/pre-push
# Should show: -rwxr-xr-x (executable)

# If not executable:
chmod +x .git/hooks/pre-push
```

### Checks Keep Failing

Run with verbose output to see details:
```bash
python3 scripts/deployment_check.py output-dev
```

Common issues:
- Old builds in output-dev (regenerate: `python3 -m src.eso_build_o_rama.main --trial-id 1`)
- Missing mundus data (check logs from generation)
- Corrupted HTML (delete output-dev and regenerate)

## 📝 Workflow Examples

### Standard Feature Development

```bash
# 1. Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/my-feature

# 2. Make changes and commit
git add .
git commit -m "Add my feature"
git push origin feature/my-feature

# 3. Merge to develop (no checks needed)
git checkout develop
git merge feature/my-feature
git push origin develop

# 4. When ready for production...
./scripts/pre-merge-check.sh output-dev

# 5. If checks pass, merge to main
git checkout main
git pull origin main
git merge develop

# 6. Push to main (hook runs automatically)
git push origin main
```

### Quick Bugfix

```bash
# 1. Create bugfix from develop
git checkout develop
git checkout -b bugfix/fix-issue

# 2. Fix and commit
git add .
git commit -m "Fix issue"

# 3. Merge to develop
git checkout develop
git merge bugfix/fix-issue
git push origin develop

# 4. Run pre-merge check
./scripts/pre-merge-check.sh output-dev

# 5. Merge to main if passing
git checkout main
git merge develop
git push origin main  # Hook validates!
```

## 🎯 Best Practices

1. **Always run checks before merging to main** - Either manually or let the hook do it
2. **Test locally first** - Generate builds and browse them at http://localhost:8080
3. **Don't bypass hooks** - Only use `--no-verify` in true emergencies
4. **Fix issues immediately** - Don't accumulate failed checks
5. **Keep develop stable** - Merge to develop frequently, to main carefully

## 🔄 Comparison: Local vs GitHub Actions

**Local Enforcement (Current)**:
- ✅ Faster feedback (runs instantly)
- ✅ Works offline
- ✅ No GitHub Actions minutes used
- ✅ Easier to bypass (if needed)
- ⚠️  Relies on developer discipline

**GitHub Actions (Disabled)**:
- ⏱️  Slower feedback (waits for CI)
- 🌐 Requires internet
- 💰 Uses GitHub Actions minutes
- 🔒 Harder to bypass (good for teams)
- ✅ Enforced server-side

## 📚 Related Documentation

- **Deployment Check Script**: `scripts/README.md`
- **GitHub Actions Setup**: `docs/BRANCH_PROTECTION.md` (if you want to re-enable)
- **Enforcement Setup**: `ENFORCEMENT_SETUP.md` (GitHub Actions version)

## 🆘 Support

If you encounter issues:
1. Check this document first
2. Run checks manually to see detailed errors
3. Verify git hooks are installed and executable
4. Check Cursor's output for any prompts about the check

---

**Status**: ✅ Local enforcement active, GitHub Actions disabled
