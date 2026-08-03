# Auditoría de distribución de potencial

Fecha de revisión: 3 de agosto de 2026.

## Conclusión

La distribución mostrada por el dashboard (360 Potencial Alto, 101 Potencial Medio y 14 Potencial Bajo) es correcta para los puntajes disponibles en el archivo base y los cortes 70/85 aplicados sin redondeo previo.

La distribución esperada (366/65/44) corresponde exactamente a otra regla: redondear primero cada puntaje al entero más cercano y clasificar luego con cortes 80/85.

Por tanto, los conteos esperados no son compatibles con los rangos declarados de 0-69,99, 70-84,99 y 85-100.

## Fuente controlante

- Archivo: `Fase_I_Evaluación_360__180__90__copia_.xlsx`
- Hoja: `Potencial`
- Campo cargado por el dashboard: `COMPETENCIAS`, normalizado como `evaluacion_potencial`
- Registros con puntaje: 475
- Promedio: 90,0604, mostrado como 90,06
- Rango observado: 57,05 a 100,00

Los campos `CAP` y `COMPETENCIAS` contienen los mismos valores en los 475 registros evaluados.

## Reconciliación de reglas

| Tratamiento del puntaje | Cortes Bajo/Medio/Alto | Alto | Medio | Bajo |
| --- | --- | ---: | ---: | ---: |
| Sin redondeo | 70 / 85 | 360 | 101 | 14 |
| Redondeo al entero | 70 / 85 | 366 | 95 | 14 |
| Sin redondeo | 80 / 85 | 360 | 69 | 46 |
| Redondeo al entero | 80 / 85 | **366** | **65** | **44** |

## Diagnóstico

El gráfico no presenta un error de conteo. La discrepancia proviene de comparar dos definiciones distintas de la métrica:

1. Dashboard actual: puntaje decimal, Bajo <70, Medio 70-<85, Alto >=85.
2. Conteo esperado: puntaje redondeado al entero, Bajo <80, Medio 80-<85, Alto >=85.

Con la regla declarada, solo existen 14 personas con puntaje inferior a 70; por ello no es posible obtener 44 personas en Potencial Bajo sin cambiar el corte inferior o los puntajes fuente.

## Decisión adoptada

Se adopta como regla oficial el redondeo previo al entero y los rangos 0-79 / 80-84 / 85-100. Esta regla mantiene la trazabilidad a los puntajes individuales y produce la distribución acordada de 44 / 65 / 366.
