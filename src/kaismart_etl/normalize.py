
from __future__ import annotations

import unicodedata

import pandas as pd


def clave_normalizada(texto: str) -> str:

    if texto is None:
        return ""
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(texto.split())


def construir_diccionario_alias(valores_canonicos: list[str], alias_extra: dict[str, str]) -> dict[str, str]:

    diccionario = {clave_normalizada(v): v for v in valores_canonicos}
    for alias, canonico in alias_extra.items():
        diccionario[clave_normalizada(alias)] = canonico
    return diccionario


def estandarizar_categoria(
    serie: pd.Series,
    valores_canonicos: list[str],
    alias_extra: dict[str, str] | None = None,
    valor_no_reconocido: str = "NO INFORMADO",
) -> tuple[pd.Series, dict]:

    alias_extra = alias_extra or {}
    diccionario = construir_diccionario_alias(valores_canonicos, alias_extra)

    valores_originales_no_nulos = serie.notna().sum()
    claves = serie.map(clave_normalizada)
    estandarizada = claves.map(diccionario)

    no_reconocidos_mask = estandarizada.isna() & serie.notna()
    no_reconocidos = serie[no_reconocidos_mask].value_counts().to_dict()
    estandarizada = estandarizada.where(~no_reconocidos_mask, valor_no_reconocido)

    reporte = {
        "valores_originales_no_nulos": int(valores_originales_no_nulos),
        "valores_reconocidos": int(valores_originales_no_nulos - len(no_reconocidos_mask[no_reconocidos_mask])),
        "valores_no_reconocidos": int(no_reconocidos_mask.sum()),
        "detalle_no_reconocidos": no_reconocidos,
    }
    return estandarizada, reporte
