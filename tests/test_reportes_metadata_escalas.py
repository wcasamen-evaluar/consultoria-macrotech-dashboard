import unittest

import pandas as pd

from reporte import integrado


class ReportesMetadataEscalasTest(unittest.TestCase):
    def test_metadata_360_solo_completa_personas_sin_potencial(self):
        desempeno = pd.DataFrame(
            {
                "colaborador": ["Sin Potencial", "Con Potencial"],
                "global": [90.0, 91.0],
                "email_colaborador": ["sin@example.com", "con@example.com"],
                "empresa": ["Empresa 360", "Empresa 360"],
                "pais": ["Pais 360", "Pais 360"],
                "area": ["Area 360", "Area 360"],
                "grupo": ["GRUPO 360", "GRUPO 360"],
            }
        )
        objetivos = pd.DataFrame(
            {
                "colaborador": ["Sin Potencial", "Con Potencial"],
                "email_colaborador": ["sin@example.com", "con@example.com"],
                "puntaje": [88.0, 89.0],
                "cargo_objetivo": ["Cargo", "Cargo"],
                "jefe": ["Jefe", "Jefe"],
            }
        )
        potencial = pd.DataFrame(
            {
                "colaborador": ["Con Potencial"],
                "correo": ["con@example.com"],
                "correo_potencial": ["con@example.com"],
                "correo_instancia": ["con@example.com"],
                "evaluacion_potencial": [90.0],
                "empresa": ["Empresa Potencial"],
                "pais": ["Pais Potencial"],
                "area": ["Area Potencial"],
                "grupo": ["GRUPO POTENCIAL"],
                "cargo": ["Cargo Potencial"],
            }
        )
        fuente_objetivos = pd.DataFrame(columns=["nombre_evaluador"])

        resultado = integrado.preparar_resultado_integrado(
            desempeno,
            objetivos,
            potencial,
            fuente_objetivos,
        ).set_index("colaborador")

        self.assertEqual(resultado.loc["Sin Potencial", "empresa"], "Empresa 360")
        self.assertEqual(resultado.loc["Sin Potencial", "grupo"], "GRUPO 360")
        self.assertEqual(
            resultado.loc["Con Potencial", "empresa"],
            "Empresa Potencial",
        )
        self.assertEqual(
            resultado.loc["Con Potencial", "grupo"],
            "GRUPO POTENCIAL",
        )

    def test_pdf_prioriza_puntaje_oficial_de_competencias(self):
        cap_recalculado = {"percent": 84.60, "score": 0.846}
        potencial = {"evaluacion_potencial": 84.41}

        cap_oficial = integrado._cap_con_puntaje_oficial(
            cap_recalculado,
            potencial,
        )

        self.assertEqual(cap_oficial["percent"], 84.41)
        self.assertEqual(cap_oficial["score"], 0.8441)

    def test_pdf_conserva_el_corte_superior_de_competencias(self):
        cap_oficial = integrado._cap_con_puntaje_oficial(
            {"percent": 84.40},
            {"evaluacion_potencial": 84.51},
        )

        self.assertEqual(cap_oficial["percent"], 84.51)
        self.assertEqual(cap_oficial["score"], 0.8451)


if __name__ == "__main__":
    unittest.main()
