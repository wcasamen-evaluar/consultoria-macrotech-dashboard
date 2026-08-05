import ast
import unittest
from pathlib import Path

import pandas as pd

from reporte import calculos
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

    def test_los_ejes_ninebox_usan_competencias_y_desempeno(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")
        self.assertIn('title=dict(text="Competencias"', contenido)
        self.assertIn('title=dict(text="Desempeño"', contenido)
        self.assertNotIn('title=dict(text="Potencial"', contenido)
        self.assertNotIn('title=dict(text="Desempeño 360"', contenido)

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

    def test_cortes_ninebox_redondean_al_entero_con_half_up(self):
        self.assertEqual(calculos.redondear_corte_ninebox(98.8), 99)
        self.assertEqual(calculos.redondear_corte_ninebox(98.5), 99)
        self.assertEqual(calculos.redondear_corte_ninebox(97.9), 98)

    def test_puntaje_inferior_al_corte_entero_no_es_super_estrella(self):
        datos = pd.DataFrame(
            {
                "colaborador": ["Persona A", "Persona B"],
                "match_nombre": ["persona a", "persona b"],
                "potencial": [100.0, 99.0],
                "desempeno_360": [98.9, 98.7],
            }
        )

        resultado = integrado.clasificar_ninebox(datos).set_index("colaborador")

        self.assertEqual(resultado.loc["Persona A", "nivel_potencial"], "alto")
        self.assertNotEqual(resultado.loc["Persona A", "nivel_desempeno"], "alto")
        self.assertNotEqual(resultado.loc["Persona A", "cuadrante"], 1)
        self.assertNotEqual(
            resultado.loc["Persona A", "cuadrante_nombre"],
            "Super Estrella",
        )

    def test_dashboard_muestra_los_rangos_sin_decimales(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")

        self.assertIn("cortes['potencial_sup']:.0f", contenido)
        self.assertIn("cortes['potencial_inf']:.0f", contenido)
        self.assertIn("cortes['desempeno_sup']:.0f", contenido)
        self.assertIn("cortes['desempeno_inf']:.0f", contenido)


if __name__ == "__main__":
    unittest.main()
