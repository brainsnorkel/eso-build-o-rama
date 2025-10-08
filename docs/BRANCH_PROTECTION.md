# Branch Protection Setup

## Overview

This guide explains how to enforce the deployment readiness check as a required status check before merging to `main`.

## GitHub Actions Workflow

The `.github/workflows/deployment-check.yml` workflow automatically runs when:

- **Pull Requests** are opened against `main` or `develop`
- **Pushes** are made to `develop` or feature/bugfix branches
- **Manual triggers** via workflow_dispatch

### What It Does

1. ✅ Checks out the code
2. ✅ Sets up Python environment
3. ✅ Installs dependencies (including BeautifulSoup4)
4. ✅ Generates a test build (Aetherian Archive)
5. ✅ Runs `scripts/deployment_check.py`
6. ✅ Comments on PR with results
7. ✅ Uploads artifacts if check fails

### Exit Behavior

- **Pass** (exit 0): Green checkmark ✅, PR can be merged
- **Fail** (exit 1): Red X ❌, PR cannot be merged (if branch protection enabled)

## Enabling Branch Protection

### Step 1: Go to Repository Settings

1. Navigate to your repository on GitHub
2. Click **Settings** tab
3. Click **Branches** in left sidebar

### Step 2: Add Branch Protection Rule

1. Click **Add branch protection rule**
2. Enter branch name pattern: `main`

### Step 3: Configure Protection Rules

Enable the following:

#### Required Status Checks
- ✅ **Require status checks to pass before merging**
- ✅ **Require branches to be up to date before merging**
- Search for and select: **`Validate Generated Site`** (the deployment-check job name)

#### Other Recommended Settings
- ✅ **Require a pull request before merging**
  - Require approvals: 0 (or 1 if you want manual review)
- ✅ **Do not allow bypassing the above settings** (optional, prevents admin bypass)

#### Optional Settings
- ⬜ **Require linear history** (keeps clean git history)
- ⬜ **Include administrators** (applies rules to repo admins too)

### Step 4: Save Changes

Click **Create** or **Save changes**

## Testing the Setup

### Test 1: Create a PR with Failing Checks

```bash
# Introduce an intentional error
echo "broken" > output-dev/index.html

# Commit and push
git checkout -b test/failing-check
git add output-dev/index.html
git commit -m "Test: Intentional failure"
git push origin test/failing-check

# Create PR via GitHub UI
# Expected: ❌ Red X, comment says check failed
```

### Test 2: Create a PR with Passing Checks

```bash
# Generate valid build
python3 -m src.eso_build_o_rama.main --trial-id 1

# Commit and push
git checkout -b test/passing-check
git add output-dev/
git commit -m "Test: Valid build"
git push origin test/passing-check

# Create PR via GitHub UI
# Expected: ✅ Green checkmark, comment says ready to merge
```

## Local Pre-Push Hook (Optional)

For additional safety, add a local git hook to run checks before pushing:

### Create Hook File

```bash
cat > .git/hooks/pre-push << 'EOF'
#!/bin/bash

echo "Running deployment check before push..."

# Run the check on develop output
if [ -d "output-dev" ]; then
    python3 scripts/deployment_check.py output-dev
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Deployment check failed!"
        echo "Fix issues before pushing or use --no-verify to skip"
        exit 1
    fi
fi

echo "✅ Deployment check passed"
EOF

chmod +x .git/hooks/pre-push
```

### Usage

The hook runs automatically before every `git push`:

```bash
# Normal push - runs check
git push origin develop

# Skip check if needed (not recommended)
git push origin develop --no-verify
```

## Troubleshooting

### "Status check not found"

**Problem**: GitHub can't find the "Validate Generated Site" check.

**Solution**: 
1. Push a commit to trigger the workflow once
2. Wait for it to complete
3. The check will now appear in branch protection settings

### "Check is required but not present"

**Problem**: Old commits don't have the check.

**Solution**:
1. Merge latest changes to your branch
2. Or temporarily disable "Require branches to be up to date"

### "Check always fails on PR"

**Problem**: Secrets not available to PR from forks.

**Solution**: 
- `ESO_LOGS_CLIENT_ID` and `ESO_LOGS_CLIENT_SECRET` must be set in repository secrets
- For fork PRs, you may need to manually approve workflow runs

## Workflow Customization

### Skip Check for Certain Files

Edit `.github/workflows/deployment-check.yml`:

```yaml
on:
  pull_request:
    branches:
      - main
    paths-ignore:
      - 'docs/**'
      - 'README.md'
      - '*.md'
```

### Run on Different Trials

Change the test build command:

```yaml
- name: Generate test build
  run: |
    # Test with multiple trials
    python -m src.eso_build_o_rama.main --trial-id 1
    python -m src.eso_build_o_rama.main --trial-id 5
    python -m src.eso_build_o_rama.main --trial-id 12
```

### Add More Checks

Add steps before the deployment check:

```yaml
- name: Run linter
  run: |
    python -m pylint src/

- name: Run unit tests
  run: |
    python -m pytest tests/
```

## Enforcement Levels

### Level 1: Informational Only
- ✅ Workflow runs on PR
- ⬜ Branch protection disabled
- Result: Checks run but don't block merge

### Level 2: Soft Enforcement
- ✅ Workflow runs on PR  
- ✅ Branch protection enabled
- ⬜ "Include administrators" unchecked
- Result: Blocks merge for non-admins

### Level 3: Hard Enforcement (Recommended)
- ✅ Workflow runs on PR
- ✅ Branch protection enabled
- ✅ "Include administrators" checked
- ✅ "Do not allow bypassing" enabled
- Result: Blocks all merges until checks pass

## Best Practices

1. **Start with Level 1** (informational) to test the workflow
2. **Move to Level 2** once stable
3. **Add manual approval** for production deploys
4. **Use secrets** for API credentials (never commit them)
5. **Test locally first** with `python scripts/deployment_check.py output-dev`
6. **Review PR comments** for detailed failure info
7. **Keep checks fast** (< 5 minutes) for better developer experience

## Support

For issues with branch protection:
- GitHub Docs: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches
- Workflow Syntax: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions

