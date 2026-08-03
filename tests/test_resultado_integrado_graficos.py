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
            "mostrar_bandas=False,",
            self.contenido,
        )
        self.assertIn("decimales=2,", self.contenido)
        self.assertIn("colorear_por_escala=True,", self.contenido)

    def test_colorea_cada_barra_segun_su_escala(self):
        self.assertIn("OBJETIVOS_ESCALA_COLORES.get(", self.contenido)
        self.assertIn("escala_objetivos_label(puntaje)", self.contenido)
        self.assertIn("marker_color=colores", self.contenido)

    def test_no_repite_la_primera_dimension_en_el_panel_izquierdo(self):
        inicio = self.contenido.index("with panel_izq:")
        fin = self.contenido.index("with panel_centro:", inicio)
        panel_izquierdo = self.contenido[inicio:fin]

        self.assertNotIn("render_tabla_dimension_objetivos", panel_izquierdo)

    def test_colaboradores_aparece_antes_que_la_tabla_de_grupo(self):
        inicio = self.contenido.index("with panel_der:")
        fin = self.contenido.index("def imagen_data_uri", inicio)
        panel_derecho = self.contenido[inicio:fin]

        posicion_colaboradores = panel_derecho.index('st.markdown(f"**Colaboradores')
        posicion_grupo = panel_derecho.index("render_tabla_dimension_objetivos")
        self.assertLess(posicion_colaboradores, posicion_grupo)
        self.assertIn('encabezado_promedio="Promedio"', panel_derecho)
        self.assertIn("decimales=2", panel_derecho)
        self.assertIn("{valor:.2f}", panel_derecho)
        self.assertNotIn('dim == "cargo_objetivo"', panel_derecho)

    def test_usa_nombres_desempeno_objetivos_y_competencias(self):
        self.assertIn('"tab": "Desempeño + Objetivos + Competencias"', self.contenido)
        self.assertIn('("evd_360", "Desempeño")', self.contenido)
        self.assertIn('("objetivos", "Objetivos")', self.contenido)
        self.assertIn('("potencial", "Competencias")', self.contenido)

    def test_excluye_sin_dato_del_desglose_por_grupo(self):
        self.assertIn('if principal_dim == "grupo":', self.contenido)
        self.assertIn('grupos_validos.str.casefold().ne("sin dato")', self.contenido)
        self.assertIn(
            "df_principal = resumen_dimension_integrada(df_principal_base, principal_dim)",
            self.contenido,
        )


if __name__ == "__main__":
    unittest.main()
