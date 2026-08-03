import json
import unittest
from pathlib import Path

from reporte import objetivos
from reporte import integrado


class EscalaObjetivosTest(unittest.TestCase):
    def test_clasifica_todos_los_limites_de_la_escala_oficial(self):
        casos = {
            0: "Espacio de crecimiento",
            74.999: "Espacio de crecimiento",
            75: "En desarrollo",
            84.999: "En desarrollo",
            85: "Satisfactorio",
            89.999: "Satisfactorio",
            90: "Alto Desempeño",
            99.999: "Alto Desempeño",
            100: "Talento estrella",
        }

        for puntaje, etiqueta in casos.items():
            with self.subTest(puntaje=puntaje):
                self.assertEqual(objetivos.escala_objetivos_label(puntaje), etiqueta)
                self.assertEqual(integrado.escala_objetivos_label(puntaje), etiqueta)

    def test_el_pdf_usa_las_mismas_bandas_que_el_dashboard(self):
        ruta = (
            Path(__file__).resolve().parents[1]
            / "reporte"
            / "assets"
            / "objetivos_interpretaciones.json"
        )
        config = json.loads(ruta.read_text(encoding="utf-8"))
        bandas_pdf = [
            (item["label"], item["from"], item["to"])
            for item in config["ranges"]
        ]
        bandas_dashboard = [
            (item["label"], item["desde"], item["hasta"])
            for item in objetivos.ESCALA_OBJETIVOS
        ]

        self.assertEqual(bandas_pdf, bandas_dashboard)


if __name__ == "__main__":
    unittest.main()
