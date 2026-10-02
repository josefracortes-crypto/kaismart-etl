"""Ejecuta el pipeline ETL completo."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kaismart_etl.pipeline import run_etl  # noqa: E402

if __name__ == "__main__":
    resultados = run_etl()
    for nombre, df in resultados.items():
        print(f"{nombre}: {df.shape}")
