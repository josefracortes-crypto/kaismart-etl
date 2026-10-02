
from __future__ import annotations

import numpy as np
import pandas as pd

from .. import catalogs
from ..normalize import estandarizar_categoria


def limpiar_ventas(df_bronze: pd.DataFrame) -> tuple[pd.DataFrame, dict]:

    df = df_bronze.drop(columns=["_fuente", "_fecha_ingesta"], errors="ignore").copy()
    reporte: dict = {"filas_entrada": len(df)}

    # 1) Duplicados completos: se consideran doble insercion accidental -> se eliminan.
    dup_completos = int(df.duplicated(keep="first").sum())
    df = df.drop_duplicates(keep="first")
    reporte["duplicados_completos_eliminados"] = dup_completos

    # 2) id_venta es la llave primaria del sistema comercial: no deberia repetirse.
    #    Si se repite, se conserva el primer registro y se documenta el resto como error de origen.
    if "id_venta" in df.columns:
        dup_id_venta = int(df["id_venta"].duplicated(keep="first").sum())
        df = df.drop_duplicates(subset=["id_venta"], keep="first")
        reporte["duplicados_id_venta_eliminados"] = dup_id_venta

    # 3) pedido_id es la llave de integracion con logistica: sin ella el registro
    #    no se puede vincular a ningun evento logistico -> se descarta y se documenta.
    if "pedido_id" in df.columns:
        sin_pedido_id = int(df["pedido_id"].isna().sum())
        df = df[df["pedido_id"].notna()].copy()
        reporte["filas_sin_pedido_id_eliminadas"] = sin_pedido_id

    # 4) fecha_venta: se parsea a datetime. Las fechas invalidas se dejan como NaT
    #    (no se inventa una fecha) y se documenta cuantas quedaron sin valor.
    if "fecha_venta" in df.columns:
        antes_validas = df["fecha_venta"].notna().sum()
        df["fecha_venta"] = pd.to_datetime(df["fecha_venta"], errors="coerce")
        reporte["fechas_venta_invalidas"] = int(antes_validas - df["fecha_venta"].notna().sum())

    # 5) Estandarizacion de categorias (ciudad, canal, categoria de producto).
    if "ciudad" in df.columns:
        df["ciudad"], rep = estandarizar_categoria(df["ciudad"], catalogs.CIUDADES, catalogs.CIUDADES_ALIAS)
        reporte["estandarizacion_ciudad"] = rep
    if "canal" in df.columns:
        df["canal"], rep = estandarizar_categoria(df["canal"], catalogs.CANALES, catalogs.CANALES_ALIAS)
        reporte["estandarizacion_canal"] = rep
    if "categoria" in df.columns:
        df["categoria"], rep = estandarizar_categoria(
            df["categoria"], catalogs.CATEGORIAS_PRODUCTO, catalogs.CATEGORIAS_PRODUCTO_ALIAS
        )
        reporte["estandarizacion_categoria"] = rep
    if "metodo_pago" in df.columns:
        # Nulo en metodo_pago no tiene un significado de negocio claro -> se marca
        # explicitamente como "NO INFORMADO" en lugar de dejarlo vacio.
        nulos_pago = int(df["metodo_pago"].isna().sum())
        df["metodo_pago"] = df["metodo_pago"].astype("string").str.strip().fillna("NO INFORMADO")
        df.loc[df["metodo_pago"].eq(""), "metodo_pago"] = "NO INFORMADO"
        reporte["metodo_pago_no_informado"] = nulos_pago

    # 6) cantidad: debe ser un entero positivo. Valores <=0 o nulos se consideran
    #    error de captura; se imputan con la MEDIANA (variable con posibles outliers,
    #    la mediana es mas robusta que la media) agrupada por categoria de producto.
    if "cantidad" in df.columns:
        df["cantidad"] = pd.to_numeric(df["cantidad"], errors="coerce")
        invalidas = int((df["cantidad"].isna() | (df["cantidad"] <= 0)).sum())
        df.loc[df["cantidad"] <= 0, "cantidad"] = np.nan
        if "categoria" in df.columns:
            df["cantidad"] = df["cantidad"].fillna(df.groupby("categoria")["cantidad"].transform("median"))
        df["cantidad"] = df["cantidad"].fillna(df["cantidad"].median())
        df["cantidad"] = df["cantidad"].round().astype("Int64")
        reporte["cantidad_imputada_mediana"] = invalidas

    # 7) precio_unitario: variable monetaria, no deberia ser negativa ni cero.
    #    Se imputa con la MEDIANA por categoria (el precio varia mucho segun la
    #    categoria de producto, por lo que la mediana global distorsionaria el dato).
    if "precio_unitario" in df.columns:
        df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")
        invalidos = int((df["precio_unitario"].isna() | (df["precio_unitario"] <= 0)).sum())
        df.loc[df["precio_unitario"] <= 0, "precio_unitario"] = np.nan
        if "categoria" in df.columns:
            df["precio_unitario"] = df["precio_unitario"].fillna(
                df.groupby("categoria")["precio_unitario"].transform("median")
            )
        df["precio_unitario"] = df["precio_unitario"].fillna(df["precio_unitario"].median())
        reporte["precio_unitario_imputado_mediana"] = invalidos

    # 8) valor_descuento: un nulo aqui SI tiene significado de negocio valido
    #    (no se aplico ningun descuento a la venta) -> se imputa con 0, no con
    #    media/mediana, porque 0 es el valor real esperado, no una estimacion.
    if "valor_descuento" in df.columns:
        df["valor_descuento"] = pd.to_numeric(df["valor_descuento"], errors="coerce")
        nulos_descuento = int(df["valor_descuento"].isna().sum())
        negativos = int((df["valor_descuento"] < 0).sum())
        df["valor_descuento"] = df["valor_descuento"].fillna(0)
        df.loc[df["valor_descuento"] < 0, "valor_descuento"] = 0
        reporte["valor_descuento_nulos_imputados_0"] = nulos_descuento
        reporte["valor_descuento_negativos_corregidos"] = negativos

    # 9) valor_bruto y valor_neto: se RECALCULAN a partir de cantidad, precio_unitario
    #    y valor_descuento para garantizar consistencia aritmetica, en lugar de
    #    confiar en un valor que pudo llegar corrupto desde el origen.
    if {"cantidad", "precio_unitario"}.issubset(df.columns):
        valor_bruto_calculado = df["cantidad"].astype(float) * df["precio_unitario"]
        if "valor_bruto" in df.columns:
            inconsistentes = int(
                (~np.isclose(df["valor_bruto"].fillna(-1), valor_bruto_calculado, rtol=0.01)).sum()
            )
            reporte["valor_bruto_inconsistentes_recalculados"] = inconsistentes
        df["valor_bruto"] = valor_bruto_calculado
    if {"valor_bruto", "valor_descuento"}.issubset(df.columns):
        df["valor_neto"] = (df["valor_bruto"] - df["valor_descuento"]).clip(lower=0)

    # 10) calificacion_cliente: un nulo SI tiene significado valido (el cliente no
    #     dejo calificacion) -> se conserva el nulo, NO se imputa. Solo se corrigen
    #     valores fuera del rango valido 1-5 (error de captura), que se llevan a NaN.
    if "calificacion_cliente" in df.columns:
        df["calificacion_cliente"] = pd.to_numeric(df["calificacion_cliente"], errors="coerce")
        fuera_de_rango = int(
            (~df["calificacion_cliente"].between(1, 5) & df["calificacion_cliente"].notna()).sum()
        )
        df.loc[~df["calificacion_cliente"].between(1, 5), "calificacion_cliente"] = np.nan
        reporte["calificacion_fuera_de_rango_a_nulo"] = fuera_de_rango
        reporte["calificacion_nulos_conservados"] = int(df["calificacion_cliente"].isna().sum())

    # 11) Tipos finales de identificadores como texto (evita operaciones aritmeticas
    #     accidentales y homogeneiza el tipo para el join en la capa Gold).
    for col in ("id_venta", "pedido_id", "cliente_id"):
        if col in df.columns:
            df[col] = df[col].astype("string")

    reporte["filas_salida"] = len(df)
    return df.reset_index(drop=True), reporte


