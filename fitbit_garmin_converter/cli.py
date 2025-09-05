from pathlib import Path
import typer
import pandas as pd

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

if __name__ == "__main__":
    app()