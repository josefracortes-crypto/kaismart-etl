"""Parte 6: 10 preguntas de negocio resueltas con pandas sobre los datos
originales (df_ventas, df_logistica), sin necesidad de integrarlos."""
from __future__ import annotations

import pandas as pd


def q1_ciudad_mayor_valor_neto(df_ventas: pd.DataFrame) -> pd.Series:
    """1. Que ciudad genera el mayor valor neto total de ventas?"""
    return df_ventas.groupby("ciudad")["valor_neto"].sum().sort_values(ascending=False)


def q2_canal_mas_ventas(df_ventas: pd.DataFrame) -> pd.Series:
    """2. Que canal de venta concentra el mayor numero de transacciones?"""
    return df_ventas["canal"].value_counts()


def q3_categoria_mas_vendida_cantidad(df_ventas: pd.DataFrame) -> pd.Series:
    """3. Que categoria de producto vende mas unidades (cantidad)?"""
    return df_ventas.groupby("categoria")["cantidad"].sum().sort_values(ascending=False)


def q4_top10_clientes_valor_neto(df_ventas: pd.DataFrame) -> pd.Series:
    """4. Cuales son los 10 clientes con mayor valor neto acumulado en compras?"""
    return (
        df_ventas.groupby("cliente_id")["valor_neto"].sum().sort_values(ascending=False).head(10)
    )


def q5_ventas_por_mes(df_ventas: pd.DataFrame) -> pd.Series:
    """5. Como se distribuyen las ventas (numero de transacciones) por mes?"""
    fechas = pd.to_datetime(df_ventas["fecha_venta"], errors="coerce")
    return fechas.dt.to_period("M").value_counts().sort_index()


def q6_transportadora_mas_incidencias(df_logistica: pd.DataFrame) -> pd.Series:
    """6. Que transportadora concentra el mayor numero de incidencias reportadas?"""
    con_incidencia = df_logistica[df_logistica["incidencia"].notna()]
    return con_incidencia["transportadora"].value_counts()


def q7_estado_evento_mas_frecuente(df_logistica: pd.DataFrame) -> pd.Series:
    """7. Cual es el estado de evento logistico mas frecuente en el proceso?"""
    return df_logistica["estado_evento"].value_counts()


def q8_tiempo_promedio_por_transportadora(df_logistica: pd.DataFrame) -> pd.Series:
    """8. Cual es el tiempo promedio (horas) de cada etapa por transportadora?"""
    return (
        df_logistica.groupby("transportadora")["tiempo_etapa_horas"]
        .mean()
        .round(2)
        .sort_values(ascending=False)
    )


def q9_costo_envio_promedio_por_ciudad(df_logistica: pd.DataFrame) -> pd.Series:
    """9. Cual es el costo de envio promedio segun la ciudad de destino?

    costo_envio puede llegar mezclado como texto (p.ej. "$ 45.000") en el
    dato crudo; se coacciona a numerico solo para poder promediar aqui.
    """
    costo_numerico = pd.to_numeric(df_logistica["costo_envio"], errors="coerce")
    return (
        costo_numerico.groupby(df_logistica["ciudad_destino"])
        .mean()
        .round(0)
        .sort_values(ascending=False)
    )


def q10_pct_ventas_con_calificacion(df_ventas: pd.DataFrame) -> dict:
    """10. Que porcentaje de ventas cuenta con calificacion del cliente y
    cual es el promedio de esa calificacion?"""
    total = len(df_ventas)
    con_calificacion = df_ventas["calificacion_cliente"].notna().sum()
    return {
        "total_ventas": total,
        "con_calificacion": int(con_calificacion),
        "pct_con_calificacion": round(con_calificacion / total * 100, 2) if total else 0,
        "promedio_calificacion": round(df_ventas["calificacion_cliente"].mean(), 2),
    }


PREGUNTAS = {
    "1_ciudad_mayor_valor_neto": q1_ciudad_mayor_valor_neto,
    "2_canal_mas_ventas": q2_canal_mas_ventas,
    "3_categoria_mas_vendida_cantidad": q3_categoria_mas_vendida_cantidad,
    "4_top10_clientes_valor_neto": q4_top10_clientes_valor_neto,
    "5_ventas_por_mes": q5_ventas_por_mes,
    "6_transportadora_mas_incidencias": q6_transportadora_mas_incidencias,
    "7_estado_evento_mas_frecuente": q7_estado_evento_mas_frecuente,
    "8_tiempo_promedio_por_transportadora": q8_tiempo_promedio_por_transportadora,
    "9_costo_envio_promedio_por_ciudad": q9_costo_envio_promedio_por_ciudad,
    "10_pct_ventas_con_calificacion": q10_pct_ventas_con_calificacion,
}
