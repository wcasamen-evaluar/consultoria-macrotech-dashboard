"""Lectura y normalización de la hoja Potencial para el dashboard."""

from pathlib import Path

import pandas as pd


HOJA_POTENCIAL = "Potencial"
COLUMNAS_PERSONA = [
    "Correo",
    "NOMBRE COMPLETO",
    "No. Identificación",
    "Empresa",
    "Cargo",
    "Jefe",
    "País",
    "Área",
    "Grupo",
    "Potencial 2025",
    "Evaluación de Potencial",
    "Escala Benchmark externo",
    "Escala Potencial",
]
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


def leer_potencial(ruta: str | Path) -> dict:
    """Convierte la matriz ancha de Potencial en tablas de personas y competencias."""
    xls = pd.ExcelFile(ruta)
    if HOJA_POTENCIAL not in xls.sheet_names:
        raise ValueError("El archivo base debe contener la hoja 'Potencial'.")

    df = pd.read_excel(xls, sheet_name=HOJA_POTENCIAL, header=2)
    faltantes = [col for col in COLUMNAS_PERSONA if col not in df.columns]
    if faltantes:
        raise ValueError(
            "La hoja 'Potencial' no tiene la estructura esperada. "
            f"Columnas faltantes: {', '.join(faltantes)}."
        )

    df = df[df["NOMBRE COMPLETO"].notna()].copy()
    df["NOMBRE COMPLETO"] = df["NOMBRE COMPLETO"].astype(str).str.strip()
    if df["NOMBRE COMPLETO"].duplicated().any():
        duplicados = int(df["NOMBRE COMPLETO"].duplicated().sum())
        raise ValueError(f"La hoja 'Potencial' contiene {duplicados} nombres duplicados.")

    for col in ["Potencial 2025", "Evaluación de Potencial"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # A partir de la columna N, cada competencia ocupa cuatro columnas:
    # Valor, Esperado, Brecha y el indicador de ajuste con nombre de competencia.
    columnas = list(df.columns)
    competencias = []
    catalogo_competencias = []
    for inicio in range(13, 254, 4):
        if inicio + 3 >= len(columnas):
            break
        col_valor, col_esperado, col_brecha, competencia = columnas[inicio:inicio + 4]
        if str(competencia).startswith("Unnamed"):
            continue
        catalogo_competencias.append(str(competencia).strip())

        bloque = df[
            [
                "Correo",
                "NOMBRE COMPLETO",
                "Empresa",
                "Cargo",
                "Jefe",
                "Área",
                "Grupo",
                col_valor,
                col_esperado,
                col_brecha,
                competencia,
            ]
        ].copy()
        bloque.columns = [
            "correo",
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
        bloque["competencia"] = str(competencia).strip()
        for col in ["valor", "esperado", "brecha", "ajuste"]:
            bloque[col] = pd.to_numeric(bloque[col], errors="coerce")
        bloque = bloque[bloque[["valor", "esperado", "brecha", "ajuste"]].notna().any(axis=1)]
        competencias.append(bloque)

    df_competencias = (
        pd.concat(competencias, ignore_index=True)
        if competencias
        else pd.DataFrame(
            columns=[
                "correo", "colaborador", "empresa", "cargo", "jefe", "area",
                "grupo", "valor", "esperado", "brecha", "ajuste", "competencia",
            ]
        )
    )
    for col in ["correo", "colaborador", "empresa", "cargo", "jefe", "area", "grupo"]:
        df_competencias[col] = df_competencias[col].apply(
            lambda valor: valor.strip() if isinstance(valor, str) else valor
        )

    df_personas = df[COLUMNAS_PERSONA + ["IQ", "DISC"]].copy()
    df_personas.columns = [
        "correo",
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
    ]
    for col in [
        "correo", "colaborador", "empresa", "cargo", "jefe", "pais", "area",
        "grupo", "escala_benchmark", "escala_potencial", "iq", "disc",
    ]:
        df_personas[col] = df_personas[col].apply(
            lambda valor: valor.strip() if isinstance(valor, str) else valor
        )

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
            "con_iq": int(df_personas["iq"].notna().sum()),
            "competencias_catalogo": len(catalogo_competencias),
            "competencias_con_datos": int(df_competencias["competencia"].nunique()),
        },
        "catalogo_competencias": catalogo_competencias,
    }
