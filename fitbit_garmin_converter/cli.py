from pathlib import Path
import typer
import pandas as pd
import os
from datetime import datetime, timezone
from getpass import getpass

app = typer.Typer()

@app.command()
def convert_weight(
    input_dir: Path = typer.Argument(..., help="Directory containing weight JSON files"),
    glob_pattern: str = typer.Option("weight*.json", help="Glob pattern for weight files"),
    output_file: Path = typer.Option("weight_data.csv", help="Output CSV file path"),
):
    """Convert Fitbit weight data to Garmin Connect CSV format."""
    files = list(input_dir.rglob(glob_pattern))
    if not files:
        typer.echo(f"No files found matching {glob_pattern} in {input_dir}")
        raise typer.Exit(1)
    
    all_data = []
    for file in files:
        try:
            data = pd.read_json(file, convert_dates=False)
            all_data.append(data)
        except Exception as e:
            typer.echo(f"Error reading {file}: {e}")
            raise typer.Exit(1)
    
    df = pd.concat(all_data, ignore_index=True)
    
    # Validate required columns exist
    required_cols = ['date', 'time', 'weight', 'bmi']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Missing required columns: {missing_cols}")
        raise typer.Exit(1)
    
    # Combine date and time into datetime for processing
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%m/%d/%y %H:%M:%S')
    
    # Extract date only for grouping
    df['date_only'] = df['datetime'].dt.date
    
    # Group by date and take minimum weight for each day
    agg_dict = {
        'weight': 'min',
        'bmi': 'first',  # Take first BMI value for the day (could also use corresponding BMI to min weight)
    }
    
    # Only add fat aggregation if the column exists
    if 'fat' in df.columns:
        agg_dict['fat'] = 'first'
    
    daily_min = df.groupby('date_only').agg(agg_dict).reset_index()
    
    # Format date as YYYY-MM-DD for Garmin
    daily_min['Date'] = pd.to_datetime(daily_min['date_only']).dt.strftime('%Y-%m-%d')
    
    # Add Fat column (optional)
    daily_min['Fat'] = daily_min['fat'] if 'fat' in df.columns else 0
    
    # Sort by date
    daily_min = daily_min.sort_values('date_only')
    
    output_df = daily_min[['Date', 'weight', 'bmi', 'Fat']].rename(columns={
        'weight': 'Weight', 'bmi': 'BMI'
    })
    
    output_df.to_csv(output_file, index=False)
    typer.echo(f"Converted {len(df)} records to {len(output_df)} daily records in {output_file}")

@app.command()
def upload_to_garmin(
    input_dir: Path = typer.Argument(..., help="Directory containing weight JSON files"),
    glob_pattern: str = typer.Option("weight*.json", help="Glob pattern for weight files"),
    unit: str = typer.Option("lbs", help="Weight unit (kg or lbs)"),
    dry_run: bool = typer.Option(False, help="Simulate upload without actually sending data"),
):
    """Upload Fitbit weight data directly to Garmin Connect via API."""

    try:
        from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError
    except ImportError as e:
        typer.echo(f"Error: Could not import garminconnect library: {e}")
        typer.echo("Please run 'uv sync' to install dependencies")
        raise typer.Exit(1)

    # Read and combine all weight data files
    files = list(input_dir.rglob(glob_pattern))
    if not files:
        typer.echo(f"No files found matching {glob_pattern} in {input_dir}")
        raise typer.Exit(1)

    all_data = []
    for file in files:
        try:
            data = pd.read_json(file, convert_dates=False)
            all_data.append(data)
        except Exception as e:
            typer.echo(f"Error reading {file}: {e}")
            raise typer.Exit(1)

    df = pd.concat(all_data, ignore_index=True)

    # Validate required columns
    required_cols = ['date', 'time', 'weight']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Missing required columns: {missing_cols}")
        raise typer.Exit(1)

    # Combine date and time into datetime
    df['datetime'] = pd.to_datetime(df['date'] + ' ' + df['time'], format='%m/%d/%y %H:%M:%S')

    # Sort by datetime
    df = df.sort_values('datetime')

    typer.echo(f"Found {len(df)} weight records to upload")

    if dry_run:
        typer.echo("\nDRY RUN MODE - No data will be uploaded")
        typer.echo("\nSample records to be uploaded:")
        for idx, row in df.head(5).iterrows():
            typer.echo(f"  {row['datetime']}: {row['weight']} {unit}")
        if len(df) > 5:
            typer.echo(f"  ... and {len(df) - 5} more records")
        return

    # Authenticate with Garmin
    typer.echo("\n🔐 Garmin Connect Authentication")
    typer.echo("=" * 50)

    # Configure token storage
    tokenstore = os.getenv("GARMINTOKENS", "~/.garminconnect")
    tokenstore_path = Path(tokenstore).expanduser()

    api = None

    # Try to login with stored tokens first
    try:
        typer.echo("Attempting to use saved authentication tokens...")
        api = Garmin()
        api.login(str(tokenstore_path))
        typer.echo("✅ Successfully logged in using saved tokens!")
    except (FileNotFoundError, GarminConnectAuthenticationError, GarminConnectConnectionError):
        typer.echo("No valid tokens found. Please login with credentials.")

        # Get credentials
        email = os.getenv("GARMIN_EMAIL")
        password = os.getenv("GARMIN_PASSWORD")

        if not email:
            email = typer.prompt("Login email")
        if not password:
            password = getpass("Enter password: ")

        try:
            typer.echo("Logging in with credentials...")
            api = Garmin(email=email, password=password, is_cn=False)
            api.login()

            # Save tokens
            api.garth.dump(str(tokenstore_path))
            typer.echo(f"✅ Tokens saved to: {tokenstore_path}")
        except GarminConnectAuthenticationError as e:
            typer.echo(f"❌ Authentication failed: {e}")
            raise typer.Exit(1)
        except Exception as e:
            typer.echo(f"❌ Login error: {e}")
            raise typer.Exit(1)

    if not api:
        typer.echo("❌ Failed to initialize Garmin API")
        raise typer.Exit(1)

    # Upload each weight record
    typer.echo(f"\n📤 Uploading {len(df)} weight records...")
    typer.echo("=" * 50)

    success_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        try:
            # Convert datetime to timezone-aware
            dt = row['datetime']
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

            # Format timestamp
            timestamp = dt.isoformat()

            weight_value = float(row['weight'])

            typer.echo(f"\n🔄 Uploading: {dt} - {weight_value} {unit}")
            typer.echo(f"   Timestamp: {timestamp}")

            # Upload weight
            result = api.add_weigh_in(
                weight=weight_value,
                unitKey=unit,
                timestamp=timestamp
            )

            typer.echo(f"   ✅ Success - API response: {result}")
            success_count += 1

        except Exception as e:
            error_count += 1
            typer.echo(f"   ❌ Error: {e}")
            typer.echo(f"   Error type: {type(e).__name__}")

            # Try to get more details from the exception
            if hasattr(e, 'response'):
                typer.echo(f"   HTTP Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
                try:
                    typer.echo(f"   Response body: {e.response.text[:200]}")
                except:
                    pass

            if error_count > 10:
                typer.echo("\nToo many errors, aborting upload")
                raise typer.Exit(1)

    typer.echo("\n" + "=" * 50)
    typer.echo(f"✅ Upload complete!")
    typer.echo(f"   Successfully uploaded: {success_count} records")
    if error_count > 0:
        typer.echo(f"   Failed: {error_count} records")

if __name__ == "__main__":
    app()