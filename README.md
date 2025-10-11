Thad's Sculpture to convert Fitbit data to a Garmin format.

Created with Sculptor by Imbue.

## Setup

```bash
uv sync
```

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
    --timezone-name America/Los_Angeles
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