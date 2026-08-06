import unittest

from scripts.validar_flujo_base_limpia import ejecutar_validacion


class TestValidacionBaseLimpia(unittest.TestCase):

    def test_script_valida_primer_cuadrante_real_sin_tocar_delivery_db(self):

        resultado = ejecutar_validacion()

        self.assertTrue(resultado["ok"], resultado["errores"])
        self.assertEqual(resultado["asignaciones"], 14)
        self.assertEqual(resultado["cubiertas"], 14)
        self.assertEqual(resultado["pendientes"], 0)
        self.assertEqual(resultado["calendario_guardado"], 14)


if __name__ == "__main__":

    unittest.main()
