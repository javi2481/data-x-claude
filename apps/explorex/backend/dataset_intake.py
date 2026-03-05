import pandas as pd
import hashlib
import os
from typing import List, Any, Optional
from pydantic import BaseModel

class ColumnProfile(BaseModel):
    name: str
    dtype: str
    null_pct: float
    cardinality: int
    sample_values: List[Any]

class DatasetProfile(BaseModel):
    dataset_hash: str
    filename: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    quality_warnings: List[str]

def _get_file_hash(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate(file_path: str) -> DatasetProfile:
    """
    Valida un archivo CSV o Excel y devuelve un perfil del dataset.
    """
    max_rows = int(os.getenv("MAX_DATASET_ROWS", "100000"))
    
    # Cargar dataset según extensión
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in [".xlsx", ".xls"]:
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    row_count = len(df)
    if row_count > max_rows:
        raise ValueError(f"Dataset too large: {row_count} rows. Maximum allowed is {max_rows}.")

    dataset_hash = _get_file_hash(file_path)
    column_profiles = []
    quality_warnings = []

    for col_name in df.columns:
        col_data = df[col_name]
        null_pct = col_data.isnull().mean()
        
        if null_pct > 0.5:
            quality_warnings.append(f"Column '{col_name}' has >50% null values ({null_pct:.1%}).")

        # Cardinalidad y valores de ejemplo (max 5)
        unique_vals = col_data.dropna().unique()
        cardinality = len(unique_vals)
        sample_values = unique_vals[:5].tolist()
        
        # Asegurar que los valores de ejemplo sean serializables
        sample_values = [str(v) if not isinstance(v, (int, float, str, bool)) and v is not None else v for v in sample_values]

        column_profiles.append(ColumnProfile(
            name=col_name,
            dtype=str(col_data.dtype),
            null_pct=float(null_pct),
            cardinality=int(cardinality),
            sample_values=sample_values
        ))

    return DatasetProfile(
        dataset_hash=dataset_hash,
        filename=os.path.basename(file_path),
        row_count=row_count,
        column_count=len(df.columns),
        columns=column_profiles,
        quality_warnings=quality_warnings
    )
