import unittest

import pandas as pd

from reporte import calculos
from reporte import integrado


class ExclusionesDesempenoTest(unittest.TestCase):
    def test_filtra_las_ocho_personas_solo_del_desempeno(self):
        filas = [
            {
                "nombre_colaborador": nombre,
                "email_colaborador": email,
            }
            for email, nombre in calculos.EXCLUIDOS_DESEMPENO.items()
        ]
        filas.append(
            {
                "nombre_colaborador": "Persona Control",
                "email_colaborador": "control@example.com",
            }
        )

        resultado = calculos.filtrar_excluidos_desempeno(pd.DataFrame(filas))

        self.assertEqual(resultado["nombre_colaborador"].tolist(), ["Persona Control"])

    def test_filtra_tambien_por_nombre_normalizado(self):
        resultado = calculos.filtrar_excluidos_desempeno(
            pd.DataFrame(
                {
                    "nombre_colaborador": ["Juan Vasquez", "Persona Control"],
                    "email_colaborador": ["correo.distinto@example.com", "control@example.com"],
                }
            )
        )

        self.assertEqual(resultado["nombre_colaborador"].tolist(), ["Persona Control"])

    def test_resultado_vacio_impide_mostrar_desempeno_en_pdf(self):
        resultado = integrado._resultado_360_vacio()

        self.assertIsNone(resultado["puntaje_global"])
        self.assertEqual(resultado["competencias"], {})
        self.assertEqual(resultado["desglose_global"], {})
        self.assertEqual(resultado["pesos_aplicados"], {})

    def test_detecta_competencias_u_objetivos_como_otra_evaluacion(self):
        self.assertTrue(integrado._tiene_otra_evaluacion({"potencial": 88.25}))
        self.assertTrue(integrado._tiene_otra_evaluacion({"objetivos": 75.0}))
        self.assertFalse(
            integrado._tiene_otra_evaluacion(
                {"evd_360": 83.33, "potencial": None, "objetivos": None}
            )
        )


if __name__ == "__main__":
    unittest.main()
