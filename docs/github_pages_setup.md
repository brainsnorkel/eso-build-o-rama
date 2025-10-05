# GitHub Pages Setup

## Overview

This project uses GitHub Pages to host the generated build analysis site. The site is automatically updated weekly via GitHub Actions.

## Initial Setup

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click **Settings** → **Pages**
3. Under "Source", select:
   - **Branch**: `gh-pages`
   - **Folder**: `/ (root)`
4. Click **Save**

The site will be available at: `https://brainsnorkel.github.io/eso-build-o-rama/`

### 2. Configure Secrets

Add your ESO Logs API credentials as repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following secrets:
   - `ESOLOGS_ID`: Your ESO Logs client ID
   - `ESOLOGS_SECRET`: Your ESO Logs client secret

### 3. Manual Deployment

To manually deploy the current output:

```bash
# Generate the builds
python3 test_per_boss.py

# Switch to gh-pages branch
git checkout gh-pages

# Copy generated files
cp -r output/* .
cp -r static .

# Commit and push
git add .
git commit -m "Update builds - $(date +'%Y-%m-%d')"
git push origin gh-pages

# Switch back to main
git checkout main
```

## Automated Workflow

The GitHub Actions workflow (`.github/workflows/generate-builds.yml`) runs:

- **Weekly**: Every Sunday at 00:00 UTC
- **Manual**: Via the "Actions" tab → "Generate ESO Builds" → "Run workflow"

### Workflow Steps:

1. Checkout main branch
2. Install Python dependencies
3. Run `test_per_boss.py` to generate all trial pages
4. Checkout gh-pages branch
5. Copy generated HTML and static files
6. Commit and push to gh-pages

## Rate Limiting

The ESO Logs API has rate limits. The current configuration:

- **Parallel processing**: 3 trials at once
- **Reports per trial**: 10 top-ranked reports
- **Estimated API calls**: ~1,000-1,500 per run
- **Run time**: ~10-15 minutes

If you hit rate limits (HTTP 429), the workflow will:
- Process as many trials as possible before hitting the limit
- Deploy whatever was successfully generated
- Retry on the next scheduled run

## Monitoring

Check the workflow status:
1. Go to **Actions** tab
2. Click on "Generate ESO Builds"
3. View recent runs and logs

## Troubleshooting

### Site not updating
- Check the Actions tab for workflow errors
- Verify secrets are configured correctly
- Check gh-pages branch has the latest files

### Rate limit errors
- Reduce `max_reports` in `test_per_boss.py`
- Reduce `batch_size` from 3 to 2
- Add delays between API calls

### Missing trials
- Check the workflow logs for specific trial errors
- Some trials may have no recent ranked reports
