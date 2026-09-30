
from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pymysql

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kaismart_etl import catalogs  # noqa: E402
from kaismart_etl.config import settings  # noqa: E402
from kaismart_etl.logging_config import get_logger  # noqa: E402

logger = get_logger(__name__)

N_VENTAS = 5000
EVENTOS_POR_PEDIDO = (6, 12)  # rango aleatorio de eventos logisticos por pedido
SEED = 42

FLUJOS_ESTADO = {
    "entregado": ["Pedido Recibido", "En Preparación", "Despachado", "En Tránsito", "Entregado"],
    "devuelto": ["Pedido Recibido", "En Preparación", "Despachado", "En Tránsito", "Entregado", "Devuelto"],
    "cancelado": ["Pedido Recibido", "En Preparación", "Cancelado"],
}


def _variantes_sucias(valor: str, rng: random.Random) -> str:
    """Devuelve el valor original o una variante 'sucia' (mayusculas, minusculas,
    espacios extra, sin tildes) para simular inconsistencias reales de captura."""
    opcion = rng.random()
    if opcion < 0.6:
        return valor
    if opcion < 0.75:
        return valor.upper()
    if opcion < 0.9:
        return valor.lower()
    return f" {valor} "


def generar_ventas(n: int = N_VENTAS, seed: int = SEED) -> pd.DataFrame:
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)

    precios_base = {
        "Tecnología": (80_000, 4_500_000),
        "Hogar": (30_000, 1_200_000),
        "Oficina": (15_000, 600_000),
        "Electrodomésticos": (100_000, 3_800_000),
        "Deportes": (25_000, 900_000),
    }

    filas = []
    fecha_inicio = datetime(2024, 1, 1)
    for i in range(1, n + 1):
        categoria = rng.choice(catalogs.CATEGORIAS_PRODUCTO)
        ciudad = rng.choice(catalogs.CIUDADES)
        canal = rng.choices(catalogs.CANALES, weights=[0.35, 0.45, 0.20])[0]
        metodo_pago = rng.choice(catalogs.METODOS_PAGO)

        cantidad = int(np_rng.choice([1, 1, 1, 2, 2, 3, 4, 5]))
        precio_min, precio_max = precios_base[categoria]
        precio_unitario = round(np_rng.uniform(precio_min, precio_max), -2)
        valor_bruto = cantidad * precio_unitario
        valor_descuento = round(valor_bruto * rng.choice([0, 0, 0, 0.05, 0.1, 0.15]), 0)
        valor_neto = valor_bruto - valor_descuento

        fecha_venta = fecha_inicio + timedelta(
            days=int(np_rng.integers(0, 600)), hours=int(np_rng.integers(0, 23))
        )

        calificacion = rng.choice([np.nan] * 6 + [1, 2, 3, 4, 5])

        filas.append(
            {
                "id_venta": i,
                "pedido_id": f"PED-{i:06d}",
                "cliente_id": int(np_rng.integers(1000, 1000 + n // 3)),
                "fecha_venta": fecha_venta,
                "ciudad": _variantes_sucias(ciudad, rng),
                "canal": _variantes_sucias(canal, rng),
                "categoria": _variantes_sucias(categoria, rng),
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "valor_bruto": valor_bruto,
                "valor_descuento": valor_descuento,
                "valor_neto": valor_neto,
                "calificacion_cliente": calificacion,
                "metodo_pago": metodo_pago,
            }
        )

    df = pd.DataFrame(filas)

    # --- Inyeccion deliberada de problemas de calidad ---
    idx = df.index

    # 1) Nulos en valor_descuento (significa "no se aplico descuento", pero llega vacio)
    muestra = rng.sample(list(idx), k=int(n * 0.15))
    df.loc[muestra, "valor_descuento"] = np.nan

    # 2) Nulos en metodo_pago
    muestra = rng.sample(list(idx), k=int(n * 0.05))
    df.loc[muestra, "metodo_pago"] = np.nan

    # 3) pedido_id faltante (registros que no se podran integrar con logistica)
    muestra = rng.sample(list(idx), k=int(n * 0.01))
    df.loc[muestra, "pedido_id"] = np.nan

    # 4) cantidad y precio_unitario invalidos (errores de captura: 0 o negativos)
    muestra = rng.sample(list(idx), k=int(n * 0.02))
    df.loc[muestra, "cantidad"] = 0
    muestra = rng.sample(list(idx), k=int(n * 0.02))
    df.loc[muestra, "precio_unitario"] = -df.loc[muestra, "precio_unitario"]

    # 5) fecha_venta invalida (texto no parseable) o nula
    muestra = rng.sample(list(idx), k=int(n * 0.01))
    df.loc[muestra, "fecha_venta"] = "fecha no disponible"
    muestra = rng.sample(list(idx), k=int(n * 0.005))
    df.loc[muestra, "fecha_venta"] = np.nan

    # 6) Duplicados: filas completamente identicas
    duplicadas = df.sample(n=int(n * 0.01), random_state=seed)
    df = pd.concat([df, duplicadas], ignore_index=True)

    # 7) id_venta duplicado (mismo id, diferente contenido -> error de origen)
    idx_dup = rng.sample(list(df.index), k=int(n * 0.005))
    for pos in idx_dup:
        df.loc[pos, "id_venta"] = df.loc[rng.choice(list(df.index)), "id_venta"]

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def generar_logistica(df_ventas: pd.DataFrame, seed: int = SEED) -> pd.DataFrame:
    rng = random.Random(seed + 1)
    np_rng = np.random.default_rng(seed + 1)

    transportadora_por_ciudad = catalogs.TRANSPORTADORAS
    filas = []
    evento_id = 1

    pedidos = df_ventas["pedido_id"].dropna().tolist()
    for pedido_id in pedidos:
        desenlace = rng.choices(
            ["entregado", "devuelto", "cancelado"], weights=[0.8, 0.12, 0.08]
        )[0]
        estados = FLUJOS_ESTADO[desenlace]
        ciudad_destino = rng.choice(catalogs.CIUDADES)
        transportadora = rng.choice(transportadora_por_ciudad)

        fecha_evento = datetime(2024, 1, 1) + timedelta(days=int(np_rng.integers(0, 600)))
        for estado in estados:
            tiempo_etapa = round(float(np_rng.gamma(shape=2.0, scale=6.0)), 2)
            fecha_evento = fecha_evento + timedelta(hours=tiempo_etapa)

            incidencia = np.nan
            if estado in ("En Tránsito", "Devuelto") and rng.random() < 0.12:
                incidencia = rng.choice(catalogs.INCIDENCIAS)

            costo_envio = round(np_rng.uniform(8_000, 45_000), -2)

            filas.append(
                {
                    "evento_id": evento_id,
                    "pedido_id": pedido_id,
                    "fecha_evento": fecha_evento,
                    "estado_evento": _variantes_sucias(estado, rng),
                    "ciudad_destino": _variantes_sucias(ciudad_destino, rng),
                    "transportadora": _variantes_sucias(transportadora, rng),
                    "incidencia": incidencia,
                    "tiempo_etapa_horas": tiempo_etapa,
                    "costo_envio": costo_envio,
                }
            )
            evento_id += 1

    df = pd.DataFrame(filas)

    # Recorta o completa a exactamente 50.000 filas para respetar el enunciado
    objetivo = 50_000
    if len(df) > objetivo:
        df = df.sample(n=objetivo, random_state=seed).reset_index(drop=True)
    elif len(df) < objetivo:
        faltantes = objetivo - len(df)
        extra = df.sample(n=faltantes, replace=True, random_state=seed).copy()
        extra["evento_id"] = range(evento_id, evento_id + faltantes)
        df = pd.concat([df, extra], ignore_index=True)

    idx = df.index

    # 1) costo_envio como texto con formato moneda colombiano ("$ 45.000,00")
    muestra = rng.sample(list(idx), k=int(len(df) * 0.2))
    df.loc[muestra, "costo_envio"] = df.loc[muestra, "costo_envio"].apply(
        lambda v: f"$ {v:,.0f}".replace(",", ".")
    )

    # 2) costo_envio nulo
    muestra = rng.sample(list(idx), k=int(len(df) * 0.03))
    df.loc[muestra, "costo_envio"] = np.nan

    # 3) tiempo_etapa_horas negativo (error de captura) y outliers extremos
    muestra = rng.sample(list(idx), k=int(len(df) * 0.01))
    df.loc[muestra, "tiempo_etapa_horas"] = -df.loc[muestra, "tiempo_etapa_horas"].abs()
    muestra = rng.sample(list(idx), k=int(len(df) * 0.005))
    df.loc[muestra, "tiempo_etapa_horas"] = df.loc[muestra, "tiempo_etapa_horas"] * 50

    # 4) pedido_id faltante (evento huerfano)
    muestra = rng.sample(list(idx), k=int(len(df) * 0.005))
    df.loc[muestra, "pedido_id"] = np.nan

    # 5) fecha_evento nula
    muestra = rng.sample(list(idx), k=int(len(df) * 0.005))
    df.loc[muestra, "fecha_evento"] = np.nan

    # 6) evento_id duplicado
    idx_dup = rng.sample(list(df.index), k=int(len(df) * 0.003))
    for pos in idx_dup:
        df.loc[pos, "evento_id"] = df.loc[rng.choice(list(df.index)), "evento_id"]

    # 7) filas completamente duplicadas
    duplicadas = df.sample(n=int(len(df) * 0.005), random_state=seed)
    df = pd.concat([df, duplicadas], ignore_index=True)

    return df.sample(frac=1, random_state=seed).reset_index(drop=True)


def sembrar_mysql(df_ventas: pd.DataFrame) -> None:
    cfg = settings.mysql
    logger.info("Creando base de datos '%s' si no existe...", cfg.database)
    conn = pymysql.connect(host=cfg.host, port=cfg.port, user=cfg.user, password=cfg.password)
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{cfg.database}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    from sqlalchemy import create_engine

    engine = create_engine(cfg.sqlalchemy_url)
    try:
        # Se guarda la columna fecha_venta como string en algunas filas a proposito
        # (ver generar_ventas), por lo que se inserta tal cual llega para simular
        # el problema real de calidad de datos en el origen.
        df_ventas.to_sql(cfg.tabla_ventas, con=engine, if_exists="replace", index=False)
        logger.info("Tabla '%s' sembrada con %s registros en MySQL.", cfg.tabla_ventas, len(df_ventas))
    finally:
        engine.dispose()


def guardar_excel_logistica(df_logistica: pd.DataFrame) -> Path:
    settings.ensure_dirs()
    destino = settings.excel_logistica_path
    destino.parent.mkdir(parents=True, exist_ok=True)
    df_logistica.to_excel(destino, index=False, engine="openpyxl")
    logger.info("Excel de logistica generado en: %s (%s registros)", destino, len(df_logistica))
    return destino


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-mysql",
        action="store_true",
        help="No siembra MySQL, solo genera el archivo Excel de logistica.",
    )
    args = parser.parse_args()

    df_ventas = generar_ventas()
    df_logistica = generar_logistica(df_ventas)

    guardar_excel_logistica(df_logistica)

    if args.skip_mysql:
        # Se deja tambien un respaldo en CSV para poder inspeccionar/cargar
        # manualmente sin necesidad de un servidor MySQL activo.
        respaldo = settings.bronze_dir.parent / "raw" / "ventas_mock.csv"
        respaldo.parent.mkdir(parents=True, exist_ok=True)
        df_ventas.to_csv(respaldo, index=False)
        logger.info("MySQL omitido (--skip-mysql). Respaldo CSV en: %s", respaldo)
    else:
        sembrar_mysql(df_ventas)

    print("\nDatos simulados generados correctamente.")
    print(f"df_ventas: {df_ventas.shape}")
    print(f"df_logistica: {df_logistica.shape}")


if __name__ == "__main__":
    main()
