
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


def guardar_bronze(df: pd.DataFrame, nombre: str, fuente: str) -> Path:


    settings.ensure_dirs()
    df_bronze = df.copy()
    df_bronze["_fuente"] = fuente
    df_bronze["_fecha_ingesta"] = datetime.now(timezone.utc).isoformat()

    destino = Path(settings.bronze_dir) / f"{nombre}.csv"
    df_bronze.to_csv(destino, index=False)
    logger.info("Bronze guardado: %s (%s registros)", destino, len(df_bronze))
    return destino


def cargar_bronze(nombre: str) -> pd.DataFrame:
    origen = Path(settings.bronze_dir) / f"{nombre}.csv"
    return pd.read_csv(origen)
