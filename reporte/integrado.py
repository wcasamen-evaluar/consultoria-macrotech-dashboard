"""Consolidacion de datos para informes integrales.

Este modulo reutiliza los motores del dashboard sin importar Streamlit. La
fuente principal es el Excel raiz del proyecto, que contiene 360, Potencial y
Objetivos.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from reporte import calculos as motor_360
from reporte import objetivos as motor_objetivos
from reporte import potencial as motor_potencial


ARCHIVO_EXCEL_PATRON = "Fase_I_Evaluaci*n_360__180__90__copia_.xlsx"

CONFIG_INTEGRADO = {
    "Completa": {
        "tab": "360 + Objetivos + Potencial",
        "sub": "360 30% / Objetivos 30% / Potencial 40%",
    },
    "360+obj": {
        "tab": "360 + Objetivos",
        "sub": "360 50% / Objetivos 50%",
    },
    "360+pot": {
        "tab": "360 + Potencial",
        "sub": "360 60% / Potencial 40%",
    },
    "obj+pot": {
        "tab": "Objetivos + Potencial",
        "sub": "Objetivos 60% / Potencial 40%",
    },
}


NINEBOX_LABELS = {
    1: "Super Estrella",
    2: "Estrella del futuro",
    3: "Enigma",
    4: "Estrella en su área",
    5: "Colaborador clave",
    6: "Dilema",
    7: "Comprometido",
    8: "Eficaz",
    9: "Bajo rendimiento",
}


def resolver_excel_dashboard(ruta_base: str | Path | None = None) -> Path:
    """Devuelve el Excel raiz usado por el dashboard."""
    if ruta_base:
        ruta = Path(ruta_base)
        if ruta.is_file():
            return ruta
        raise FileNotFoundError(f"No se encontro el Excel indicado: {ruta}")

    raiz = Path(__file__).resolve().parents[1]
    candidatos = list(raiz.glob(ARCHIVO_EXCEL_PATRON))
    if not candidatos:
        candidatos = list(raiz.glob("*.xlsx"))
    if not candidatos:
        raise FileNotFoundError("No se encontro ningun Excel en la raiz del proyecto.")
    return candidatos[0]


def normalizar_nombre_match(nombre: object) -> str:
    texto = "" if nombre is None else str(nombre)
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"[^a-zA-Z0-9]+", " ", texto).strip().casefold()
    return re.sub(r"\s+", " ", texto)


def normalizar_email_match(email: object) -> str:
    if email is None or pd.isna(email):
        return ""
    return str(email).strip().casefold()


def _primer_email_serie(series: pd.Series) -> str:
    valores = [normalizar_email_match(v) for v in series.dropna()]
    valores = [v for v in valores if v]
    return valores[0] if valores else ""


def _match_key_from_row(row: pd.Series) -> str:
    for col in ["match_email", "match_email_potencial", "match_email_instancia"]:
        valor = row.get(col)
        if isinstance(valor, str) and valor:
            return f"email:{valor}"
    return f"nombre:{row.get('match_nombre', '')}"


def escala_objetivos_label(valor: float) -> str:
    return motor_objetivos.escala_objetivos_label(valor)


def preparar_resultado_integrado(
    df_360_global: pd.DataFrame,
    df_obj_colab: pd.DataFrame,
    df_potencial: pd.DataFrame,
    df_obj_fuente: pd.DataFrame,
) -> pd.DataFrame:
    cols_360 = [col for col in ["colaborador", "global", "email_colaborador"] if col in df_360_global.columns]
    base_360 = df_360_global[cols_360].rename(
        columns={"colaborador": "colaborador_360", "global": "evd_360"}
    ).copy()
    cols_obj = [col for col in ["colaborador", "email_colaborador", "puntaje", "cargo_objetivo", "jefe"] if col in df_obj_colab.columns]
    base_obj = df_obj_colab[cols_obj].rename(
        columns={"colaborador": "colaborador_obj", "puntaje": "objetivos"}
    ).copy()
    cols_pot = [
        col
        for col in [
            "colaborador", "correo", "correo_potencial", "correo_instancia",
            "evaluacion_potencial", "empresa", "pais", "grupo", "cargo", "area"
        ]
        if col in df_potencial.columns
    ]
    base_pot = df_potencial[cols_pot].rename(
        columns={"colaborador": "colaborador_pot", "evaluacion_potencial": "potencial"}
    ).copy()

    for df, col_nombre in [
        (base_360, "colaborador_360"),
        (base_obj, "colaborador_obj"),
        (base_pot, "colaborador_pot"),
    ]:
        if df.empty:
            df["match_nombre"] = []
            continue
        df["match_nombre"] = df[col_nombre].map(normalizar_nombre_match)
    if "email_colaborador" in base_360.columns:
        base_360["match_email"] = base_360["email_colaborador"].map(normalizar_email_match)
    else:
        base_360["match_email"] = ""
    if "email_colaborador" in base_obj.columns:
        base_obj["match_email"] = base_obj["email_colaborador"].map(normalizar_email_match)
    else:
        base_obj["match_email"] = ""
    for col in ["correo", "correo_potencial", "correo_instancia"]:
        if col not in base_pot.columns:
            base_pot[col] = ""
    base_pot["match_email"] = base_pot["correo"].map(normalizar_email_match)
    base_pot["match_email_potencial"] = base_pot["correo_potencial"].map(normalizar_email_match)
    base_pot["match_email_instancia"] = base_pot["correo_instancia"].map(normalizar_email_match)

    for df in [base_360, base_obj, base_pot]:
        df["match_key"] = df.apply(_match_key_from_row, axis=1)
        df.drop_duplicates("match_key", inplace=True)

    aliases = []
    for _, row in base_pot.iterrows():
        principal = row["match_key"]
        for col in ["match_email", "match_email_potencial", "match_email_instancia"]:
            email = row.get(col)
            if isinstance(email, str) and email:
                aliases.append({"match_key": f"email:{email}", "pot_match_key": principal})
        aliases.append({"match_key": f"nombre:{row.get('match_nombre', '')}", "pot_match_key": principal})
    df_alias = pd.DataFrame(aliases).drop_duplicates("match_key") if aliases else pd.DataFrame(columns=["match_key", "pot_match_key"])
    base_pot = base_pot.rename(columns={"match_key": "pot_match_key"})

    def canonicalizar(df: pd.DataFrame) -> pd.DataFrame:
        canon = df.merge(df_alias, on="match_key", how="left")
        if "match_nombre" in canon.columns and not df_alias.empty:
            alias_nombre = df_alias.rename(
                columns={"match_key": "match_key_nombre", "pot_match_key": "pot_match_key_nombre"}
            )
            canon["match_key_nombre"] = "nombre:" + canon["match_nombre"].fillna("").astype(str)
            canon = canon.merge(alias_nombre, on="match_key_nombre", how="left")
            canon["pot_match_key"] = canon["pot_match_key"].fillna(canon["pot_match_key_nombre"])
            canon = canon.drop(columns=["match_key_nombre", "pot_match_key_nombre"], errors="ignore")
        canon["canonical_key"] = canon["pot_match_key"].fillna(canon["match_key"])
        return canon.drop(columns=["pot_match_key"], errors="ignore")

    base_360 = canonicalizar(base_360)
    base_obj = canonicalizar(base_obj)
    base_pot["canonical_key"] = base_pot["pot_match_key"]

    integrado = base_360.merge(base_obj, on="canonical_key", how="outer", suffixes=("_360", "_obj"))
    integrado = integrado.merge(base_pot, on="canonical_key", how="outer")
    integrado["pot_match_key"] = integrado["canonical_key"]
    if "match_nombre" not in integrado.columns:
        integrado["match_nombre"] = ""
    integrado["match_nombre"] = integrado.get("match_nombre_360", pd.Series(dtype=object)).combine_first(
        integrado.get("match_nombre_obj", pd.Series(dtype=object))
    ).combine_first(integrado.get("match_nombre", pd.Series(dtype=object)))
    integrado["colaborador"] = integrado["colaborador_360"].combine_first(integrado["colaborador_obj"])
    integrado["colaborador"] = integrado["colaborador"].combine_first(integrado["colaborador_pot"])

    evaluadores = (
        set(df_obj_fuente["nombre_evaluador"].dropna().map(normalizar_nombre_match))
        if not df_obj_fuente.empty and "nombre_evaluador" in df_obj_fuente.columns
        else set()
    )
    integrado["gente_a_cargo"] = integrado["colaborador"].map(
        lambda nombre: "SI" if normalizar_nombre_match(nombre) in evaluadores else "NO"
    )

    def etiqueta(row: pd.Series) -> str:
        tiene_360 = pd.notna(row.get("evd_360")) and row.get("evd_360") > 0
        tiene_obj = pd.notna(row.get("objetivos")) and row.get("objetivos") > 0
        tiene_pot = pd.notna(row.get("potencial")) and row.get("potencial") > 0
        if tiene_360 and tiene_obj and tiene_pot:
            return "Completa"
        if tiene_360 and tiene_obj:
            return "360+obj"
        if tiene_360 and tiene_pot:
            return "360+pot"
        if tiene_obj and tiene_pot:
            return "obj+pot"
        if tiene_360:
            return "Solo 360"
        if tiene_obj:
            return "Solo obj"
        if tiene_pot:
            return "Solo pot"
        return ""

    integrado["etiqueta_integrada"] = integrado.apply(etiqueta, axis=1)

    def calcular_integrada(row: pd.Series) -> float:
        etiqueta_val = row["etiqueta_integrada"]
        if etiqueta_val == "Completa":
            return round(row["evd_360"] * 0.30 + row["objetivos"] * 0.30 + row["potencial"] * 0.40, 0)
        if etiqueta_val == "360+obj":
            return round(row["evd_360"] * 0.50 + row["objetivos"] * 0.50, 0)
        if etiqueta_val == "360+pot":
            return round(row["evd_360"] * 0.60 + row["potencial"] * 0.40, 0)
        if etiqueta_val == "obj+pot":
            return round(row["objetivos"] * 0.60 + row["potencial"] * 0.40, 0)
        return np.nan

    integrado["integrada"] = integrado.apply(calcular_integrada, axis=1)
    integrado["escala_integrada"] = integrado["integrada"].apply(escala_objetivos_label)
    for col in ["empresa", "pais", "grupo", "cargo_objetivo", "jefe", "cargo", "area"]:
        if col not in integrado.columns:
            integrado[col] = "Sin dato"
        integrado[col] = integrado[col].fillna("Sin dato").replace("", "Sin dato")
    return integrado.sort_values("integrada", ascending=False, na_position="last")


def preparar_ninebox(df_360_global: pd.DataFrame, df_potencial: pd.DataFrame) -> pd.DataFrame:
    desempeno = df_360_global[["colaborador", "global"]].copy()
    potencial = df_potencial[["colaborador", "evaluacion_potencial"]].copy()
    desempeno["match_nombre"] = desempeno["colaborador"].map(normalizar_nombre_match)
    potencial["match_nombre"] = potencial["colaborador"].map(normalizar_nombre_match)
    desempeno = desempeno.drop_duplicates("match_nombre")
    potencial = potencial.drop_duplicates("match_nombre")
    merged = desempeno.merge(potencial, on="match_nombre", how="inner", suffixes=("_360", "_potencial"))
    merged = merged.dropna(subset=["global", "evaluacion_potencial"]).copy()
    merged = merged.rename(
        columns={
            "colaborador_360": "colaborador",
            "global": "desempeno_360",
            "evaluacion_potencial": "potencial",
        }
    )
    return merged[["colaborador", "match_nombre", "potencial", "desempeno_360"]].sort_values("colaborador")


def clasificar_ninebox(df_ninebox: pd.DataFrame) -> pd.DataFrame:
    if df_ninebox.empty or len(df_ninebox) < 2:
        df = df_ninebox.copy()
        df["cuadrante"] = np.nan
        df["cuadrante_nombre"] = ""
        return df

    cortes = {
        "potencial_sup": df_ninebox["potencial"].mean() + df_ninebox["potencial"].std(ddof=1),
        "potencial_inf": df_ninebox["potencial"].mean() - df_ninebox["potencial"].std(ddof=1),
        "desempeno_sup": df_ninebox["desempeno_360"].mean() + df_ninebox["desempeno_360"].std(ddof=1),
        "desempeno_inf": df_ninebox["desempeno_360"].mean() - df_ninebox["desempeno_360"].std(ddof=1),
    }

    def nivel(valor: float, inferior: float, superior: float) -> str:
        if valor >= superior:
            return "alto"
        if valor < inferior:
            return "bajo"
        return "medio"

    mapa = {
        ("alto", "alto"): 1, ("alto", "medio"): 2, ("alto", "bajo"): 3,
        ("medio", "alto"): 4, ("medio", "medio"): 5, ("medio", "bajo"): 6,
        ("bajo", "alto"): 7, ("bajo", "medio"): 8, ("bajo", "bajo"): 9,
    }
    df = df_ninebox.copy()
    df["nivel_potencial"] = df["potencial"].apply(lambda v: nivel(v, cortes["potencial_inf"], cortes["potencial_sup"]))
    df["nivel_desempeno"] = df["desempeno_360"].apply(lambda v: nivel(v, cortes["desempeno_inf"], cortes["desempeno_sup"]))
    df["cuadrante"] = [mapa[(pot, desp)] for pot, desp in zip(df["nivel_potencial"], df["nivel_desempeno"])]
    df["cuadrante_nombre"] = df["cuadrante"].map(NINEBOX_LABELS)
    return df


def _registro_por_match(df: pd.DataFrame, match: str) -> dict[str, Any]:
    if df.empty or "match_nombre" not in df.columns:
        return {}
    filas = df[df["match_nombre"] == match]
    if filas.empty:
        return {}
    return filas.iloc[0].dropna().to_dict()


def _registro_por_llaves(df: pd.DataFrame, match_nombre: str, emails: set[str]) -> dict[str, Any]:
    if df.empty:
        return {}
    datos = df
    for col in [
        "match_email",
        "match_email_360",
        "match_email_obj",
        "match_email_potencial",
        "match_email_instancia",
        "match_correo",
        "match_correo_potencial",
        "match_correo_instancia",
    ]:
        if col in datos.columns and emails:
            filas = datos[datos[col].isin(emails)]
            if not filas.empty:
                return filas.iloc[0].dropna().to_dict()
    if "match_key" in datos.columns and emails:
        filas = datos[datos["match_key"].isin({f"email:{email}" for email in emails})]
        if not filas.empty:
            return filas.iloc[0].dropna().to_dict()
    return _registro_por_match(datos, match_nombre)


def _dato_real(*valores: Any, default: str = "") -> Any:
    for valor in valores:
        if valor is None:
            continue
        if isinstance(valor, float) and pd.isna(valor):
            continue
        texto = str(valor).strip()
        if not texto:
            continue
        if texto.casefold() in {"sin dato", "nan", "none", "null", "-"}:
            continue
        return valor
    return default


def _competencias_potencial_colaborador(df_comp: pd.DataFrame, match: str) -> list[dict[str, Any]]:
    if df_comp.empty:
        return []
    datos = df_comp.copy()
    datos["match_nombre"] = datos["colaborador"].map(normalizar_nombre_match)
    datos = datos[datos["match_nombre"] == match].copy()
    if datos.empty:
        return []
    datos = datos[datos[["valor", "esperado", "brecha", "ajuste"]].notna().any(axis=1)].copy()
    if datos.empty:
        return []
    datos = datos.sort_values(["competencia"], ascending=True)
    return datos.to_dict("records")


def _competencias_potencial_por_llaves(df_comp: pd.DataFrame, match: str, emails: set[str]) -> list[dict[str, Any]]:
    if df_comp.empty:
        return []
    datos = df_comp.copy()
    for col in ["correo", "correo_potencial", "correo_instancia"]:
        if col in datos.columns:
            datos[f"match_{col}"] = datos[col].map(normalizar_email_match)
    if emails:
        mask = pd.Series(False, index=datos.index)
        for col in ["match_correo", "match_correo_potencial", "match_correo_instancia"]:
            if col in datos.columns:
                mask = mask | datos[col].isin(emails)
        datos_email = datos[mask].copy()
        if not datos_email.empty:
            datos_email = datos_email[datos_email[["valor", "esperado", "brecha", "ajuste"]].notna().any(axis=1)]
            return datos_email.sort_values(["competencia"], ascending=True).to_dict("records")
    return _competencias_potencial_colaborador(df_comp, match)


def _calcular_cap(competencias: list[dict[str, Any]]) -> dict[str, Any]:
    valores = []
    for item in competencias:
        try:
            valor = float(item.get("ajuste"))
        except (TypeError, ValueError):
            continue
        if pd.notna(valor):
            valores.append(valor)
    if not valores:
        return {"score": None, "percent": None, "competencias": 0}
    score = float(np.mean(valores))
    return {
        "score": round(score, 4),
        "percent": round(score * 100, 1),
        "competencias": len(valores),
    }


def _items_360_colaborador(
    df_colaborador: pd.DataFrame,
    df_items_org: pd.DataFrame,
) -> dict[str, list[dict[str, Any]]]:
    if df_colaborador.empty:
        return {}
    df_ind = motor_360.calcular_items(df_colaborador, motor_360.PESOS_BASE)
    if df_ind.empty:
        return {}

    org_map = {
        (normalizar_nombre_match(row["competencia"]), normalizar_nombre_match(row["item"])): float(row["puntaje"])
        for _, row in df_items_org.iterrows()
    }
    orden_items = (
        df_colaborador[["competencia", "pregunta_texto"]]
        .drop_duplicates()
        .assign(
            comp_key=lambda df: df["competencia"].map(normalizar_nombre_match),
            item_key=lambda df: df["pregunta_texto"].map(normalizar_nombre_match),
            orden=range(len(df_colaborador[["competencia", "pregunta_texto"]].drop_duplicates())),
        )
    )
    orden_map = {
        (row["comp_key"], row["item_key"]): int(row["orden"])
        for _, row in orden_items.iterrows()
    }

    items = {}
    for _, row in df_ind.iterrows():
        comp = str(row["competencia"])
        item = str(row["item"])
        key = (normalizar_nombre_match(comp), normalizar_nombre_match(item))
        items.setdefault(comp, []).append(
            {
                "item": item,
                "puntaje": round(float(row["puntaje"]), 2),
                "organizacion": round(float(org_map.get(key, row["puntaje"])), 2),
                "orden": orden_map.get(key, 9999),
            }
        )
    for comp_items in items.values():
        comp_items.sort(key=lambda item: item["orden"])
        for item in comp_items:
            item.pop("orden", None)
    return items


def _objetivos_detalle_colaborador(df_objetivos: pd.DataFrame, match: str) -> list[dict[str, Any]]:
    if df_objetivos.empty:
        return []
    datos = df_objetivos.copy()
    datos["match_nombre"] = datos["nombre_colaborador"].map(normalizar_nombre_match)
    datos = datos[datos["match_nombre"] == match].copy()
    if datos.empty:
        return []
    detalle = (
        datos.groupby("objetivo", dropna=False)
        .agg(puntaje=("puntaje", "mean"))
        .reset_index()
        .sort_values("objetivo")
    )
    return [
        {"objetivo": str(row["objetivo"]), "puntaje": round(float(row["puntaje"]), 2)}
        for _, row in detalle.iterrows()
    ]


def _objetivos_detalle_por_llaves(df_objetivos: pd.DataFrame, match: str, emails: set[str]) -> list[dict[str, Any]]:
    if df_objetivos.empty:
        return []
    if "email_colaborador" in df_objetivos.columns and emails:
        datos = df_objetivos.copy()
        datos["match_email"] = datos["email_colaborador"].map(normalizar_email_match)
        datos = datos[datos["match_email"].isin(emails)].copy()
        if not datos.empty:
            detalle = (
                datos.groupby("objetivo", dropna=False)
                .agg(puntaje=("puntaje", "mean"))
                .reset_index()
                .sort_values("objetivo")
            )
            return [
                {"objetivo": str(row["objetivo"]), "puntaje": round(float(row["puntaje"]), 2)}
                for _, row in detalle.iterrows()
            ]
    return _objetivos_detalle_colaborador(df_objetivos, match)


def cargar_base_reportes(ruta_excel: str | Path | None = None) -> dict[str, Any]:
    ruta = resolver_excel_dashboard(ruta_excel)
    df_360 = motor_360.leer_exportacion_dashboard(ruta)
    res_360 = motor_360.calcular_dashboard(df_360, motor_360.PESOS_BASE)
    emails_360 = (
        df_360.groupby("nombre_colaborador", dropna=False)["email_colaborador"]
        .agg(_primer_email_serie)
        .reset_index()
        .rename(columns={"nombre_colaborador": "colaborador"})
    )
    res_360["df_global"] = res_360["df_global"].merge(emails_360, on="colaborador", how="left")
    res_360["df_global"]["escala"] = res_360["df_global"]["escala_idx"].apply(
        lambda i: motor_360.ESCALA_DASHBOARD[i]
    )
    resultados_360 = {
        nombre: motor_360.calcular_colaborador(grupo)
        for nombre, grupo in df_360.groupby("nombre_colaborador")
    }
    grupos_360 = {nombre: grupo.copy() for nombre, grupo in df_360.groupby("nombre_colaborador")}
    promedio_competencias_360 = {
        normalizar_nombre_match(row["competencia"]): float(row["prom_comp"])
        for _, row in res_360["df_comp_prom"].iterrows()
    }
    res_potencial = motor_potencial.leer_potencial(ruta)
    res_objetivos = motor_objetivos.leer_objetivos(ruta)
    df_integrado = preparar_resultado_integrado(
        res_360["df_global"],
        res_objetivos["df_colaboradores"],
        res_potencial["df_personas"],
        res_objetivos["df_fuente"],
    )
    df_ninebox = clasificar_ninebox(preparar_ninebox(res_360["df_global"], res_potencial["df_personas"]))

    for df, col in [
        (res_potencial["df_personas"], "colaborador"),
        (res_objetivos["df_colaboradores"], "colaborador"),
        (df_integrado, "colaborador"),
        (df_ninebox, "colaborador"),
    ]:
        if not df.empty:
            df["match_nombre"] = df[col].map(normalizar_nombre_match)
    if not res_potencial["df_personas"].empty:
        for col in ["correo", "correo_potencial", "correo_instancia"]:
            if col in res_potencial["df_personas"].columns:
                res_potencial["df_personas"][f"match_{col}"] = res_potencial["df_personas"][col].map(normalizar_email_match)
        res_potencial["df_personas"]["match_email"] = res_potencial["df_personas"].get("match_correo", "")
        res_potencial["df_personas"]["match_email_potencial"] = res_potencial["df_personas"].get("match_correo_potencial", "")
        res_potencial["df_personas"]["match_email_instancia"] = res_potencial["df_personas"].get("match_correo_instancia", "")
    if not res_objetivos["df_colaboradores"].empty and "email_colaborador" in res_objetivos["df_colaboradores"].columns:
        res_objetivos["df_colaboradores"]["match_email"] = res_objetivos["df_colaboradores"]["email_colaborador"].map(normalizar_email_match)

    reportes = {}
    for nombre, resultado_360 in resultados_360.items():
        match = normalizar_nombre_match(nombre)
        emails = {
            normalizar_email_match(valor)
            for valor in grupos_360.get(nombre, pd.DataFrame()).get("email_colaborador", pd.Series(dtype=object)).dropna().unique()
            if normalizar_email_match(valor)
        }
        integrado = _registro_por_llaves(df_integrado, match, emails)
        potencial = _registro_por_llaves(res_potencial["df_personas"], match, emails)
        objetivos = _registro_por_llaves(res_objetivos["df_colaboradores"], match, emails)
        ninebox = _registro_por_match(df_ninebox, match)
        ficha = {
            "cargo": _dato_real(integrado.get("cargo"), integrado.get("cargo_objetivo"), potencial.get("cargo"), objetivos.get("cargo_objetivo")),
            "area": _dato_real(integrado.get("area"), potencial.get("area")),
            "empresa": _dato_real(integrado.get("empresa"), potencial.get("empresa"), default="Macrotech"),
            "pais": _dato_real(integrado.get("pais"), potencial.get("pais")),
            "grupo": _dato_real(integrado.get("grupo"), potencial.get("grupo")),
            "jefe": _dato_real(integrado.get("jefe"), potencial.get("jefe"), objetivos.get("jefe")),
            "gente_a_cargo": _dato_real(integrado.get("gente_a_cargo")),
        }
        competencias_potencial = _competencias_potencial_por_llaves(
            res_potencial["df_competencias"], match, emails
        )
        reportes[nombre] = {
            "resultado_360": resultado_360,
            "ficha": ficha,
            "integrado": integrado,
            "potencial": potencial,
            "objetivos": objetivos,
            "objetivos_detalle": _objetivos_detalle_por_llaves(res_objetivos["df_fuente"], match, emails),
            "ninebox": ninebox,
            "cap": _calcular_cap(competencias_potencial),
            "promedios_organizacion_360": promedio_competencias_360,
            "items_360": _items_360_colaborador(
                grupos_360.get(nombre, pd.DataFrame()),
                res_360["df_items"],
            ),
            "competencias_potencial": sorted(
                competencias_potencial,
                key=lambda item: (
                    float(item.get("ajuste")) if pd.notna(item.get("ajuste")) else 999,
                    str(item.get("competencia")),
                ),
            ),
        }

    return {
        "ruta_excel": ruta,
        "res_360": res_360,
        "res_potencial": res_potencial,
        "res_objetivos": res_objetivos,
        "df_integrado": df_integrado,
        "df_ninebox": df_ninebox,
        "reportes": reportes,
    }
