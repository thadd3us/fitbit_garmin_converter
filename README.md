Thad's Sculpture to convert Fitbit data to a Garmin format.

Created with Sculptor by Imbue.

```
uv run pytest
```

```
uv run python fitbit_garmin_converter/cli.py \
    tests/test_data \
    --output-file /tmp/weight_data.csv
```