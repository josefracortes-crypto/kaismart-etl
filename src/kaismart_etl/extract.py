"""Extraccion de datos desde las dos fuentes (Partes 1 y 2 del ejercicio).

- ``extract_ventas``: conecta a MySQL, consulta la tabla ``ventas`` completa,
  la guarda en ``df_ventas`` y cierra la conexion correctamente.
- ``extract_logistica``: lee el archivo Excel de eventos logisticos y lo
  guarda en ``df_logistica``.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import text

from .config import settings
from .db import get_mysql_engine
from .logging_config import get_logger

logger = get_logger(__name__)


def extract_ventas(tabla: str | None = None) -> pd.DataFrame:
    """Extrae todos los registros de la tabla ``ventas`` en un DataFrame.

    Abre la conexion, ejecuta la consulta, y SIEMPRE cierra la conexion
    (incluso si ocurre un error), usando un bloque try/finally.
    """
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
    """Lee el archivo Excel de eventos logisticos y lo retorna como DataFrame."""
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
    """Imprime shape, columns, head() y una muestra aleatoria (requerido en
    las Partes 1 y 2 para comprobar la extraccion)."""
    print(f"\n{'=' * 70}\nComprobacion de extraccion: {nombre}\n{'=' * 70}")
    print(f"Shape: {df.shape}")
    print(f"\nColumnas ({len(df.columns)}):\n{list(df.columns)}")
    print("\nPrimeros 5 registros (head):")
    print(df.head())
    print(f"\nMuestra aleatoria de {n_muestra} registros:")
    print(df.sample(n=min(n_muestra, len(df)), random_state=42))
