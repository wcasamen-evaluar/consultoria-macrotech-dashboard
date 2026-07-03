# Consultoria Macrotech - Evaluacion 360

Proyecto para procesar resultados de Evaluacion 360 de Macrotech, visualizar indicadores en Streamlit y generar informes PDF individuales.

## Estructura

- `dashboard_360.py`: dashboard Streamlit para analizar resultados agregados de Fase I.
- `reporte/calculos.py`: motor compartido de lectura, normalizacion, ponderacion y clasificacion.
- `reporte/main.py`: orquestador para generar PDFs individuales.
- `reporte/generar_pdf.py`: plantilla visual y renderizado PDF con ReportLab y Matplotlib.
- `reporte/datos/`: carpeta esperada para el Excel fuente de reportes.
- `reporte/output/`: carpeta de salida para PDFs generados.
- `analisis_desempeño.ipynb`: notebook exploratorio usado durante la preparacion inicial.
- `Fase_I_Evaluación_360__180__90__copia_.xlsx`: exportación original usada como fuente oficial del dashboard.
- `evaluacion_360_procesada.xlsx`: artefacto histórico de procesamiento; no es la entrada del dashboard.

## Instalacion

```powershell
pip install -r requirements.txt
```

## Dashboard

Desde la raiz del proyecto:

```powershell
streamlit run dashboard_360.py
```

El dashboard carga automáticamente `Fase_I_Evaluación_360__180__90__copia_.xlsx` desde la raíz del proyecto. No requiere carga manual. La caché se invalida cuando cambia el archivo.

La hoja `Desempeño` contiene la exportación original de Fase I y se recalcula desde `respuesta_valor`. Durante la transición también se admite el nombre anterior `Resultado consulta`. La hoja `Potencial` alimenta Fase II.

## Reportes PDF

Coloca el Excel fuente dentro de `reporte/datos/` y ejecuta:

```powershell
cd reporte
python main.py
```

Los PDFs se guardan en `reporte/output/`.

## Contrato De Datos

El Excel del dashboard debe incluir la hoja `Desempeño` con las 14 columnas del exporte de Evaluar.com. Durante la transición se acepta también `Resultado consulta`. Para el cálculo son esenciales:

- `nombre_colaborador`
- `nombre_seccion`
- `tipo_evaluacion`
- `respuesta_valor`

- `pregunta_texto`

El campo `calificacion_porcentaje` del exporte original no se utiliza como puntaje final. El dashboard transforma `respuesta_valor` con la escala definida a continuación.

## Reglas De Calculo

La respuesta original `1-5` se transforma a puntaje interno:

| Respuesta | Puntaje |
| --- | ---: |
| 5 | 100 |
| 4 | 90 |
| 3 | 85 |
| 2 | 75 |
| 1 | 65 |

Pesos base por tipo de evaluador:

| Tipo | Peso |
| --- | ---: |
| Autoevaluacion | 10% |
| Jefe | 40% |
| Subordinado | 25% |
| Pares | 15% |
| Cliente interno | 10% |

Si falta algun tipo de evaluador para una competencia, su peso se redistribuye proporcionalmente entre los tipos presentes.

Bandas de desempeno:

| Rango | Banda |
| --- | --- |
| 90-100 | Alto Desempeño |
| 80-89.99 | Satisfactorio |
| 70-79.99 | Bajo Desempeño |
| < 70 | Insatisfactorio |

## Nota Tecnica

El dashboard y los reportes comparten el motor de calculo en `reporte/calculos.py`. Si cambia la escala, los pesos o la regla de redistribucion, debe actualizarse ahi primero.
