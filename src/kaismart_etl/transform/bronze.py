"""Capa Bronze: persiste los datos EXACTAMENTE como llegaron de la fuente,
solo agregando metadatos de trazabilidad de la ingesta. No se limpia nada aqui."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


def guardar_bronze(df: pd.DataFrame, nombre: str, fuente: str) -> Path:
    """Guarda una copia inmutable del DataFrame crudo en la capa Bronze.

    Agrega columnas de trazabilidad (_fuente, _fecha_ingesta) sin modificar
    ninguna columna original.
    """
    settings.ensure_dirs()
    df_bronze = df.copy()
    df_bronze["_fuente"] = fuente
    df_bronze["_fecha_ingesta"] = datetime.now(timezone.utc).isoformat()

    destino = Path(settings.bronze_dir) / f"{nombre}.xlsx"
    df_bronze.to_excel(destino, index=False)
    logger.info("Bronze guardado: %s (%s registros)", destino, len(df_bronze))
    return destino


def cargar_bronze(nombre: str) -> pd.DataFrame:
    origen = Path(settings.bronze_dir) / f"{nombre}.xlsx"
    return pd.read_excel(origen)
