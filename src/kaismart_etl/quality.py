
from __future__ import annotations

import pandas as pd


# ---------------------------------------------------------------------------
# Parte 3: comprension inicial
# ---------------------------------------------------------------------------
def resumen_estructura(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    """Tabla con: tipo de dato, no nulos, nulos, %nulos y nunique por columna."""
    resumen = pd.DataFrame(
        {
            "columna": df.columns,
            "tipo_dato": [str(t) for t in df.dtypes],
            "no_nulos": df.notna().sum().values,
            "nulos": df.isna().sum().values,
            "pct_nulos": (df.isna().mean() * 100).round(2).values,
            "valores_unicos": [df[c].nunique(dropna=True) for c in df.columns],
        }
    )
    resumen.insert(0, "dataset", nombre)
    return resumen


def sugerir_tipos_variables(df: pd.DataFrame) -> dict[str, list[str]]:

    identificadores, categoricas, numericas, fechas = [], [], [], []

    for col in df.columns:
        serie = df[col]
        nombre_col = col.lower()

        if "fecha" in nombre_col or "date" in nombre_col or pd.api.types.is_datetime64_any_dtype(serie):
            fechas.append(col)
            continue

        if nombre_col.endswith("_id") or nombre_col.startswith("id_") or nombre_col == "pedido_id":
            identificadores.append(col)
            continue

        if pd.api.types.is_numeric_dtype(serie):
            numericas.append(col)
            continue

        # object / string: categorica si la cardinalidad es baja respecto al total
        if serie.nunique(dropna=True) <= max(50, int(len(df) * 0.05)):
            categoricas.append(col)
        else:
            identificadores.append(col)  # alta cardinalidad tipo texto -> posible id/texto libre

    return {
        "identificadores": identificadores,
        "categoricas": categoricas,
        "numericas": numericas,
        "fechas": fechas,
    }


def rango_fechas(df: pd.DataFrame, columna_fecha: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Retorna (fecha_min, fecha_max) de una columna, convirtiendo a datetime si hace falta."""
    serie = pd.to_datetime(df[columna_fecha], errors="coerce")
    return serie.min(), serie.max()


# ---------------------------------------------------------------------------
# Parte 4.1: valores nulos
# ---------------------------------------------------------------------------
def perfil_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Cantidad y porcentaje de nulos por variable, ordenado descendente."""
    nulos = df.isna().sum()
    porcentaje = (df.isna().mean() * 100).round(2)
    perfil = (
        pd.DataFrame({"cantidad_nulos": nulos, "pct_nulos": porcentaje})
        .sort_values("pct_nulos", ascending=False)
    )
    perfil.index.name = "columna"
    return perfil.reset_index()


# ---------------------------------------------------------------------------
# Parte 4.2: valores unicos / cardinalidad
# ---------------------------------------------------------------------------
def perfil_cardinalidad(df: pd.DataFrame, umbral_baja: int = 15) -> pd.DataFrame:
    """nunique() por columna + clasificacion de cardinalidad.

    - baja: <= umbral_baja valores distintos (candidatas a categoricas).
    - alta: el resto (posibles identificadores o texto libre).
    """
    n = len(df)
    filas = []
    for col in df.columns:
        nun = df[col].nunique(dropna=True)
        pct_unico = round(nun / n * 100, 2) if n else 0.0
        if nun <= umbral_baja:
            categoria = "baja cardinalidad"
        elif pct_unico >= 95:
            categoria = "posible identificador (casi todos los valores son unicos)"
        else:
            categoria = "alta cardinalidad"
        filas.append(
            {
                "columna": col,
                "valores_unicos": nun,
                "pct_valores_unicos": pct_unico,
                "clasificacion": categoria,
            }
        )
    return pd.DataFrame(filas).sort_values("valores_unicos", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Parte 4.3: duplicados
# ---------------------------------------------------------------------------
def perfil_duplicados(df: pd.DataFrame, columnas_id: list[str] | None = None) -> dict:
    """Cuenta filas completamente duplicadas y duplicados en columnas identificadoras.

    No elimina nada; solo diagnostica.
    """
    resultado = {
        "filas_totales": len(df),
        "filas_duplicadas_completas": int(df.duplicated(keep=False).sum()),
        "filas_duplicadas_completas_excedentes": int(df.duplicated(keep="first").sum()),
    }
    if columnas_id:
        for col in columnas_id:
            if col not in df.columns:
                continue
            dup_id = df[col].duplicated(keep=False) & df[col].notna()
            resultado[f"duplicados_en_{col}"] = int(dup_id.sum())
            resultado[f"valores_{col}_repetidos"] = int(
                df.loc[dup_id, col].nunique()
            )
    return resultado


# ---------------------------------------------------------------------------
# Parte 4.4: revision de tipos de datos
# ---------------------------------------------------------------------------
def revisar_tipos(df: pd.DataFrame, columnas_esperadas: dict[str, str]) -> pd.DataFrame:
    """Compara el tipo detectado por pandas contra el tipo esperado por el analista.

    columnas_esperadas: {"columna": "fecha|identificador|monetaria|numerica|categorica"}
    Retorna filas marcadas para revision cuando el dtype real no calza con lo esperado.
    """
    filas = []
    for col, tipo_esperado in columnas_esperadas.items():
        if col not in df.columns:
            continue
        dtype_real = str(df[col].dtype)
        requiere_revision = False
        motivo = ""

        if tipo_esperado == "fecha" and not pd.api.types.is_datetime64_any_dtype(df[col]):
            requiere_revision = True
            motivo = "se esperaba datetime pero llego como texto/objeto"
        elif tipo_esperado == "monetaria" and not pd.api.types.is_numeric_dtype(df[col]):
            requiere_revision = True
            motivo = "se esperaba numerico (moneda) pero llego como texto/objeto"
        elif tipo_esperado == "numerica" and not pd.api.types.is_numeric_dtype(df[col]):
            requiere_revision = True
            motivo = "se esperaba numerico pero llego como texto/objeto"
        elif tipo_esperado == "identificador" and pd.api.types.is_float_dtype(df[col]):
            requiere_revision = True
            motivo = "identificador llego como float (posibles NaN o formato incorrecto)"

        filas.append(
            {
                "columna": col,
                "tipo_esperado": tipo_esperado,
                "dtype_detectado": dtype_real,
                "requiere_revision": requiere_revision,
                "motivo": motivo,
            }
        )
    return pd.DataFrame(filas)
