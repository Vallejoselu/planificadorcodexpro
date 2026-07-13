import unittest

from services.rules.descansos import (
    asegurar_descanso_consecutivo,
    calcular_descanso,
    descanso_es_consecutivo,
    dias_no_disponibles,
    disponibilidad_aporta_descanso,
    tiene_dias_consecutivos
)


class TestRulesDescansos(unittest.TestCase):

    def test_descanso_valido_se_conserva(self):

        repartidor = {"descanso": ["lunes", "martes"], "disponibilidad": {}}

        self.assertTrue(descanso_es_consecutivo(repartidor["descanso"]))
        self.assertEqual(
            asegurar_descanso_consecutivo(repartidor),
            ["lunes", "martes"]
        )

    def test_disponibilidad_con_dos_dias_libres_cubre_descanso(self):

        repartidor = {
            "disponibilidad": {
                "lunes": "No disponible",
                "martes": "No disponible",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        }

        self.assertEqual(
            dias_no_disponibles(repartidor),
            ["lunes", "martes"]
        )
        self.assertTrue(disponibilidad_aporta_descanso(repartidor))
        self.assertEqual(asegurar_descanso_consecutivo(repartidor), [])

    def test_sin_descanso_disponible_calcula_descanso_adicional(self):

        repartidor = {
            "disponibilidad": {
                "lunes": "Ambos",
                "martes": "Ambos",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        }

        descanso = calcular_descanso(repartidor)

        self.assertTrue(descanso_es_consecutivo(descanso))
        self.assertEqual(descanso, ["lunes", "martes"])

    def test_domingo_lunes_cuenta_como_consecutivo_para_no_disponibles(self):

        self.assertTrue(tiene_dias_consecutivos(["domingo", "lunes"]))
        self.assertFalse(tiene_dias_consecutivos(["lunes", "miercoles"]))


if __name__ == "__main__":

    unittest.main()
