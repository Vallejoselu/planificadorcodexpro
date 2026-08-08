import unittest

from scripts.validar_arranque_en_blanco import ejecutar_validacion


class TestArranqueEnBlanco(unittest.TestCase):

    def test_base_nueva_no_muestra_datos_operativos_ni_demo(self):

        resultado = ejecutar_validacion()

        self.assertTrue(resultado["ok"], resultado["errores"])
        self.assertEqual(
            resultado["visibles"],
            {
                "ciudades": 0,
                "restaurantes": 0,
                "repartidores": 0,
                "turnos": 0
            }
        )
        self.assertEqual(resultado["conteos"]["ciudades"], 1)
        self.assertEqual(resultado["ciudad_tecnica"], "Sin ciudad")

        for tabla, total in resultado["conteos"].items():

            if tabla == "ciudades":

                continue

            self.assertEqual(total, 0, tabla)


if __name__ == "__main__":

    unittest.main()
