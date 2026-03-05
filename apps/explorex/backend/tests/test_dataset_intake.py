import pytest
import pandas as pd
import os
from . import dataset_intake

@pytest.fixture
def temp_csv(tmp_path):
    p = tmp_path / "test.csv"
    df = pd.DataFrame({
        "A": [1, 2, 3, 4, 5],
        "B": ["x", "y", "z", "x", "y"],
        "C": [1.0, None, None, None, 5.0] # >50% nulls
    })
    df.to_csv(p, index=False)
    return str(p)

def test_validate_csv(temp_csv):
    profile = dataset_intake.validate(temp_csv)
    
    assert profile.row_count == 5
    assert profile.column_count == 3
    assert profile.filename == "test.csv"
    assert len(profile.columns) == 3
    
    # Check column B (cardinality 3: x, y, z)
    col_b = next(c for c in profile.columns if c.name == "B")
    assert col_b.cardinality == 3
    assert len(col_b.sample_values) == 3
    
    # Check quality warning for column C
    assert any("Column 'C' has >50% null values" in w for w in profile.quality_warnings)

def test_validate_max_rows(temp_csv, monkeypatch):
    monkeypatch.setenv("MAX_DATASET_ROWS", "2")
    with pytest.raises(ValueError, match="Dataset too large"):
        dataset_intake.validate(temp_csv)

def test_unsupported_format(tmp_path):
    p = tmp_path / "test.txt"
    p.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported file format"):
        dataset_intake.validate(str(p))

def test_invalid_csv(tmp_path):
    p = tmp_path / "invalid.csv"
    p.write_text("A,B\n1,2,3") # Malformed
    # Pandas sometimes just handles malformed CSVs by skipping rows or filling NaNs, 
    # but let's test that it at least completes or fails predictably.
    profile = dataset_intake.validate(str(p))
    assert profile.row_count > 0
