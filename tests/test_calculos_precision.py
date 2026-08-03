import unittest

import pandas as pd

from reporte import calculos


class CalculosPrecisionTest(unittest.TestCase):
    def test_reporte_y_dashboard_redondean_el_mismo_resultado_global(self):
        puntajes_competencia = [
            88.27083333333333,
            88.41666666666666,
            86.85416666666667,
            88.10416666666667,
            92.25000000000001,
            93.3125,
        ]
        df = pd.DataFrame(
            {
                "nombre_colaborador": ["Colaboradora"] * len(puntajes_competencia),
                "competencia": [
                    f"Competencia {indice}"
                    for indice in range(len(puntajes_competencia))
                ],
                "pregunta_texto": [
                    f"Pregunta {indice}"
                    for indice in range(len(puntajes_competencia))
                ],
                "tipo_evaluacion": ["autoEvaluation"] * len(puntajes_competencia),
                "puntaje": puntajes_competencia,
            }
        )

        resultado_reporte = calculos.calcular_colaborador(df)
        resultado_dashboard = calculos.calcular_dashboard(df)
        puntaje_dashboard = float(resultado_dashboard["df_global"]["global"].iloc[0])

        self.assertEqual(puntaje_dashboard, 89.53472222222223)
        self.assertEqual(
            resultado_reporte["puntaje_global"],
            round(puntaje_dashboard, 2),
        )
        self.assertEqual(resultado_reporte["puntaje_global"], 89.53)


if __name__ == "__main__":
    unittest.main()
