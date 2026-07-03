"""
calculos.py
===========
Motor compartido para Evaluacion 360.

Lo usan:
    - reporte/main.py para generar PDFs individuales.
    - dashboard_360.py para vistas agregadas en Streamlit.
"""

from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------

ESCALA_TRANSFORM = {
    5: 100,
    4: 90,
    3: 85,
    2: 75,
    1: 65,
}

PESOS_BASE = {
    "autoEvaluation": 0.10,
    "bossToSubordinate": 0.40,
    "subordinateToBoss": 0.25,
    "peerToPeer": 0.15,
    "insideClients": 0.10,
}

TIPOS_DISPLAY = {
    "autoEvaluation": "Autoevaluación",
    "bossToSubordinate": "Jefe",
    "subordinateToBoss": "Subordinado",
    "peerToPeer": "Pares",
    "insideClients": "Cliente Interno",
}

BANDAS = [
    (90, 101, "Alto Desempeño", "#1F4E79"),
    (80, 90, "Satisfactorio", "#375623"),
    (70, 80, "Bajo Desempeño", "#7F3F00"),
    (0, 70, "Insatisfactorio", "#7B0000"),
]

HOJAS_EVALUACION = ("Desempeño", "Resultado consulta", "datos")
COLUMNAS_REQUERIDAS = [
    "nombre_colaborador",
    "nombre_seccion",
    "tipo_evaluacion",
    "respuesta_valor",
]
COLUMNAS_EXPORTACION_EVALUAR = [
    "nombre_ciclo",
    "nombre_colaborador",
    "email_colaborador",
    "curp",
    "employee_id",
    "categoria",
    "pregunta_abierta",
    "nombre_seccion",
    "pregunta_texto",
    "tipo_evaluacion",
    "nombre_evaluador",
    "email_evaluador",
    "respuesta_valor",
    "calificacion_porcentaje",
]
ESCALA_DASHBOARD = [
    "Alto desempeño",
    "Desempeño satisfactorio",
    "Bajo desempeño",
    "Desempeño insatisfactorio",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clasificar(puntaje: float) -> dict:
    """Devuelve etiqueta y color para un puntaje dado."""
    for lo, hi, etiqueta, color in BANDAS:
        if lo <= puntaje < hi:
            return {"etiqueta": etiqueta, "color": color}
    return {"etiqueta": "Alto Desempeño", "color": "#1F4E79"}


def limpiar_nombre_competencia(nombre: str) -> str:
    """Elimina prefijos numericos como '2.1 ' del nombre de competencia."""
    import re

    return re.sub(r"^\d+(\.\d+)?\s+", "", str(nombre).strip())


def calcular_pesos_redistribuidos(tipos_presentes: list, weights: dict | None = None) -> dict:
    """
    Redistribuye el peso de tipos faltantes en partes iguales entre los presentes.

    Regla de negocio:
    si faltan calificaciones, sus pesos se suman, se dividen entre las
    calificaciones existentes y ese incremento se suma al peso original
    de cada calificacion existente.
    """
    weights = weights or PESOS_BASE
    tipos_unicos = list(dict.fromkeys(tipos_presentes))
    pesos_presentes = {t: weights[t] for t in tipos_unicos if t in weights and weights[t] > 0}
    if not pesos_presentes:
        raise ValueError(f"Ningun tipo reconocido en: {tipos_presentes}")
    peso_faltante = sum(
        peso for tipo, peso in weights.items()
        if peso > 0 and tipo not in pesos_presentes
    )
    incremento = peso_faltante / len(pesos_presentes)
    return {tipo: peso + incremento for tipo, peso in pesos_presentes.items()}


def _idx_escala(puntaje: float) -> int:
    if puntaje >= 90:
        return 0
    if puntaje >= 80:
        return 1
    if puntaje >= 70:
        return 2
    return 3


# ---------------------------------------------------------------------------
# Lectura y normalizacion de datos
# ---------------------------------------------------------------------------

def normalizar_dataframe(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Limpia una hoja de evaluacion y agrega 'puntaje' y 'competencia'.
    """
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise ValueError(f"Columnas faltantes en el Excel: {faltantes}")

    for col in [
        "nombre_colaborador",
        "nombre_seccion",
        "tipo_evaluacion",
        "nombre_evaluador",
        "respuesta_valor",
    ]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    df["respuesta_valor"] = pd.to_numeric(df["respuesta_valor"], errors="coerce")

    n_antes = len(df)
    df = df[df["respuesta_valor"].isin([1, 2, 3, 4, 5])].copy()
    n_descartadas = n_antes - len(df)
    if verbose and n_descartadas:
        print(f"  ! Se descartaron {n_descartadas} filas con respuesta_valor invalido.")

    df["puntaje"] = df["respuesta_valor"].map(ESCALA_TRANSFORM)
    df["competencia"] = df["nombre_seccion"].apply(limpiar_nombre_competencia)
    return df


def leer_excel(ruta: str | Path, sheet_name: str | None = "Resultado consulta") -> pd.DataFrame:
    """
    Lee el Excel de evaluacion y devuelve DataFrame limpio.

    Prioriza 'Desempeño' o 'Resultado consulta' y también acepta archivos
    procesados con hoja 'datos'.
    """
    xls = pd.ExcelFile(ruta)
    hojas = list(xls.sheet_names)

    candidatas = []
    if sheet_name:
        candidatas.append(sheet_name)
    candidatas.extend(h for h in HOJAS_EVALUACION if h not in candidatas)
    candidatas.extend(h for h in hojas if h not in candidatas)

    errores = {}
    for hoja in candidatas:
        if hoja not in hojas:
            continue
        df_hoja = pd.read_excel(xls, sheet_name=hoja, dtype=str)
        try:
            return normalizar_dataframe(df_hoja)
        except ValueError as exc:
            errores[hoja] = str(exc)

    detalle = "; ".join(f"{hoja}: {err}" for hoja, err in errores.items())
    raise ValueError(
        "No se encontro una hoja de evaluacion valida. "
        f"Hojas disponibles: {hojas}. {detalle}"
    )


def leer_exportacion_dashboard(ruta: str | Path) -> pd.DataFrame:
    """Lee y valida el exporte oficial de Fase I generado por Evaluar.com."""
    xls = pd.ExcelFile(ruta)
    hoja = next(
        (nombre for nombre in ("Desempeño", "Resultado consulta") if nombre in xls.sheet_names),
        None,
    )
    if hoja is None:
        raise ValueError(
            "El archivo no corresponde al exporte oficial de Fase I: "
            "debe contener la hoja 'Desempeño'."
        )

    df = pd.read_excel(xls, sheet_name=hoja, dtype=str)
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    faltantes = [col for col in COLUMNAS_EXPORTACION_EVALUAR if col not in df.columns]
    if faltantes:
        raise ValueError(
            "El exporte de Evaluar.com esta incompleto. "
            f"Columnas faltantes: {', '.join(faltantes)}."
        )
    if df.empty:
        raise ValueError(f"La hoja '{hoja}' no contiene registros.")

    abiertas = df["pregunta_abierta"].fillna("").str.strip().str.upper().isin(
        ["SI", "SÍ", "YES", "TRUE", "1"]
    )
    filas_abiertas = int(abiertas.sum())
    df = df.loc[~abiertas].copy()

    campos_clave = [
        "nombre_ciclo",
        "nombre_colaborador",
        "nombre_seccion",
        "pregunta_texto",
        "tipo_evaluacion",
        "respuesta_valor",
    ]
    vacios = {
        col: int((df[col].isna() | df[col].fillna("").str.strip().eq("")).sum())
        for col in campos_clave
    }
    vacios = {col: cantidad for col, cantidad in vacios.items() if cantidad}
    if vacios:
        detalle = ", ".join(f"{col}: {cantidad}" for col, cantidad in vacios.items())
        raise ValueError(f"Hay campos obligatorios vacios en el exporte ({detalle}).")

    respuestas = pd.to_numeric(df["respuesta_valor"], errors="coerce")
    invalidas = ~respuestas.isin([1, 2, 3, 4, 5])
    if invalidas.any():
        raise ValueError(
            f"Hay {int(invalidas.sum())} respuestas fuera de la escala permitida 1-5."
        )

    tipos = set(df["tipo_evaluacion"].str.strip().unique())
    desconocidos = sorted(tipos - set(PESOS_BASE))
    if desconocidos:
        raise ValueError(
            "El archivo contiene tipos de evaluacion no reconocidos: "
            + ", ".join(desconocidos)
        )

    duplicadas = int(df.duplicated().sum())
    if duplicadas:
        raise ValueError(f"El exporte contiene {duplicadas} filas duplicadas.")

    normalizado = normalizar_dataframe(df, verbose=False)
    normalizado.attrs["filas_preguntas_abiertas_omitidas"] = filas_abiertas
    return normalizado


# ---------------------------------------------------------------------------
# Motor para informes PDF
# ---------------------------------------------------------------------------

def calcular_colaborador(df_col: pd.DataFrame) -> dict:
    """
    Calcula el resultado individual de un colaborador.
    """
    df_col = normalizar_dataframe(df_col, verbose=False) if "puntaje" not in df_col.columns else df_col.copy()
    competencias_unicas = sorted(df_col["competencia"].unique())
    tipos_presentes_global = df_col["tipo_evaluacion"].unique().tolist()

    resultados_competencias = {}

    for competencia in competencias_unicas:
        df_comp = df_col[df_col["competencia"] == competencia]

        puntaje_por_tipo = {}
        for tipo in df_comp["tipo_evaluacion"].unique():
            items = df_comp[df_comp["tipo_evaluacion"] == tipo]["puntaje"]
            puntaje_por_tipo[tipo] = round(float(items.mean()), 2)

        tipos_en_comp = list(puntaje_por_tipo.keys())
        pesos = calcular_pesos_redistribuidos(tipos_en_comp)

        puntaje_comp = sum(puntaje_por_tipo[t] * pesos[t] for t in tipos_en_comp)
        puntaje_comp = round(puntaje_comp, 2)

        resultados_competencias[competencia] = {
            "puntaje": puntaje_comp,
            "clasificacion": clasificar(puntaje_comp),
            "desglose_tipo": {
                TIPOS_DISPLAY.get(t, t): puntaje_por_tipo[t]
                for t in PESOS_BASE
                if t in puntaje_por_tipo
            },
            "pesos_aplicados": {
                TIPOS_DISPLAY.get(t, t): round(pesos[t] * 100, 1)
                for t in pesos
            },
        }

    puntajes_comp = [v["puntaje"] for v in resultados_competencias.values()]
    puntaje_global = round(float(np.mean(puntajes_comp)), 2)

    desglose_global = {}
    for tipo in PESOS_BASE:
        items = df_col[df_col["tipo_evaluacion"] == tipo]["puntaje"]
        if len(items) > 0:
            desglose_global[TIPOS_DISPLAY[tipo]] = round(float(items.mean()), 2)

    pesos_globales = calcular_pesos_redistribuidos(tipos_presentes_global)

    return {
        "puntaje_global": puntaje_global,
        "clasificacion": clasificar(puntaje_global),
        "competencias": resultados_competencias,
        "desglose_global": desglose_global,
        "pesos_aplicados": {
            TIPOS_DISPLAY.get(t, t): round(pesos_globales[t] * 100, 1)
            for t in pesos_globales
        },
        "tipos_presentes": [TIPOS_DISPLAY.get(t, t) for t in tipos_presentes_global],
        "n_items": len(df_col),
    }


def calcular_todos(df: pd.DataFrame) -> dict:
    """
    Ejecuta el calculo para todos los colaboradores.
    Retorna dict: {nombre_colaborador: resultado}.
    """
    df = normalizar_dataframe(df, verbose=False) if "puntaje" not in df.columns else df.copy()
    resultados = {}
    for nombre, grupo in df.groupby("nombre_colaborador"):
        print(f"  -> Calculando: {nombre}")
        resultados[nombre] = calcular_colaborador(grupo)
    return resultados


# ---------------------------------------------------------------------------
# Motor para dashboard agregado
# ---------------------------------------------------------------------------

def calcular_items(df: pd.DataFrame, weights: dict | None = None) -> pd.DataFrame:
    """Calcula el puntaje ponderado por ítem para el conjunto de filas recibido."""
    df = normalizar_dataframe(df, verbose=False) if "puntaje" not in df.columns else df.copy()
    weights = weights or PESOS_BASE
    tipos_activos = {tipo: peso for tipo, peso in weights.items() if peso > 0}

    paso_item = (
        df.groupby(["competencia", "pregunta_texto", "tipo_evaluacion"])["puntaje"]
        .mean()
        .reset_index()
        .rename(columns={"puntaje": "prom_item_tipo"})
    )

    registros = []
    for (competencia, item), grupo in paso_item.groupby(["competencia", "pregunta_texto"]):
        presentes = [tipo for tipo in tipos_activos if tipo in grupo["tipo_evaluacion"].values]
        if not presentes:
            continue
        pesos_redistribuidos = calcular_pesos_redistribuidos(presentes, weights)
        puntaje = sum(
            grupo.loc[grupo["tipo_evaluacion"] == tipo, "prom_item_tipo"].iloc[0]
            * pesos_redistribuidos[tipo]
            for tipo in presentes
        )
        registros.append({"competencia": competencia, "item": item, "puntaje": puntaje})

    if not registros:
        return pd.DataFrame(columns=["competencia", "item", "puntaje"])
    return pd.DataFrame(registros).sort_values("puntaje", ascending=False)


def calcular_dashboard(df: pd.DataFrame, weights: dict | None = None) -> dict:
    """
    Calcula los indicadores agregados usados por dashboard_360.py.
    """
    df = normalizar_dataframe(df, verbose=False) if "puntaje" not in df.columns else df.copy()
    weights = weights or PESOS_BASE
    tipos_activos = {t: w for t, w in weights.items() if w > 0}

    paso1 = (
        df.groupby(["nombre_colaborador", "competencia", "tipo_evaluacion"])
        ["puntaje"]
        .mean()
        .reset_index()
        .rename(columns={"puntaje": "prom_items"})
    )

    registros = []
    for (col, comp), grp in paso1.groupby(["nombre_colaborador", "competencia"]):
        presentes = [t for t in tipos_activos if t in grp["tipo_evaluacion"].values]
        if not presentes:
            continue
        pesos_redistribuidos = calcular_pesos_redistribuidos(presentes, weights)
        puntaje = 0.0
        desglose = {}
        for tipo in presentes:
            valor = grp.loc[grp["tipo_evaluacion"] == tipo, "prom_items"].values[0]
            puntaje += valor * pesos_redistribuidos[tipo]
            desglose[tipo] = valor
        registros.append({
            "colaborador": col,
            "competencia": comp,
            "puntaje": puntaje,
            **{f"tipo_{tipo}": desglose.get(tipo) for tipo in tipos_activos},
        })

    df_comp = pd.DataFrame(registros)
    if df_comp.empty:
        raise ValueError("No hay datos validos para calcular indicadores.")

    df_global = (
        df_comp.groupby("colaborador")["puntaje"]
        .mean()
        .reset_index()
        .rename(columns={"puntaje": "global"})
        .sort_values("global", ascending=False)
    )

    df_comp_prom = (
        df_comp.groupby("competencia")["puntaje"]
        .mean()
        .reset_index()
        .rename(columns={"puntaje": "prom_comp"})
        .sort_values("prom_comp", ascending=False)
    )

    rel_prom = {}
    for tipo in tipos_activos:
        col_t = f"tipo_{tipo}"
        if col_t in df_comp.columns:
            vals = df_comp[col_t].dropna()
            if len(vals):
                rel_prom[tipo] = vals.mean()

    comp_rel = {}
    for tipo in tipos_activos:
        col_t = f"tipo_{tipo}"
        if col_t in df_comp.columns:
            comp_rel[tipo] = (
                df_comp.groupby("competencia")[col_t]
                .mean()
                .dropna()
                .to_dict()
            )

    df_items = calcular_items(df, weights)

    df_global["escala_idx"] = df_global["global"].apply(_idx_escala)
    df_global["escala"] = df_global["escala_idx"].apply(lambda i: ESCALA_DASHBOARD[i])

    ciclo = df["nombre_ciclo"].iloc[0] if "nombre_ciclo" in df.columns else "Evaluacion 360"

    return dict(
        ciclo=ciclo,
        resumen_fuente={
            "filas": len(df),
            "colaboradores": df["nombre_colaborador"].nunique(),
            "competencias": df["competencia"].nunique(),
            "items": df["pregunta_texto"].nunique(),
            "preguntas_abiertas_omitidas": df.attrs.get("filas_preguntas_abiertas_omitidas", 0),
        },
        df_global=df_global,
        df_comp=df_comp,
        df_comp_prom=df_comp_prom,
        rel_prom=rel_prom,
        comp_rel=comp_rel,
        df_items=df_items,
        df_fuente=df,
        tipos_activos=tipos_activos,
        colaboradores=df_global["colaborador"].tolist(),
        competencias=df_comp_prom["competencia"].tolist(),
    )


# ---------------------------------------------------------------------------
# Validacion por consola
# ---------------------------------------------------------------------------

def imprimir_resultado(nombre: str, resultado: dict):
    """Imprime el resultado de un colaborador de forma legible."""
    sep = "-" * 70
    print(f"\n{sep}")
    print(f"  COLABORADOR: {nombre}")
    print(
        f"  Puntaje global: {resultado['puntaje_global']} "
        f"-> {resultado['clasificacion']['etiqueta']}"
    )
    print(f"  Items procesados: {resultado['n_items']}")

    print("\n  Pesos aplicados:")
    for tipo, peso in resultado["pesos_aplicados"].items():
        print(f"    {tipo:<25} {peso}%")

    print("\n  Desglose global por tipo de evaluador:")
    for tipo, pts in resultado["desglose_global"].items():
        print(f"    {tipo:<25} {pts}")

    print("\n  Resultados por competencia:")
    print(f"    {'Competencia':<40} {'Puntaje':>8}  {'Banda'}")
    print(f"    {'-'*40} {'-'*8}  {'-'*20}")
    for comp, datos in resultado["competencias"].items():
        print(f"    {comp:<40} {datos['puntaje']:>8}  {datos['clasificacion']['etiqueta']}")
        for tipo, pts in datos["desglose_tipo"].items():
            print(f"      {'- ' + tipo:<40} {pts:>8}")


if __name__ == "__main__":
    import sys

    carpeta = Path("datos")
    excels = list(carpeta.glob("*.xlsx")) if carpeta.exists() else []

    if not excels:
        print("ERROR: No se encontro ningun .xlsx en la carpeta 'datos/'")
        print("       Coloca el archivo exportado de Evaluar.com ahi y vuelve a ejecutar.")
        sys.exit(1)

    ruta = excels[0]
    print(f"Leyendo: {ruta}")

    df_eval = leer_excel(ruta)
    print(f"Filas validas: {len(df_eval)}")
    print(f"Colaboradores: {df_eval['nombre_colaborador'].nunique()}")

    resultados = calcular_todos(df_eval)
    for nombre, resultado in resultados.items():
        imprimir_resultado(nombre, resultado)

    print(f"\n{'-'*70}")
    print("Calculo completado sin errores.")
