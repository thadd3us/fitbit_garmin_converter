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
        data = pd.read_json(file)
        all_data.append(data)
    
    df = pd.concat(all_data, ignore_index=True)
    df['Fat'] = df.get('fat', 0)
    output_df = df[['date', 'weight', 'bmi', 'Fat']].rename(columns={
        'date': 'Date', 'weight': 'Weight', 'bmi': 'BMI'
    })
    
    output_df.to_csv(output_file, index=False)
    typer.echo(f"Converted {len(df)} records to {output_file}")

if __name__ == "__main__":
    app()