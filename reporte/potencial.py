"""Lectura y normalización de la hoja Potencial para el dashboard y reportes."""

from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore", category=pd.errors.PerformanceWarning)

HOJA_POTENCIAL = "Potencial"
ETIQUETAS_ESCALA = ["Ajustado al perfil", "Cercano al perfil", "Alejado al perfil"]
MAPA_ESCALA = {etiqueta.casefold(): etiqueta for etiqueta in ETIQUETAS_ESCALA}


def contar_escala(df: pd.DataFrame, columna: str) -> pd.Series:
    """Cuenta una escala ignorando diferencias de mayúsculas y espacios."""
    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .str.strip()
        .str.casefold()
        .map(MAPA_ESCALA)
    )
    return valores.value_counts().reindex(ETIQUETAS_ESCALA, fill_value=0)


def _limpiar_texto(valor):
    return valor.strip() if isinstance(valor, str) else valor


def _codigo_arquetipo(valor):
    if not isinstance(valor, str):
        return pd.NA
    match = re.search(r"\(([^)]+)\)", valor)
    return match.group(1).strip() if match else valor.strip()


def _clasificar_potencial(valor, limites: tuple[float, float]):
    puntaje = pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0]
    if pd.isna(puntaje):
        return pd.NA
    bajo, alto = limites
    if puntaje >= alto:
        return "Ajustado al perfil"
    if puntaje >= bajo:
        return "Cercano al perfil"
    return "Alejado al perfil"


def _preparar_columnas_persona(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "Email": "correo",
        "Correo": "correo",
        "Correo Potencial": "correo_potencial",
        "Correo Instancia": "correo_instancia",
        "NOMBRE COMPLETO": "colaborador",
        "Nombre del Perfil": "colaborador",
        "No. IdentificaciÃ³n": "identificacion",
        "No. Identificación": "identificacion",
        "PaÃ­s": "pais",
        "País": "pais",
        "Ãrea": "area",
        "Área": "area",
        "CAP": "potencial_2025",
        "COMPETENCIAS": "evaluacion_potencial",
        "EvaluaciÃ³n de Potencial": "evaluacion_potencial",
        "Evaluación de Potencial": "evaluacion_potencial",
        "Potencial 2025": "potencial_2025",
        "Escala Benchmark externo": "escala_benchmark",
        "Escala Potencial": "escala_potencial",
    }
    df = df.rename(columns={col: rename_map.get(col, col) for col in df.columns})
    if "colaborador" not in df.columns and {"Nombres", "Apellidos"}.issubset(df.columns):
        df["colaborador"] = (
            df["Nombres"].fillna("").astype(str).str.strip()
            + " "
            + df["Apellidos"].fillna("").astype(str).str.strip()
        ).str.strip()

    defaults = {
        "correo": df.get("correo_potencial", pd.NA),
        "correo_potencial": pd.NA,
        "correo_instancia": pd.NA,
        "identificacion": pd.NA,
        "empresa": pd.NA,
        "pais": pd.NA,
        "area": pd.NA,
        "escala_benchmark": pd.NA,
        "escala_potencial": pd.NA,
        "potencial_2025": pd.NA,
        "evaluacion_potencial": pd.NA,
    }
    for original in ["Empresa", "Cargo", "Jefe", "Grupo"]:
        if original in df.columns:
            df[original.lower()] = df[original]
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default
    for col in ["cargo", "jefe", "grupo"]:
        if col not in df.columns:
            df[col] = pd.NA
    return df


