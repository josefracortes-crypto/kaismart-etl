
from __future__ import annotations

from pathlib import Path

import pandas as pd

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


def _resumen_logistico_por_pedido(df_logistica: pd.DataFrame) -> pd.DataFrame:

    df = df_logistica.sort_values("fecha_evento")
    agg = df.groupby("pedido_id").agg(
        cantidad_eventos=("evento_id", "count"),
        estado_actual=("estado_evento", "last"),
        fecha_primer_evento=("fecha_evento", "min"),
        fecha_ultimo_evento=("fecha_evento", "max"),
        transportadora=("transportadora", "first"),
        ciudad_destino=("ciudad_destino", "first"),
        tiempo_total_horas=("tiempo_etapa_horas", "sum"),
        costo_envio=("costo_envio", "max"),
        tuvo_incidencia=("incidencia", lambda s: (s != "SIN INCIDENCIA").any()),
    )
    agg["dias_ciclo_logistico"] = (
        agg["fecha_ultimo_evento"] - agg["fecha_primer_evento"]
    ).dt.total_seconds() / 86400
    return agg.reset_index()


def construir_gold_pedidos(
    df_ventas: pd.DataFrame, df_logistica: pd.DataFrame
) -> tuple[pd.DataFrame, dict]:

    resumen_logistico = _resumen_logistico_por_pedido(df_logistica)

    df_gold = df_ventas.merge(resumen_logistico, on="pedido_id", how="left", indicator=True)

    reporte = {
        "pedidos_ventas": df_ventas["pedido_id"].nunique(),
        "pedidos_con_logistica": int((df_gold["_merge"] == "both").sum()),
        "pedidos_sin_eventos_logisticos": int((df_gold["_merge"] == "left_only").sum()),
    }
    pedidos_venta_unicos = set(df_ventas["pedido_id"])
    pedidos_logistica_unicos = set(df_logistica["pedido_id"])
    reporte["eventos_logisticos_sin_venta_asociada"] = len(
        pedidos_logistica_unicos - pedidos_venta_unicos
    )

    df_gold = df_gold.drop(columns=["_merge"])
    return df_gold.reset_index(drop=True), reporte


def construir_marts(df_gold_pedidos: pd.DataFrame) -> dict[str, pd.DataFrame]:

    marts: dict[str, pd.DataFrame] = {}

    marts["ventas_por_ciudad_categoria"] = (
        df_gold_pedidos.groupby(["ciudad", "categoria"])["valor_neto"]
        .sum()
        .reset_index()
        .sort_values("valor_neto", ascending=False)
    )

    if "estado_actual" in df_gold_pedidos.columns:
        marts["pedidos_por_estado_logistico"] = (
            df_gold_pedidos["estado_actual"].value_counts().rename_axis("estado_actual").reset_index(name="pedidos")
        )

    if "transportadora" in df_gold_pedidos.columns:
        marts["kpis_por_transportadora"] = (
            df_gold_pedidos.groupby("transportadora")
            .agg(
                pedidos=("pedido_id", "nunique"),
                costo_envio_promedio=("costo_envio", "mean"),
                dias_ciclo_promedio=("dias_ciclo_logistico", "mean"),
                pct_con_incidencia=("tuvo_incidencia", "mean"),
            )
            .round(2)
            .reset_index()
        )

    return marts


def guardar_gold(df: pd.DataFrame, nombre: str) -> Path:
    settings.ensure_dirs()
    destino = Path(settings.gold_dir) / f"{nombre}.csv"
    df.to_csv(destino, index=False)
    logger.info("Gold guardado: %s (%s registros)", destino, len(df))
    return destino
