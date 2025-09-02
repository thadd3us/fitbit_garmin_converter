import subprocess
from pathlib import Path

def test_convert_weight_cli(tmp_path, snapshot):
    output_file = tmp_path / "output.csv"
    test_data_dir = Path(__file__).parent / "test_data"
    
    result = subprocess.run([
        "python", "-m", "fitbit_garmin_converter.cli",
        str(test_data_dir), "--output-file", str(output_file)
    ], capture_output=True, text=True, cwd=Path(__file__).parent.parent)
    
    assert result.returncode == 0
    assert snapshot == output_file.read_text()