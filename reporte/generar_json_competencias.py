"""Genera el catalogo JSON de competencias para los informes.

Entrada esperada:
    reporte/datos/competencias.xlsx

Hojas:
    - Competencias: id, name, definition
    - Niveles: CompetenceName, competenceId, valueFrom, valueTo, Etiqueta, interpretation
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_XLSX = BASE_DIR / "datos" / "competencias.xlsx"
INPUT_RECOMMENDATIONS_XLSX = BASE_DIR / "datos" / "recomendaciones.xlsx"
INPUT_SUPPLEMENTAL_RECOMMENDATIONS = BASE_DIR / "datos" / "recomendaciones_suplementarias.tsv"
OUTPUT_JSON = BASE_DIR / "assets" / "competencias_interpretacion.json"

RECOMMENDATIONS_BY_LEVEL = {
    "Muy desarrollado": (
        "Capitalizar esta competencia como fortaleza: asignar retos de mayor "
        "alcance, compartir buenas practicas y usarla como referencia para otros."
    ),
    "Desarrollado": (
        "Mantener el nivel actual con practica deliberada, seguimiento periodico "
        "y oportunidades de aplicacion en situaciones de mayor complejidad."
    ),
    "En desarrollo": (
        "Definir un plan de mejora concreto con acciones observables, apoyo del "
        "lider y seguimiento de avances en un plazo corto."
    ),
    "Moderadamente desarrollado": (
        "Consolidar la competencia mediante practica frecuente, retroalimentacion "
        "especifica y exposicion gradual a situaciones de mayor exigencia."
    ),
    "Poco desarrollado": (
        "Priorizar esta brecha con acompanamiento cercano, formacion especifica "
        "y metas simples que permitan construir la competencia de forma gradual."
    ),
    "Muy poco desarrollado": (
        "Iniciar un plan de fortalecimiento desde bases esenciales, con actividades "
        "guiadas, objetivos de corto plazo y seguimiento cercano."
    ),
}

LEVEL_LABEL_TRANSLATIONS = {
    "HIGH_DEVELOPED": "Muy desarrollado",
    "DEVELOPED": "Desarrollado",
    "MODERATELY_DEVELOPED": "Moderadamente desarrollado",
    "DEVELOPING": "En desarrollo",
    "UNDER_DEVELOPED": "Poco desarrollado",
    "VERY_LITTLE_DEVELOPED": "Muy poco desarrollado",
}

SUPPLEMENTAL_LEVELS = {
    438: [
        {
            "type": "HIGH_DEVELOPED",
            "valueFrom": 9,
            "valueTo": 10.1,
            "interpretation": (
                "<p>La persona evaluada tiene un dominio excepcional del ingl&eacute;s. "
                "Puede interpretar con facilidad textos altamente complejos, emplear "
                "vocabulario y gram&aacute;tica avanzada con precisi&oacute;n y comunicarse "
                "con exactitud en cualquier contexto, incluyendo &aacute;mbitos t&eacute;cnicos "
                "y literarios.&nbsp;</p><p><em>Este nivel equivale a C2 en el Marco "
                "Com&uacute;n Europeo de Referencia para las Lenguas.</em></p>"
            ),
        },
        {
            "type": "DEVELOPED",
            "valueFrom": 8,
            "valueTo": 9,
            "interpretation": (
                "<p>La persona evaluada tiene un dominio avanzado del ingl&eacute;s. "
                "Demuestra fluidez y precisi&oacute;n en la comprensi&oacute;n y uso del "
                "vocabulario, la gram&aacute;tica y la lectura. Maneja textos y situaciones "
                "complejas con confianza y coherencia.&nbsp;</p><p><em>Este nivel equivale "
                "a C1 en el Marco Com&uacute;n Europeo de Referencia para las Lenguas.</em></p>"
            ),
        },
        {
            "type": "MODERATELY_DEVELOPED",
            "valueFrom": 7,
            "valueTo": 8,
            "interpretation": (
                "<p>La persona evaluada tiene un buen dominio del ingl&eacute;s, con la "
                "capacidad de comprender textos moderadamente complejos, usar vocabulario "
                "variado y aplicar estructuras gramaticales con precisi&oacute;n en la "
                "mayor&iacute;a de los contextos. Los errores ocasionales no impiden una "
                "comunicaci&oacute;n efectiva.&nbsp;</p><p><em>Este nivel equivale a B2 en "
                "el Marco Com&uacute;n Europeo de Referencia para las Lenguas.</em></p>"
            ),
        },
        {
            "type": "DEVELOPING",
            "valueFrom": 5,
            "valueTo": 7,
            "interpretation": (
                "<p>La persona evaluada muestra un progreso moderado en ingl&eacute;s. "
                "Puede interpretar textos simples, aplicar estructuras gramaticales comunes "
                "y usar vocabulario funcional en contextos cotidianos. A pesar de estas "
                "habilidades, a&uacute;n comete errores y muestra limitaciones al enfrentarse "
                "a situaciones moderadamente complejas.&nbsp;</p><p><em>Este nivel equivale "
                "a B1 en el Marco Com&uacute;n Europeo de Referencia para las Lenguas.</em></p>"
            ),
        },
        {
            "type": "UNDER_DEVELOPED",
            "valueFrom": 4,
            "valueTo": 5,
            "interpretation": (
                "<p>La persona evaluada demuestra un conocimiento limitado del ingl&eacute;s. "
                "Puede comprender y usar vocabulario b&aacute;sico, aplicar estructuras "
                "gramaticales simples e interpretar textos cortos y directos. Sin embargo, "
                "enfrenta desaf&iacute;os en fluidez y precisi&oacute;n al comunicarse.&nbsp;"
                "</p><p><em>Este nivel equivale a A2 en el Marco Com&uacute;n Europeo de "
                "Referencia para las Lenguas.</em></p>"
            ),
        },
        {
            "type": "VERY_LITTLE_DEVELOPED",
            "valueFrom": 0,
            "valueTo": 4,
            "interpretation": (
                "<p>La persona evaluada tiene un conocimiento m&iacute;nimo del ingl&eacute;s "
                "y enfrenta dificultades significativas en vocabulario, gram&aacute;tica y "
                "comprensi&oacute;n lectora. Su capacidad para interpretar textos, usar "
                "gram&aacute;tica b&aacute;sica y emplear vocabulario adecuado es muy limitada, "
                "lo que impide una comunicaci&oacute;n efectiva.&nbsp;</p><p><em>Este nivel "
                "equivale a A1 en el Marco Com&uacute;n Europeo de Referencia para las Lenguas."
                "</em></p>"
            ),
        },
    ]
}

GAP_RULES = [
    {
        "id": "fortaleza",
        "from": 0.5,
        "to": None,
        "label": "Fortaleza frente al perfil",
        "recommendation": (
            "Aprovechar como diferenciador y buscar escenarios donde el colaborador "
            "pueda transferir esta capacidad al equipo."
        ),
    },
    {
        "id": "ajustada",
        "from": -0.49,
        "to": 0.49,
        "label": "Ajustada al perfil",
        "recommendation": (
            "Mantener el desempeno actual con practica continua y seguimiento "
            "regular para sostener el ajuste."
        ),
    },
    {
        "id": "brecha_desarrollo",
        "from": -1.49,
        "to": -0.5,
        "label": "Brecha de desarrollo",
        "recommendation": (
            "Trabajar acciones puntuales de mejora, priorizando los comportamientos "
            "que mas impactan el rol."
        ),
    },
    {
        "id": "brecha_prioritaria",
        "from": None,
        "to": -1.5,
        "label": "Brecha prioritaria",
        "recommendation": (
            "Incluir en el plan de desarrollo inmediato con apoyo del lider, "
            "practica guiada y evidencia de avance."
        ),
    },
]


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return " ".join(str(value).replace("\n", " ").split()).strip()


def clean_html(value: Any) -> str:
    text = unescape(clean_text(value)).replace("\xa0", " ")
    text = re.sub(r"</p>\s*<p[^>]*>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.split()).strip()


def clean_recommendation(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = unescape(str(value)).replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    text = re.sub(r"</p>\s*<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    lines = [" ".join(line.split()).strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()


def to_float(value: Any) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 4)


def normalize_level_label(value: Any) -> str:
    label = clean_text(value).lower()
    return {
        "muy desarrollado": "Muy desarrollado",
        "muy desarrollada": "Muy desarrollado",
        "desarrollado": "Desarrollado",
        "desarrollada": "Desarrollado",
        "moderadamente desarrollado": "Moderadamente desarrollado",
        "moderadamente desarrollada": "Moderadamente desarrollado",
        "en desarrollo": "En desarrollo",
        "poco desarrollado": "Poco desarrollado",
        "poco desarrollada": "Poco desarrollado",
        "muy poco desarrollado": "Muy poco desarrollado",
        "muy poco desarrollada": "Muy poco desarrollado",
    }.get(label, clean_text(value))


def load_recommendations(input_xlsx: Path = INPUT_RECOMMENDATIONS_XLSX) -> dict[int, list[dict[str, str]]]:
    recommendations: dict[int, list[dict[str, str]]] = {}
    if input_xlsx.exists():
        df = pd.read_excel(input_xlsx)
        df.columns = [clean_text(col) for col in df.columns]
        required = {"id", "recommendations"}
        missing = sorted(required - set(df.columns))
        if missing:
            raise ValueError(f"Estructura invalida en recomendaciones. Columnas faltantes: {missing}.")
        for _, row in df.dropna(subset=["id", "recommendations"]).iterrows():
            rec = clean_recommendation(row["recommendations"])
            if rec:
                recommendations.setdefault(int(row["id"]), []).append({"label": "", "text": rec})

    if INPUT_SUPPLEMENTAL_RECOMMENDATIONS.exists():
        supplemental = pd.read_csv(INPUT_SUPPLEMENTAL_RECOMMENDATIONS, sep="\t")
        supplemental.columns = [clean_text(col) for col in supplemental.columns]
        required = {"competenceId", "recommendation"}
        missing = sorted(required - set(supplemental.columns))
        if missing:
            raise ValueError(f"Estructura invalida en recomendaciones suplementarias. Columnas faltantes: {missing}.")
        for _, row in supplemental.dropna(subset=["competenceId", "recommendation"]).iterrows():
            rec = clean_recommendation(row["recommendation"])
            if rec:
                recommendations.setdefault(int(row["competenceId"]), []).append(
                    {
                        "label": normalize_level_label(row.get("Interpretación", "")),
                        "text": rec,
                    }
                )
    return recommendations


def apply_recommendations(comp_id: int, levels: list[dict[str, Any]], recs: list[dict[str, str]]) -> None:
    if not recs:
        for level in levels:
            level["recommendation"] = RECOMMENDATIONS_BY_LEVEL.get(level["label"], "")
        return

    labeled = {item["label"]: item["text"] for item in recs if item.get("label") in {level["label"] for level in levels}}
    if labeled:
        for level in levels:
            level["recommendation"] = labeled.get(level["label"], RECOMMENDATIONS_BY_LEVEL.get(level["label"], ""))
        return

    rec_texts = [item["text"] for item in recs if item.get("text")]
    if comp_id <= 431 or len(rec_texts) == 1:
        for level in levels:
            level["recommendation"] = rec_texts[0]
        return

    if comp_id == 438:
        if len(rec_texts) >= len(levels):
            for level, rec in zip(levels, rec_texts):
                level["recommendation"] = rec
            return

        # English se trata como caso especial: la primera recomendacion aplica
        # al nivel mas alto y las siguientes bajan una a una por nivel.
        for idx, level in enumerate(levels):
            level["recommendation"] = rec_texts[min(idx, len(rec_texts) - 1)]
        return

    first = rec_texts[0]
    middle = rec_texts[1] if len(rec_texts) > 1 else first
    low = rec_texts[2] if len(rec_texts) > 2 else middle
    for level in levels:
        label = level["label"]
        if label in {"Muy desarrollado", "Desarrollado"}:
            level["recommendation"] = first
        elif label == "Poco desarrollado":
            level["recommendation"] = low
        else:
            level["recommendation"] = middle


def build_catalog(input_xlsx: Path = INPUT_XLSX) -> dict[str, Any]:
    comp = pd.read_excel(input_xlsx, sheet_name="Competencias")
    niveles = pd.read_excel(input_xlsx, sheet_name="Niveles")
    recommendations_by_id = load_recommendations()

    comp.columns = [clean_text(col) for col in comp.columns]
    niveles.columns = [clean_text(col) for col in niveles.columns]

    required_comp = {"id", "name", "definition"}
    required_niveles = {
        "CompetenceName",
        "competenceId",
        "valueFrom",
        "valueTo",
        "Etiqueta",
        "interpretation",
    }
    missing_comp = sorted(required_comp - set(comp.columns))
    missing_niveles = sorted(required_niveles - set(niveles.columns))
    if missing_comp or missing_niveles:
        raise ValueError(
            "Estructura invalida. "
            f"Competencias faltantes: {missing_comp}. "
            f"Niveles faltantes: {missing_niveles}."
        )

    comp = comp.dropna(subset=["id", "name"]).copy()
    niveles = niveles.dropna(subset=["competenceId", "valueFrom", "valueTo", "Etiqueta"]).copy()

    levels_by_id: dict[int, list[dict[str, Any]]] = {}
    for _, row in niveles.iterrows():
        comp_id = int(row["competenceId"])
        label = clean_text(row["Etiqueta"])
        levels_by_id.setdefault(comp_id, []).append(
            {
                "label": label,
                "value_from": to_float(row["valueFrom"]),
                "value_to": to_float(row["valueTo"]),
                "interpretation": clean_text(row["interpretation"]),
            }
        )

    for comp_id, supplemental_levels in SUPPLEMENTAL_LEVELS.items():
        for item in supplemental_levels:
            label = LEVEL_LABEL_TRANSLATIONS[item["type"]]
            levels_by_id.setdefault(comp_id, []).append(
                {
                    "label": label,
                    "source_type": item["type"],
                    "value_from": to_float(item["valueFrom"]),
                    "value_to": to_float(item["valueTo"]),
                    "interpretation": clean_html(item["interpretation"]),
                }
            )

    competencies = []
    for _, row in comp.sort_values("id").iterrows():
        comp_id = int(row["id"])
        levels = sorted(
            levels_by_id.get(comp_id, []),
            key=lambda item: (item["value_from"] if item["value_from"] is not None else -999),
            reverse=True,
        )
        apply_recommendations(comp_id, levels, recommendations_by_id.get(comp_id, []))
        competencies.append(
            {
                "id": comp_id,
                "name": clean_text(row["name"]),
                "definition": clean_text(row["definition"]),
                "levels": levels,
            }
        )

    comp_ids = {int(value) for value in comp["id"].dropna()}
    level_ids = set(levels_by_id)
    warnings = []
    missing_levels = sorted(comp_ids - level_ids)
    if missing_levels:
        warnings.append(
            {
                "type": "competencies_without_levels",
                "ids": missing_levels,
            }
        )
    recommendation_ids = set(recommendations_by_id)
    extra_recommendations = sorted(recommendation_ids - comp_ids)
    if extra_recommendations:
        warnings.append(
            {
                "type": "recommendations_without_competency",
                "ids": extra_recommendations,
            }
        )
    missing_recommendations = sorted(comp_ids - recommendation_ids)
    if missing_recommendations:
        warnings.append(
            {
                "type": "competencies_without_recommendations",
                "ids": missing_recommendations,
            }
        )

    return {
        "schema_version": "1.0",
        "source_file": str(input_xlsx.name),
        "recommendations_source_file": str(INPUT_RECOMMENDATIONS_XLSX.name),
        "supplemental_recommendations_source_file": str(INPUT_SUPPLEMENTAL_RECOMMENDATIONS.name),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scale": {
            "min": 0,
            "max": 10,
            "note": "Los rangos son inclusivos en value_from y exclusivos en value_to, salvo el limite superior del maximo.",
        },
        "recommendations_by_level": RECOMMENDATIONS_BY_LEVEL,
        "gap_rules": GAP_RULES,
        "competencies": competencies,
        "validation": {
            "competencies_count": len(competencies),
            "competencies_with_levels": len(level_ids),
            "levels_count": int(sum(len(item["levels"]) for item in competencies)),
            "recommendations_count": int(sum(len(items) for items in recommendations_by_id.values())),
            "warnings": warnings,
        },
    }


def main() -> None:
    catalog = build_catalog()
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"JSON generado: {OUTPUT_JSON}")
    print(json.dumps(catalog["validation"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
