
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from .config import settings
from .db import get_mysql_engine
from .logging_config import get_logger

logger = get_logger(__name__)


def extract_ventas(tabla: str | None = None) -> pd.DataFrame:

    tabla = tabla or settings.mysql.tabla_ventas
    engine = get_mysql_engine()
    connection = engine.connect()
    try:
        logger.info("Consultando todos los registros de la tabla '%s'...", tabla)
        query = text(f"SELECT * FROM {tabla}")
        df_ventas = pd.read_sql(query, con=connection)
        logger.info("Extraccion de ventas completada: %s registros", len(df_ventas))
        return df_ventas
    finally:
        connection.close()
        engine.dispose()
        logger.info("Conexion a MySQL cerrada correctamente.")


def extract_logistica(excel_path: str | Path | None = None) -> pd.DataFrame:

    excel_path = Path(excel_path) if excel_path else settings.excel_logistica_path
    if not excel_path.exists():
        raise FileNotFoundError(
            f"No se encontro el archivo de eventos logisticos en: {excel_path}. "
            "Ejecute scripts/generate_mock_data.py para generar un archivo de "
            "prueba, o copie el archivo real en esa ruta."
        )
    logger.info("Leyendo archivo Excel: %s", excel_path)
    df_logistica = pd.read_excel(excel_path, engine="openpyxl")
    logger.info(
        "Extraccion de eventos logisticos completada: %s registros", len(df_logistica)
    )
    return df_logistica


def mostrar_comprobacion(df: pd.DataFrame, nombre: str, n_muestra: int = 5) -> None:

    print(f"\n{'=' * 70}\nComprobacion de extraccion: {nombre}\n{'=' * 70}")
    print(f"Shape: {df.shape}")
    print(f"\nColumnas ({len(df.columns)}):\n{list(df.columns)}")
    print("\nPrimeros 5 registros (head):")
    print(df.head())
    print(f"\nMuestra aleatoria de {n_muestra} registros:")
    print(df.sample(n=min(n_muestra, len(df)), random_state=42))
