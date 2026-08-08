import unittest

from scripts.validar_flujo_zona_general import ejecutar_validacion


class TestValidacionZonaGeneral(unittest.TestCase):

    def test_script_valida_cuadrante_por_zona_sin_restaurante_activo(self):

        resultado = ejecutar_validacion()

        self.assertTrue(resultado["ok"], resultado["errores"])
        self.assertEqual(resultado["zona"], "Santiago Centro")
        self.assertEqual(resultado["asignaciones"], 14)
        self.assertEqual(resultado["cubiertas"], 14)
        self.assertEqual(resultado["pendientes"], 0)
        self.assertEqual(resultado["calendario_guardado"], 14)
        self.assertEqual(resultado["restaurantes_activos"], 0)


if __name__ == "__main__":

    unittest.main()
