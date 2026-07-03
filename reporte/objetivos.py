"""Lectura y calculo de la hoja Objetivos para el dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


HOJA_OBJETIVOS = "Objetivos"
COLUMNAS_OBJETIVOS = [
    "nombre_ciclo",
    "nombre_colaborador",
    "email_colaborador",
    "nombre_seccion",
    "pregunta_texto",
    "tipo_evaluacion",
    "nombre_evaluador",
    "email_evaluador",
    "respuesta_valor",
    "calificacion_porcentaje",
]


def limpiar_texto(valor: object) -> object:
    if not isinstance(valor, str):
        return valor
    return " ".join(valor.replace("\n", " ").split()).strip()


def leer_objetivos(ruta: str | Path) -> dict:
    xls = pd.ExcelFile(ruta)
    if HOJA_OBJETIVOS not in xls.sheet_names:
        return _vacio()

    df = pd.read_excel(xls, sheet_name=HOJA_OBJETIVOS, dtype=str)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    faltantes = [col for col in COLUMNAS_OBJETIVOS if col not in df.columns]
    if faltantes:
        raise ValueError(
            "La hoja 'Objetivos' no tiene la estructura esperada. "
            f"Columnas faltantes: {', '.join(faltantes)}."
        )

    df = df[df["nombre_colaborador"].notna()].copy()
    for col in [
        "nombre_ciclo",
        "nombre_colaborador",
        "email_colaborador",
        "nombre_seccion",
        "pregunta_texto",
        "tipo_evaluacion",
        "nombre_evaluador",
        "email_evaluador",
    ]:
        df[col] = df[col].apply(limpiar_texto)

    df["respuesta_valor"] = pd.to_numeric(df["respuesta_valor"], errors="coerce")
    df["calificacion_porcentaje"] = pd.to_numeric(df["calificacion_porcentaje"], errors="coerce")

    sin_porcentaje = df["calificacion_porcentaje"].isna() & df["respuesta_valor"].notna()
    df.loc[sin_porcentaje, "calificacion_porcentaje"] = df.loc[sin_porcentaje, "respuesta_valor"] * 20

    df = df[df["calificacion_porcentaje"].notna()].copy()
    df["puntaje"] = df["calificacion_porcentaje"].clip(0, 100)
    df["cargo_objetivo"] = df["nombre_seccion"]
    df["objetivo"] = df["pregunta_texto"]

    df_colaboradores = (
        df.groupby(["nombre_colaborador", "email_colaborador"], dropna=False)
        .agg(
            puntaje=("puntaje", "mean"),
            objetivos=("objetivo", "nunique"),
            cargo_objetivo=("cargo_objetivo", lambda valores: " / ".join(sorted(set(map(str, valores.dropna()))))),
            jefe=("nombre_evaluador", lambda valores: " / ".join(sorted(set(map(str, valores.dropna()))))),
        )
        .reset_index()
        .rename(columns={
            "nombre_colaborador": "colaborador",
        })
        .sort_values("puntaje", ascending=False)
    )

    df_cargos = (
        df.groupby("cargo_objetivo", dropna=False)
        .agg(
            puntaje=("puntaje", "mean"),
            colaboradores=("nombre_colaborador", "nunique"),
            objetivos=("objetivo", "nunique"),
        )
        .reset_index()
        .sort_values("puntaje", ascending=False)
    )

    df_objetivos = (
        df.groupby(["cargo_objetivo", "objetivo"], dropna=False)
        .agg(
            puntaje=("puntaje", "mean"),
            colaboradores=("nombre_colaborador", "nunique"),
        )
        .reset_index()
        .sort_values("puntaje", ascending=False)
    )

    resumen = {
        "filas": len(df),
        "colaboradores": int(df["nombre_colaborador"].nunique()),
        "jefes": int(df["nombre_evaluador"].nunique()),
        "cargos": int(df["cargo_objetivo"].nunique()),
        "objetivos": int(df["objetivo"].nunique()),
        "promedio": float(df_colaboradores["puntaje"].mean()) if len(df_colaboradores) else 0.0,
        "ciclo": str(df["nombre_ciclo"].dropna().iloc[0]) if df["nombre_ciclo"].notna().any() else "Objetivos",
    }

    return {
        "df_fuente": df,
        "df_colaboradores": df_colaboradores,
        "df_cargos": df_cargos,
        "df_objetivos": df_objetivos,
        "resumen": resumen,
    }


def _vacio() -> dict:
    return {
        "df_fuente": pd.DataFrame(),
        "df_colaboradores": pd.DataFrame(
            columns=["colaborador", "email_colaborador", "cargo_objetivo", "jefe", "puntaje", "objetivos"]
        ),
        "df_cargos": pd.DataFrame(columns=["cargo_objetivo", "puntaje", "colaboradores", "objetivos"]),
        "df_objetivos": pd.DataFrame(columns=["cargo_objetivo", "objetivo", "puntaje", "colaboradores"]),
        "resumen": {
            "filas": 0,
            "colaboradores": 0,
            "jefes": 0,
            "cargos": 0,
            "objetivos": 0,
            "promedio": 0.0,
            "ciclo": "Objetivos",
        },
    }
