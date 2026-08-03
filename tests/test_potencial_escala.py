import ast
import json
import unittest
from pathlib import Path

from reporte import potencial


class EscalaPotencialTest(unittest.TestCase):
    def test_redondea_antes_de_clasificar_con_cortes_80_y_85(self):
        casos = {
            57.05: "Potencial Bajo",
            79.49: "Potencial Bajo",
            79.50: "Potencial Medio",
            84.49: "Potencial Medio",
            84.50: "Potencial Medio",
            84.51: "Potencial Alto",
            100: "Potencial Alto",
        }

        for puntaje, etiqueta in casos.items():
            with self.subTest(puntaje=puntaje):
                self.assertEqual(
                    potencial.clasificar_nivel_potencial(puntaje),
                    etiqueta,
                )

    def test_dashboard_y_motor_comparten_los_mismos_limites(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
        limites_dashboard = None
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            if any(
                isinstance(destino, ast.Name) and destino.id == "POTENCIAL_LIMITES"
                for destino in nodo.targets
            ):
                limites_dashboard = ast.literal_eval(nodo.value)
                break

        self.assertEqual(limites_dashboard, potencial.LIMITES_NIVEL_POTENCIAL)

    def test_pdf_usa_los_mismos_limites(self):
        ruta = (
            Path(__file__).resolve().parents[1]
            / "reporte"
            / "assets"
            / "cap.json"
        )
        config = json.loads(ruta.read_text(encoding="utf-8"))
        rangos = [(item["from"], item["to"]) for item in config["ranges"]]

        self.assertEqual(rangos, [(0, 80), (80, 85), (85, 101)])


if __name__ == "__main__":
    unittest.main()
