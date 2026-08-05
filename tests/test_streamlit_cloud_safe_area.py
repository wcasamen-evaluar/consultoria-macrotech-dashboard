import unittest
from pathlib import Path


class StreamlitCloudSafeAreaTest(unittest.TestCase):
    def test_reserva_espacio_inferior_para_controles_flotantes(self):
        ruta = Path(__file__).resolve().parents[1] / "dashboard_360.py"
        contenido = ruta.read_text(encoding="utf-8-sig")

        self.assertIn(
            ".block-container { padding-top: 1rem; padding-bottom: 5rem; }",
            contenido,
        )


if __name__ == "__main__":
    unittest.main()
