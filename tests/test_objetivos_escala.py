import ast
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

    def test_el_dashboard_no_depende_de_constantes_cacheadas_del_modulo(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
        rangos_dashboard = None
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            if any(
                isinstance(destino, ast.Name)
                and destino.id == "OBJETIVOS_ESCALA_RANGOS"
                for destino in nodo.targets
            ):
                rangos_dashboard = ast.literal_eval(nodo.value)
                break

        self.assertEqual(rangos_dashboard, objetivos.ESCALA_OBJETIVOS)


if __name__ == "__main__":
    unittest.main()