def leer_potencial(ruta: str | Path) -> dict:
    """Convierte la matriz ancha de Potencial en tablas de personas y competencias."""
    xls = pd.ExcelFile(ruta)
    if HOJA_POTENCIAL not in xls.sheet_names:
        raise ValueError("El archivo base debe contener la hoja 'Potencial'.")

    raw = pd.read_excel(xls, sheet_name=HOJA_POTENCIAL, header=None)
    header_row = 1 if "Correo Potencial" in raw.iloc[1].astype(str).tolist() else 2
    grupos = raw.iloc[header_row - 1].tolist() if header_row > 0 else [pd.NA] * raw.shape[1]
    df = pd.read_excel(xls, sheet_name=HOJA_POTENCIAL, header=header_row)
    rename_grupos = {}
    for idx, col in enumerate(df.columns):
        grupo = grupos[idx] if idx < len(grupos) else pd.NA
        if str(col).startswith("Unnamed") and isinstance(grupo, str) and grupo.strip().casefold() == "iq":
            rename_grupos[col] = "IQ"
    if rename_grupos:
        df = df.rename(columns=rename_grupos)
    df = _preparar_columnas_persona(df)

    if "colaborador" not in df.columns:
        raise ValueError("La hoja 'Potencial' debe contener el nombre del colaborador.")

    df = df[df["colaborador"].notna()].copy()
    df["colaborador"] = df["colaborador"].astype(str).str.strip()
    if df["colaborador"].duplicated().any():
        duplicados = int(df["colaborador"].duplicated().sum())
        raise ValueError(f"La hoja 'Potencial' contiene {duplicados} nombres duplicados.")

    for col in ["potencial_2025", "evaluacion_potencial"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if df["evaluacion_potencial"].notna().sum() == 0 and "potencial_2025" in df.columns:
        df["evaluacion_potencial"] = df["potencial_2025"]
    if df["escala_benchmark"].isna().all():
        df["escala_benchmark"] = df["evaluacion_potencial"].apply(
            lambda valor: _clasificar_potencial(valor, (70, 85))
        )
    if df["escala_potencial"].isna().all():
        df["escala_potencial"] = df["evaluacion_potencial"].apply(
            lambda valor: _clasificar_potencial(valor, (82, 98))
        )

    columnas = list(df.columns)
    competencias = []
    catalogo_competencias = []
    idx_inicio = 17 if len(columnas) > 17 and str(columnas[17]).startswith("Valor") else 13
    for inicio in range(idx_inicio, len(columnas), 4):
        if inicio + 3 >= len(columnas):
            break
        col_valor, col_esperado, col_brecha, col_ajuste = columnas[inicio:inicio + 4]
        if not str(col_valor).startswith("Valor"):
            continue
        nombre_competencia = grupos[inicio] if inicio < len(grupos) else col_ajuste
        if pd.isna(nombre_competencia) or str(nombre_competencia).startswith("Unnamed"):
            continue
        nombre_competencia = str(nombre_competencia).strip()
        catalogo_competencias.append(nombre_competencia)

        bloque = df[
            [
                "correo",
                "correo_potencial",
                "correo_instancia",
                "colaborador",
                "empresa",
                "cargo",
                "jefe",
                "area",
                "grupo",
                col_valor,
                col_esperado,
                col_brecha,
                col_ajuste,
            ]
        ].copy()
        bloque.columns = [
            "correo",
            "correo_potencial",
            "correo_instancia",
            "colaborador",
            "empresa",
            "cargo",
            "jefe",
            "area",
            "grupo",
            "valor",
            "esperado",
            "brecha",
            "ajuste",
        ]
        bloque["competencia"] = nombre_competencia
        for col in ["valor", "esperado", "brecha", "ajuste"]:
            bloque[col] = pd.to_numeric(bloque[col], errors="coerce")
        bloque = bloque[bloque[["valor", "esperado", "brecha", "ajuste"]].notna().any(axis=1)]
        competencias.append(bloque)

    df_competencias = (
        pd.concat(competencias, ignore_index=True)
        if competencias
        else pd.DataFrame(
            columns=[
                "correo",
                "correo_potencial",
                "correo_instancia",
                "colaborador",
                "empresa",
                "cargo",
                "jefe",
                "area",
                "grupo",
                "valor",
                "esperado",
                "brecha",
                "ajuste",
                "competencia",
            ]
        )
    )
    for col in ["correo", "correo_potencial", "correo_instancia", "colaborador", "empresa", "cargo", "jefe", "area", "grupo"]:
        df_competencias[col] = df_competencias[col].apply(_limpiar_texto)

    for col in ["IQ", "Arquetipo", "Intensidad", "D", "I", "S", "C"]:
        if col not in df.columns:
            df[col] = pd.NA
    if "DISC" not in df.columns:
        df["DISC"] = df.get("Arquetipo", pd.NA)

    df_personas = df[
        [
            "correo",
            "correo_potencial",
            "correo_instancia",
            "colaborador",
            "identificacion",
            "empresa",
            "cargo",
            "jefe",
            "pais",
            "area",
            "grupo",
            "potencial_2025",
            "evaluacion_potencial",
            "escala_benchmark",
            "escala_potencial",
            "IQ",
            "DISC",
            "Arquetipo",
            "Intensidad",
            "D",
            "I",
            "S",
            "C",
        ]
    ].copy()
    df_personas.columns = [
        "correo",
        "correo_potencial",
        "correo_instancia",
        "colaborador",
        "identificacion",
        "empresa",
        "cargo",
        "jefe",
        "pais",
        "area",
        "grupo",
        "potencial_2025",
        "evaluacion_potencial",
        "escala_benchmark",
        "escala_potencial",
        "iq",
        "disc",
        "arquetipo",
        "intensidad",
        "d",
        "i",
        "s",
        "c",
    ]
    df_personas["disc"] = df_personas["disc"].combine_first(df_personas["arquetipo"])
    df_personas["arquetipo"] = df_personas["arquetipo"].apply(_codigo_arquetipo)
    for col in ["d", "i", "s", "c", "intensidad"]:
        df_personas[col] = pd.to_numeric(df_personas[col], errors="coerce")
    for col in [
        "correo",
        "correo_potencial",
        "correo_instancia",
        "colaborador",
        "empresa",
        "cargo",
        "jefe",
        "pais",
        "area",
        "grupo",
        "escala_benchmark",
        "escala_potencial",
        "iq",
        "disc",
        "arquetipo",
    ]:
        df_personas[col] = df_personas[col].apply(_limpiar_texto)

    for col in ["escala_benchmark", "escala_potencial"]:
        df_personas[col] = df_personas[col].apply(
            lambda valor: MAPA_ESCALA.get(valor.casefold(), valor)
            if isinstance(valor, str)
            else valor
        )

    evaluados = int(df_personas["evaluacion_potencial"].notna().sum())
    return {
        "df_personas": df_personas,
        "df_competencias": df_competencias,
        "resumen": {
            "personas": len(df_personas),
            "evaluados": evaluados,
            "sin_evaluacion": len(df_personas) - evaluados,
            "con_potencial_2025": int(df_personas["potencial_2025"].notna().sum()),
            "con_disc": int(df_personas["disc"].notna().sum()),
            "con_arquetipo": int(df_personas["arquetipo"].notna().sum()),
            "con_iq": int(df_personas["iq"].notna().sum()),
            "competencias_catalogo": len(catalogo_competencias),
            "competencias_con_datos": int(df_competencias["competencia"].nunique()),
        },
        "catalogo_competencias": catalogo_competencias,
    }
