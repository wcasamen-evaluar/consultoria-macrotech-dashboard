import unittest

import pandas as pd

from reporte import calculos


class CompetenciasResumenTest(unittest.TestCase):
    @staticmethod
    def _datos(cantidad: int) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "competencia": [f"Competencia {indice}" for indice in range(cantidad)],
                "prom_comp": [100 - indice for indice in range(cantidad)],
            }
        )

    def test_seis_competencias_se_reparten_tres_y_tres(self):
        top, fortalecer = calculos.seleccionar_competencias_resumen(
            self._datos(6)
        )

        self.assertEqual(len(top), 3)
        self.assertEqual(len(fortalecer), 3)
        self.assertTrue(
            set(top["competencia"]).isdisjoint(fortalecer["competencia"])
        )

    def test_siete_competencias_se_reparten_cuatro_y_tres(self):
        top, fortalecer = calculos.seleccionar_competencias_resumen(
            self._datos(7)
        )

        self.assertEqual(len(top), 4)
        self.assertEqual(len(fortalecer), 3)
        self.assertTrue(
            set(top["competencia"]).isdisjoint(fortalecer["competencia"])
        )

    def test_ocho_o_mas_conservan_cuatro_por_lado(self):
        top, fortalecer = calculos.seleccionar_competencias_resumen(
            self._datos(12)
        )

        self.assertEqual(len(top), 4)
        self.assertEqual(len(fortalecer), 4)
        self.assertTrue(
            set(top["competencia"]).isdisjoint(fortalecer["competencia"])
        )

    def test_elimina_duplicados_por_nombre_antes_del_reparto(self):
        datos = self._datos(6)
        datos = pd.concat([datos, datos.iloc[[0]]], ignore_index=True)

        top, fortalecer = calculos.seleccionar_competencias_resumen(datos)

        mostradas = pd.concat([top, fortalecer], ignore_index=True)
        self.assertEqual(len(mostradas), 6)
        self.assertEqual(mostradas["competencia"].nunique(), 6)


if __name__ == "__main__":
    unittest.main()
