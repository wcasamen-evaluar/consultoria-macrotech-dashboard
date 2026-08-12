# Reporte general de evaluaciones

Genera un archivo consolidado con las columnas `Nombre`, `correo`,
`desempeño`, `competencias` y `objetivos`.

El script reutiliza los motores y las reglas de emparejamiento del dashboard.
Cada puntaje aparece solo cuando la persona realizó esa evaluación; en caso
contrario, la celda queda vacía.

Desde la raíz del proyecto:

```powershell
python ".\reporte excel\generar_reporte_excel.py"
```

El resultado predeterminado se guarda en:

```text
reporte excel/reporte general_excel.xlsx
```

Para indicar archivos distintos:

```powershell
python ".\reporte excel\generar_reporte_excel.py" `
  --entrada ".\mi_fuente.xlsx" `
  --salida ".\reporte excel\mi_reporte.xlsx"
```
