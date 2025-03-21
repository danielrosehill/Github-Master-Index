# Automated Repository Index Updates

This repository is configured to automatically update itself on a daily basis using GitHub Actions. This ensures that the repository index, timeline, and category listings always reflect your latest GitHub repositories without requiring manual intervention.

## How It Works

1. **Scheduled Updates**: A GitHub Actions workflow runs automatically at 2:00 AM UTC every day.
2. **Data Collection**: The workflow fetches your latest repository data from the GitHub API.
3. **Index Generation**: It generates updated JSON and CSV exports, timeline, and category listings.
4. **Automatic Commit**: Changes are automatically committed and pushed back to the repository.

## GitHub Actions Workflow

The automation is handled by a GitHub Actions workflow defined in `.github/workflows/update-index.yml`. This workflow:

- Runs on a daily schedule (2:00 AM UTC)
- Can also be triggered manually through the GitHub Actions interface
- Uses the repository's GitHub token for authentication
- Installs all required dependencies
- Executes the `run_all.py` script with the `--push` flag to commit changes

## Manual Triggers

If you need to update the index outside of the scheduled time:

1. Go to the "Actions" tab in your GitHub repository
2. Select the "Update GitHub Repository Index" workflow
3. Click "Run workflow" on the right side
4. Select the branch you want to run it on (usually `main` or `master`)
5. Click the green "Run workflow" button

## Environment Variables

The workflow uses the following environment variables:

- `GITHUB_TOKEN`: Automatically provided by GitHub Actions, used for authentication and pushing changes
- `GITHUB_PAT`: Set to the same value as `GITHUB_TOKEN`, used by the repo-fetcher script

## Troubleshooting

If the automated updates aren't working as expected:

1. Check the "Actions" tab in your GitHub repository to view workflow run logs
2. Ensure your repository has the necessary permissions set for GitHub Actions
3. Verify that the workflow file (`.github/workflows/update-index.yml`) is present in your repository
4. Check that the required dependencies are listed in `requirements.txt`

## Modifying the Schedule

To change when the updates occur, edit the cron expression in the `.github/workflows/update-index.yml` file:

```yaml
on:
  schedule:
    # Format: minute hour day-of-month month day-of-week
    - cron: '0 2 * * *'  # Currently set to 2:00 AM UTC daily
```

For example, to run at 4:30 PM UTC every Monday and Thursday:
```yaml
- cron: '30 16 * * 1,4'
```