def limpiar_logistica(df_bronze: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Limpia df_logistica (bronze) y retorna (df_logistica_transformado, reporte)."""
    df = df_bronze.drop(columns=["_fuente", "_fecha_ingesta"], errors="ignore").copy()
    reporte: dict = {"filas_entrada": len(df)}

    # 1) Duplicados completos: doble registro del mismo evento -> se eliminan.
    dup_completos = int(df.duplicated(keep="first").sum())
    df = df.drop_duplicates(keep="first")
    reporte["duplicados_completos_eliminados"] = dup_completos

    # 2) evento_id deberia ser unico por evento; si se repite se conserva el primero.
    if "evento_id" in df.columns:
        dup_evento = int(df["evento_id"].duplicated(keep="first").sum())
        df = df.drop_duplicates(subset=["evento_id"], keep="first")
        reporte["duplicados_evento_id_eliminados"] = dup_evento

    # 3) pedido_id es la llave de integracion: eventos sin pedido_id no se pueden
    #    vincular a ninguna venta -> se descartan y se documenta cuantos fueron.
    if "pedido_id" in df.columns:
        sin_pedido_id = int(df["pedido_id"].isna().sum())
        df = df[df["pedido_id"].notna()].copy()
        reporte["filas_sin_pedido_id_eliminadas"] = sin_pedido_id

    # 4) fecha_evento: se parsea a datetime; invalidas se dejan como NaT (no se inventan).
    if "fecha_evento" in df.columns:
        antes_validas = df["fecha_evento"].notna().sum()
        df["fecha_evento"] = pd.to_datetime(df["fecha_evento"], errors="coerce")
        reporte["fechas_evento_invalidas"] = int(antes_validas - df["fecha_evento"].notna().sum())

    # 5) Estandarizacion de categorias.
    if "estado_evento" in df.columns:
        df["estado_evento"], rep = estandarizar_categoria(
            df["estado_evento"], catalogs.ESTADOS_EVENTO, catalogs.ESTADOS_EVENTO_ALIAS
        )
        reporte["estandarizacion_estado_evento"] = rep
    if "ciudad_destino" in df.columns:
        df["ciudad_destino"], rep = estandarizar_categoria(
            df["ciudad_destino"], catalogs.CIUDADES, catalogs.CIUDADES_ALIAS
        )
        reporte["estandarizacion_ciudad_destino"] = rep
    if "transportadora" in df.columns:
        df["transportadora"], rep = estandarizar_categoria(
            df["transportadora"], catalogs.TRANSPORTADORAS, catalogs.TRANSPORTADORAS_ALIAS
        )
        reporte["estandarizacion_transportadora"] = rep

    # 6) incidencia: un nulo SI tiene significado valido (el evento se completo sin
    #    ningun incidente) -> se imputa con la categoria "SIN INCIDENCIA" en lugar
    #    de la moda, porque el nulo no representa un dato faltante sino "no aplica".
    if "incidencia" in df.columns:
        nulos_incidencia = int(df["incidencia"].isna().sum())
        df["incidencia"], rep = estandarizar_categoria(
            df["incidencia"], catalogs.INCIDENCIAS, catalogs.INCIDENCIAS_ALIAS,
            valor_no_reconocido="OTRA INCIDENCIA",
        )
        df["incidencia"] = df["incidencia"].fillna("SIN INCIDENCIA")
        reporte["incidencia_nulos_a_sin_incidencia"] = nulos_incidencia
        reporte["estandarizacion_incidencia"] = rep

    # 7) costo_envio: variable monetaria que en el origen a veces llega como texto
    #    (p.ej. "$45.000"). Se limpia el formato y se convierte a numerico.
    #    Los nulos resultantes se imputan con la MEDIANA por transportadora (variable
    #    con outliers -> la mediana es mas robusta que la media).
    if "costo_envio" in df.columns:
        costo_texto = df["costo_envio"].astype("string")
        costo_limpio = costo_texto.str.replace(r"[^0-9,.\-]", "", regex=True)
        costo_limpio = costo_limpio.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        df["costo_envio"] = pd.to_numeric(costo_limpio, errors="coerce")
        invalidos = int((df["costo_envio"].isna() | (df["costo_envio"] < 0)).sum())
        df.loc[df["costo_envio"] < 0, "costo_envio"] = np.nan
        if "transportadora" in df.columns:
            df["costo_envio"] = df["costo_envio"].fillna(
                df.groupby("transportadora")["costo_envio"].transform("median")
            )
        df["costo_envio"] = df["costo_envio"].fillna(df["costo_envio"].median())
        reporte["costo_envio_imputado_mediana"] = invalidos

    # 8) tiempo_etapa_horas: no puede ser negativo (error de captura). Se lleva a
    #    NaN y se imputa con la MEDIANA por estado_evento (cada etapa tiene una
    #    duracion tipica distinta, y la mediana evita el sesgo de valores extremos).
    if "tiempo_etapa_horas" in df.columns:
        df["tiempo_etapa_horas"] = pd.to_numeric(df["tiempo_etapa_horas"], errors="coerce")
        invalidos = int((df["tiempo_etapa_horas"].isna() | (df["tiempo_etapa_horas"] < 0)).sum())
        df.loc[df["tiempo_etapa_horas"] < 0, "tiempo_etapa_horas"] = np.nan
        if "estado_evento" in df.columns:
            df["tiempo_etapa_horas"] = df["tiempo_etapa_horas"].fillna(
                df.groupby("estado_evento")["tiempo_etapa_horas"].transform("median")
            )
        df["tiempo_etapa_horas"] = df["tiempo_etapa_horas"].fillna(df["tiempo_etapa_horas"].median())
        reporte["tiempo_etapa_horas_imputado_mediana"] = invalidos

    for col in ("evento_id", "pedido_id"):
        if col in df.columns:
            df[col] = df[col].astype("string")

    reporte["filas_salida"] = len(df)
    return df.reset_index(drop=True), reporte
