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
            data = pd.read_json(file)
            all_data.append(data)
        except Exception as e:
            typer.echo(f"Error reading {file}: {e}")
            raise typer.Exit(1)
    
    df = pd.concat(all_data, ignore_index=True)
    
    # Validate required columns exist
    required_cols = ['date', 'weight', 'bmi']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        typer.echo(f"Error: Missing required columns: {missing_cols}")
        raise typer.Exit(1)
    
    # Add Fat column (optional)
    df['Fat'] = df['fat'] if 'fat' in df.columns else 0
    
    output_df = df[['date', 'weight', 'bmi', 'Fat']].rename(columns={
        'date': 'Date', 'weight': 'Weight', 'bmi': 'BMI'
    })
    
    output_df.to_csv(output_file, index=False)
    typer.echo(f"Converted {len(df)} records to {output_file}")

if __name__ == "__main__":
    app()