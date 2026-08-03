import ast
import unittest
from pathlib import Path

from reporte import integrado


class NineboxLabelsTest(unittest.TestCase):
    def test_los_nombres_corresponden_a_las_nueve_posiciones(self):
        esperados = {
            1: "Super Estrella",
            2: "Estrella del futuro",
            3: "Enigma",
            4: "Estrella en su área",
            5: "Colaborador clave",
            6: "Dilema",
            7: "Comprometido",
            8: "Eficaz",
            9: "Bajo rendimiento",
        }
        self.assertEqual(integrado.NINEBOX_LABELS, esperados)

    def test_dashboard_y_reporte_comparten_los_mismos_nombres(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
        etiquetas_dashboard = None
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            if any(
                isinstance(destino, ast.Name) and destino.id == "NINEBOX_LABELS"
                for destino in nodo.targets
            ):
                etiquetas_dashboard = ast.literal_eval(nodo.value)
                break

        self.assertEqual(etiquetas_dashboard, integrado.NINEBOX_LABELS)

    def test_el_encabezado_de_cargos_se_reemplazo_por_ranking(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")
        self.assertIn('st.markdown("**Ranking**")', contenido)
        self.assertNotIn("Cargos con mejor cumplimiento", contenido)

    def test_los_colores_coinciden_con_la_matriz_de_referencia(self):
        esperados = {
            1: "#4EA72F",
            2: "#C5E0B3",
            3: "#EAEAEA",
            4: "#528139",
            5: "#FFC000",
            6: "#FF99FF",
            7: "#0071C0",
            8: "#9F2522",
            9: "#FE0000",
        }
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
        colores_dashboard = None
        for nodo in arbol.body:
            if not isinstance(nodo, ast.Assign):
                continue
            if any(
                isinstance(destino, ast.Name) and destino.id == "NINEBOX_COLORES"
                for destino in nodo.targets
            ):
                colores_dashboard = ast.literal_eval(nodo.value)
                break

        self.assertEqual(colores_dashboard, esperados)


if __name__ == "__main__":
    unittest.main()
