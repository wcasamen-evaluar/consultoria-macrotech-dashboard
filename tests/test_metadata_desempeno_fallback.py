import unittest
from pathlib import Path

import pandas as pd

from reporte import calculos


class MetadataDesempenoFallbackTest(unittest.TestCase):
    def test_normaliza_metadata_desde_resultado_consulta(self):
        fuente = pd.DataFrame(
            {
                "nombre_colaborador": ["Persona", "Persona"],
                "email_colaborador": ["persona@example.com"] * 2,
                "empresa": ["Empresa A"] * 2,
                "país": ["República Dominicana"] * 2,
                "área": ["Tecnología"] * 2,
                "grupo": ["ESPECIALISTAS"] * 2,
            }
        )

        resultado = calculos.extraer_metadata_colaboradores(fuente)

        self.assertEqual(len(resultado), 1)
        self.assertEqual(resultado.loc[0, "colaborador"], "Persona")
        self.assertEqual(resultado.loc[0, "empresa"], "Empresa A")
        self.assertEqual(resultado.loc[0, "pais"], "República Dominicana")
        self.assertEqual(resultado.loc[0, "area"], "Tecnología")
        self.assertEqual(resultado.loc[0, "grupo"], "ESPECIALISTAS")

    def test_dashboard_limita_el_fallback_a_quienes_no_existen_en_potencial(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")

        self.assertIn("sin_registro_potencial = (", contenido)
        self.assertIn("metadata_fallback = (", contenido)
        self.assertIn("if sin_registro_potencial", contenido)
        self.assertIn(
            'for campo in ["empresa", "pais", "area", "grupo"]:',
            contenido,
        )
        self.assertIn('"grupo": fila.get("grupo"),', contenido)

    def test_dashboard_tolera_un_modulo_calculos_aun_no_recargado(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")

        self.assertIn('getattr(\n        motor_360,', contenido)
        self.assertIn('"extraer_metadata_colaboradores",', contenido)
        self.assertIn("if callable(extraer_metadata):", contenido)


if __name__ == "__main__":
    unittest.main()
