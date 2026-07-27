"""Genera el catalogo JSON de arquetipos DISC para los informes.

Entrada esperada:
    reporte/datos/disc.xlsx

Salida:
    reporte/assets/disc.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
INPUT_XLSX = BASE_DIR / "datos" / "disc.xlsx"
OUTPUT_JSON = BASE_DIR / "assets" / "disc.json"

COLUMN_MAP = {
    "id": "id",
    "Arquetipo": "archetype",
    "¿Cómo es la personalidad del arquetipo Analítico?": "personality",
    "¿Cuáles son sus fortalezas?": "strengths",
    "¿Cuáles son sus debilidades?": "weaknesses",
    "¿Qué le motiva en el trabajo?": "motivators",
    "¿Qué les desmotiva en el trabajo?": "demotivators",
}


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).replace("\xa0", " ")
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    return " ".join(text.split()).strip()


def split_bullets(value: Any) -> list[str]:
    text = clean_text(value)
    if not text:
        return []
    parts = [part.strip(" .;") for part in re.split(r"\s*-\s+", text) if part.strip(" .;")]
    return parts


def parse_archetype(value: Any) -> dict[str, str]:
    raw = clean_text(value)
    match = re.match(r"^(.*?)\((.*?)\)\s*$", raw)
    if not match:
        return {"raw": raw, "name": raw.title(), "code": ""}
    name = " ".join(match.group(1).split()).title()
    code = match.group(2).strip()
    return {"raw": raw, "name": name, "code": code}


def build_catalog(input_xlsx: Path = INPUT_XLSX) -> dict[str, Any]:
    if not input_xlsx.exists():
        raise FileNotFoundError(f"No se encontro el archivo DISC: {input_xlsx}")

    df = pd.read_excel(input_xlsx)
    df.columns = [clean_text(col) for col in df.columns]
    missing = sorted(set(COLUMN_MAP) - set(df.columns))
    if missing:
        raise ValueError(f"Estructura invalida en disc.xlsx. Columnas faltantes: {missing}.")

    df = df.dropna(subset=["id", "Arquetipo"]).copy()
    archetypes = []
    for _, row in df.sort_values("id").iterrows():
        archetype = parse_archetype(row["Arquetipo"])
        archetypes.append(
            {
                "id": int(row["id"]),
                "archetype": archetype["raw"],
                "name": archetype["name"],
                "code": archetype["code"],
                "personality": clean_text(row["¿Cómo es la personalidad del arquetipo Analítico?"]),
                "strengths": split_bullets(row["¿Cuáles son sus fortalezas?"]),
                "weaknesses": split_bullets(row["¿Cuáles son sus debilidades?"]),
                "motivators": split_bullets(row["¿Qué le motiva en el trabajo?"]),
                "demotivators": split_bullets(row["¿Qué les desmotiva en el trabajo?"]),
            }
        )

    warnings = []
    duplicate_codes = (
        pd.Series([item["code"] for item in archetypes])
        .value_counts()
        .loc[lambda serie: serie > 1]
        .index.tolist()
    )
    if duplicate_codes:
        warnings.append({"type": "duplicate_codes", "codes": duplicate_codes})

    return {
        "schema_version": "1.0",
        "source_file": input_xlsx.name,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "archetypes": archetypes,
        "validation": {
            "archetypes_count": len(archetypes),
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
