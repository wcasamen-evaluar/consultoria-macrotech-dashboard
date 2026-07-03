"""
main.py
=======
Orquestador principal del generador de informes de Evaluación 360°.
Evaluar.com / Grupo Centrico — Consultoría Macrotech

Uso:
    python main.py

Espera:
    - datos/*.xlsx      : archivo exportado de Evaluar.com
    - output/           : carpeta donde se guardan los PDFs (se crea sola)

Configuración:
    Edita la sección CONFIGURACIÓN más abajo antes de ejecutar.
"""

import sys
from pathlib import Path
from datetime import datetime

# Asegurar que los módulos hermanos sean importables
sys.path.insert(0, str(Path(__file__).parent))

import calculos
import generar_pdf


# ---------------------------------------------------------------------------
# CONFIGURACIÓN — editar antes de ejecutar
# ---------------------------------------------------------------------------

CLIENTE  = "Macrotech"
PROCESO  = "Evaluación de Desempeño 360°"
FECHA    = datetime.now().strftime("%d/%m/%Y")   # o escribe: "Mayo 2025"

CARPETA_DATOS  = Path("datos")
CARPETA_OUTPUT = Path("output")

# ---------------------------------------------------------------------------


def main():
    print("=" * 60)
    print(f"  Evaluar.com — Generador de Informes 360°")
    print(f"  Cliente : {CLIENTE}")
    print(f"  Proceso : {PROCESO}")
    print(f"  Fecha   : {FECHA}")
    print("=" * 60)

    # Buscar Excel
    excels = list(CARPETA_DATOS.glob("*.xlsx"))
    if not excels:
        print(f"\nERROR: No se encontró ningún .xlsx en '{CARPETA_DATOS}/'")
        sys.exit(1)
    if len(excels) > 1:
        print(f"  ⚠  Se encontraron {len(excels)} archivos. Se usará: {excels[0].name}")

    ruta_excel = excels[0]
    print(f"\nLeyendo: {ruta_excel}")

    # Leer y calcular
    df = calculos.leer_excel(ruta_excel)
    print(f"Filas válidas    : {len(df)}")
    print(f"Colaboradores    : {df['nombre_colaborador'].nunique()}")
    print()

    resultados = calculos.calcular_todos(df)

    # Crear carpeta de salida
    CARPETA_OUTPUT.mkdir(exist_ok=True)

    # Generar un PDF por colaborador
    print()
    errores = []
    for nombre, resultado in resultados.items():
        slug = nombre.replace(" ", "_").replace("/", "-")
        ruta_pdf = CARPETA_OUTPUT / f"Informe_360_{slug}.pdf"

        try:
            generar_pdf.generar_pdf(
                nombre      = nombre,
                resultado   = resultado,
                proceso     = PROCESO,
                cliente     = CLIENTE,
                fecha       = FECHA,
                ruta_salida = str(ruta_pdf),
            )
        except Exception as e:
            print(f"  ✗  Error generando PDF para {nombre}: {e}")
            errores.append((nombre, str(e)))

    print()
    print("=" * 60)
    if errores:
        print(f"  Completado con {len(errores)} error(es):")
        for nombre, err in errores:
            print(f"    · {nombre}: {err}")
    else:
        print(f"  ✓  {len(resultados)} PDF(s) generado(s) en '{CARPETA_OUTPUT}/'")
    print("=" * 60)


if __name__ == "__main__":
    main()
