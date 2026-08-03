import unittest
from pathlib import Path


class ResultadoIntegradoGraficosTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        cls.contenido = ruta.read_text(encoding="utf-8-sig")

    def test_medidor_integrado_no_muestra_bandas_ni_titulo_interno(self):
        self.assertIn("fig.data[0].gauge.steps = ()", self.contenido)
        self.assertIn('fig.data[0].title.text = ""', self.contenido)
        self.assertIn('fig.data[0].number.valueformat = ".2f"', self.contenido)

    def test_resultado_por_grupo_no_muestra_bandas_de_fondo(self):
        self.assertIn(
            "fig_objetivos_dimension(df_principal, principal_dim, mostrar_bandas=False)",
            self.contenido,
        )

    def test_no_repite_la_primera_dimension_en_el_panel_izquierdo(self):
        inicio = self.contenido.index("with panel_izq:")
        fin = self.contenido.index("with panel_centro:", inicio)
        panel_izquierdo = self.contenido[inicio:fin]

        self.assertNotIn("render_tabla_dimension_objetivos", panel_izquierdo)


if __name__ == "__main__":
    unittest.main()
