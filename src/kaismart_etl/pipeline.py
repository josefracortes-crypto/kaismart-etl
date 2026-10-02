
from __future__ import annotations

import pandas as pd

from .config import settings
from .extract import extract_logistica, extract_ventas
from .logging_config import get_logger
from .transform import bronze, gold, silver

logger = get_logger(__name__)


def run_etl() -> dict[str, pd.DataFrame]:

    settings.ensure_dirs()
    logger.info("=== INICIO pipeline ETL Kaismart ===")

    # --- Extraccion (Partes 1 y 2) ---
    df_ventas = extract_ventas()
    df_logistica = extract_logistica()

    # --- Bronze (crudo + metadatos de trazabilidad) ---
    bronze.guardar_bronze(df_ventas, "ventas", fuente="mysql.clientes.ventas")
    bronze.guardar_bronze(df_logistica, "logistica", fuente="kaismart_eventos_logisticos.xlsx")

    # --- Silver (limpieza y estandarizacion independiente por fuente, Parte 7) ---
    df_ventas_transformado, reporte_ventas = silver.limpiar_ventas(df_ventas)
    df_logistica_transformado, reporte_logistica = silver.limpiar_logistica(df_logistica)
    logger.info("Reporte limpieza ventas: %s", reporte_ventas)
    logger.info("Reporte limpieza logistica: %s", reporte_logistica)

    df_ventas_transformado.to_csv(settings.silver_dir / "ventas_transformado.csv", index=False)
    df_logistica_transformado.to_csv(
       settings.silver_dir / "logistica_transformado.csv", index=False
    )

    # --- Gold (integracion por pedido_id + datamarts) ---
    df_gold_pedidos, reporte_gold = gold.construir_gold_pedidos(
        df_ventas_transformado, df_logistica_transformado
    )
    logger.info("Reporte integracion gold: %s", reporte_gold)
    gold.guardar_gold(df_gold_pedidos, "pedidos_360")

    marts = gold.construir_marts(df_gold_pedidos)
    for nombre_mart, df_mart in marts.items():
        gold.guardar_gold(df_mart, nombre_mart)

    logger.info("=== FIN pipeline ETL Kaismart ===")

    resultado = {
        "df_ventas": df_ventas,
        "df_logistica": df_logistica,
        "df_ventas_transformado": df_ventas_transformado,
        "df_logistica_transformado": df_logistica_transformado,
        "df_gold_pedidos": df_gold_pedidos,
        **{f"mart_{k}": v for k, v in marts.items()},
    }
    return resultado


if __name__ == "__main__":
    run_etl()
