import ast
import json
import unittest
from pathlib import Path

from reporte import calculos


class EscalaDesempenoTest(unittest.TestCase):
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
                indice = calculos._idx_escala(puntaje)
                self.assertEqual(calculos.ESCALA_DASHBOARD[indice], etiqueta)
                self.assertEqual(calculos.clasificar(puntaje)["etiqueta"], etiqueta)

    def test_el_pdf_usa_las_mismas_bandas_que_el_motor_360(self):
        ruta = (
            Path(__file__).resolve().parents[1]
            / "reporte"
            / "assets"
            / "desempeno_360_interpretaciones.json"
        )
        config = json.loads(ruta.read_text(encoding="utf-8"))
        bandas_pdf = [
            (item["label"], item["from"], item["to"])
            for item in config["ranges"]
        ]
        bandas_motor = [
            (etiqueta, desde, hasta)
            for desde, hasta, etiqueta, _ in calculos.BANDAS
        ]

        self.assertEqual(bandas_pdf, bandas_motor)

    def test_el_dashboard_reclasifica_con_las_mismas_bandas_del_motor(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
        rangos_dashboard = None
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            if any(
                isinstance(destino, ast.Name) and destino.id == "ESCALA_RANGOS"
                for destino in nodo.targets
            ):
                rangos_dashboard = ast.literal_eval(nodo.value)
                break

        self.assertEqual(rangos_dashboard, calculos.BANDAS)


if __name__ == "__main__":
    unittest.main()
