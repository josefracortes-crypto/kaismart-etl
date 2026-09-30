"""Estadisticos descriptivos y resumenes (Parte 5). No integra las fuentes."""
from __future__ import annotations

import pandas as pd


def resumen_numerico(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """count, mean, std, min, p25, mediana, p75, max para columnas numericas.

    Coacciona a numerico con errors="coerce" antes de describir: en el EDA
    inicial (Parte 5) algunas columnas monetarias aun llegan como texto
    (p.ej. costo_envio="$ 45.000"); esto permite dimensionar la variable
    igual, dejando la limpieza formal del formato para la capa Silver (Parte 7).
    """
    columnas = [c for c in columnas if c in df.columns]
    numerico = df[columnas].apply(pd.to_numeric, errors="coerce")
    desc = numerico.describe(percentiles=[0.25, 0.5, 0.75]).T
    desc = desc.rename(columns={"50%": "mediana", "25%": "p25", "75%": "p75"})
    return desc[["count", "mean", "std", "min", "p25", "mediana", "p75", "max"]]


def resumen_categorico(df: pd.DataFrame, columna: str, top: int = 20) -> pd.DataFrame:
    """Frecuencia absoluta y relativa de cada categoria de una columna."""
    conteo = df[columna].value_counts(dropna=False)
    pct = df[columna].value_counts(normalize=True, dropna=False) * 100
    out = pd.DataFrame({"conteo": conteo, "pct": pct.round(2)})
    out.index.name = columna
    return out.head(top).reset_index()


def categoria_mas_frecuente(df: pd.DataFrame, columna: str):
    moda = df[columna].mode(dropna=True)
    return moda.iloc[0] if not moda.empty else None


# ---------------------------------------------------------------------------
# Resumenes especificos solicitados para df_ventas
# ---------------------------------------------------------------------------
def resumen_ventas(df_ventas: pd.DataFrame) -> dict[str, pd.DataFrame]:
    resultados: dict[str, pd.DataFrame] = {}

    if "ciudad" in df_ventas:
        resultados["ventas_por_ciudad"] = resumen_categorico(df_ventas, "ciudad")
    if "canal" in df_ventas:
        resultados["ventas_por_canal"] = resumen_categorico(df_ventas, "canal")
    if "categoria" in df_ventas:
        resultados["ventas_por_categoria"] = resumen_categorico(df_ventas, "categoria")
    if "cantidad" in df_ventas:
        resultados["distribucion_cantidad"] = df_ventas["cantidad"].describe().to_frame(
            "cantidad"
        )
    for col in ["precio_unitario", "valor_bruto", "valor_descuento", "valor_neto"]:
        if col in df_ventas:
            resultados[f"resumen_{col}"] = resumen_numerico(df_ventas, [col])
    if "calificacion_cliente" in df_ventas:
        con_calificacion = df_ventas["calificacion_cliente"].dropna()
        resultados["distribucion_calificacion_cliente"] = con_calificacion.describe().to_frame(
            "calificacion_cliente"
        )
        resultados["conteo_calificacion_cliente"] = con_calificacion.value_counts().sort_index().to_frame(
            "conteo"
        )
    return resultados


# ---------------------------------------------------------------------------
# Resumenes especificos solicitados para df_logistica
# ---------------------------------------------------------------------------
def resumen_logistica(df_logistica: pd.DataFrame) -> dict[str, pd.DataFrame]:
    resultados: dict[str, pd.DataFrame] = {}

    if "estado_evento" in df_logistica:
        resultados["eventos_por_estado"] = resumen_categorico(df_logistica, "estado_evento")
    if "ciudad_destino" in df_logistica:
        resultados["eventos_por_ciudad_destino"] = resumen_categorico(
            df_logistica, "ciudad_destino"
        )
    if "transportadora" in df_logistica:
        resultados["frecuencia_transportadoras"] = resumen_categorico(
            df_logistica, "transportadora"
        )
    if "incidencia" in df_logistica:
        resultados["frecuencia_incidencias"] = resumen_categorico(df_logistica, "incidencia")
    for col in ["tiempo_etapa_horas", "costo_envio"]:
        if col in df_logistica:
            resultados[f"resumen_{col}"] = resumen_numerico(df_logistica, [col])
    return resultados
