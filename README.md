# Fitbit to Garmin Data Converter

This tool converts Fitbit weight data to Garmin Connect format and uploads it directly via the Garmin Connect API.

## Why This Tool Exists

When migrating from Fitbit to Garmin, the official Garmin CSV uploader has several limitations:
- It often doesn't work reliably
- It only supports one measurement per day
- It doesn't capture the timestamp of measurements

This tool solves these problems by using the Garmin Connect API to upload data with full timestamp precision, allowing multiple measurements per day.

Created with Sculptor by Imbue.

## Setup

```bash
uv sync
```

The `garminconnect` package is installed in editable mode from `third-party/python-garminconnect`, so changes to that code are picked up automatically.

## Usage

### Convert to CSV (legacy)

```bash
uv run python fitbit_garmin_converter/cli.py convert-weight \
    tests/test_data \
    --output-file /tmp/weight_data.csv
```

### Upload directly to Garmin Connect

```bash
uv run python fitbit_garmin_converter/cli.py upload-to-garmin \
    tests/test_data \
    --unit lbs \
    --timezone-name America/Los_Angeles \
    --limit 10
```

The timezone defaults to `America/Los_Angeles`. Other common options:
- `America/New_York` (Eastern)
- `America/Chicago` (Central)
- `America/Denver` (Mountain)
- `Europe/London`, `Asia/Tokyo`, etc.

Set credentials via environment variables or you'll be prompted:
```bash
export GARMIN_EMAIL="your@email.com"
export GARMIN_PASSWORD="yourpassword"
```

## Testing

```bash
uv run pytest
```

## Updating the python-garminconnect Subtree

The `third-party/python-garminconnect` directory is maintained as a git subtree, which means the code is committed directly into this repository while maintaining a connection to the upstream repository.

To pull updates from upstream:
```bash
git subtree pull --prefix=third-party/python-garminconnect https://github.com/cyberjunky/python-garminconnect.git main --squash
```

To push changes back to upstream (if you have permissions):
```bash
git subtree push --prefix=third-party/python-garminconnect <url> <branch>
```