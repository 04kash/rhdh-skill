# Google Sheets API Setup

The skill accesses the RHDH schedule Google Sheet using your existing Google account via `gcloud`.

## Setup (one-time)

**Step 1: Install gcloud** (skip if already installed)

Follow [Install the Google Cloud CLI](https://cloud.google.com/sdk/docs/install) for your OS. Examples:

- **Linux**: package manager (`apt`/`yum`/`dnf`), [Snap](https://cloud.google.com/sdk/docs/downloads-snap), or tarball — install so `gcloud` is on your `PATH`.
- **macOS**: [Installer pkg](https://cloud.google.com/sdk/docs/install-sdk#mac), [Homebrew cask](https://formulae.brew.sh/cask/google-cloud-sdk), or tarball — install so `gcloud` is on your `PATH`.

The scripts invoke `gcloud` only via `PATH`. If `which gcloud` fails, fix your install or shell configuration before retrying.

**Step 2: Authenticate with Google Drive access**

```bash
gcloud auth login --enable-gdrive-access
```

This opens a browser window. Sign in with the Google account that has access to the RHDH schedule sheet.

**Step 3: Verify**

```bash
python scripts/check_gsheets.py
```

Expected output:
```
✓ gcloud auth token available
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `gcloud not found` / `gcloud not on PATH` | Install the SDK (see step 1) so `gcloud` is on your `PATH` |
| `No active gcloud account` | Run `gcloud auth login --enable-gdrive-access` |
| `403 Forbidden` when fetching sheet | Sign in with an account that has Viewer access to the sheet |
| Token expired | Run `gcloud auth login --enable-gdrive-access` again |
