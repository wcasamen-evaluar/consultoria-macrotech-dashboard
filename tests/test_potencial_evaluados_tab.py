import unittest
from pathlib import Path


class PotencialColaboradoresTabTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        cls.contenido = ruta.read_text(encoding="utf-8-sig")

    def test_agrega_colaboradores_despues_de_curvas_de_desarrollo(self):
        self.assertIn(
            '"Curvas de Desarrollo", "Colaboradores",',
            self.contenido,
        )
        self.assertIn("with sub_f2_colaboradores:", self.contenido)

    def test_renombra_el_nivel_como_competencias(self):
        self.assertIn('"Nivel de Competencias"', self.contenido)
        self.assertNotIn('"Nivel de potencial"', self.contenido)
        self.assertIn("Distribuci\\u00f3n por nivel de competencias", self.contenido)

    def test_tabla_muestra_solo_el_puntaje_exacto_y_el_nivel(self):
        self.assertIn("<th style='text-align:right'>Puntaje</th>", self.contenido)
        self.assertNotIn("Puntaje exacto", self.contenido)
        self.assertNotIn("Puntaje redondeado", self.contenido)
        self.assertIn("<th>Nivel de Competencias</th>", self.contenido)
        self.assertIn('tabla_evaluados["nivel_potencial"]', self.contenido)


if __name__ == "__main__":
    unittest.main()
