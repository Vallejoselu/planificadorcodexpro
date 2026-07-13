import unittest

from services.rules.disponibilidad import (
    claves_disponibilidad_turno,
    esta_disponible,
    intervalo_turno,
    intervalos_solapados
)


class TestRulesDisponibilidad(unittest.TestCase):

    def test_disponibilidad_por_turno_respeta_comidas_y_cenas(self):

        repartidor = {
            "disponibilidad": {
                "lunes": "Comidas",
                "martes": "Cenas",
                "miercoles": "No disponible"
            }
        }

        self.assertTrue(
            esta_disponible(repartidor, "lunes", {"nombre": "Comida"})
        )
        self.assertFalse(
            esta_disponible(repartidor, "lunes", {"nombre": "Cena"})
        )
        self.assertTrue(
            esta_disponible(repartidor, "martes", {"nombre": "Cena"})
        )
        self.assertFalse(
            esta_disponible(repartidor, "miercoles", {"nombre": "Comida"})
        )

    def test_dia_no_configurado_no_se_considera_disponible(self):

        repartidor = {"disponibilidad": {"lunes": "Ambos"}}

        self.assertFalse(
            esta_disponible(repartidor, "martes", {"nombre": "Comida"})
        )

    def test_claves_de_turno_partido_exigen_comida_y_noche(self):

        self.assertEqual(
            claves_disponibilidad_turno({"tipo": "Turno partido", "nombre": "Partido"}),
            ("comida", "noche")
        )

    def test_solapamiento_detecta_horarios_parciales_y_medianoche(self):

        self.assertTrue(
            intervalos_solapados("13:00", "16:00", "15:00", "18:00")
        )
        self.assertTrue(
            intervalos_solapados("22:00", "01:00", "23:30", "02:00")
        )
        self.assertFalse(
            intervalos_solapados("13:00", "16:00", "16:00", "18:00")
        )

    def test_intervalo_de_turno_que_cruza_medianoche_sigue_en_orden(self):

        inicio, fin = intervalo_turno(
            "viernes",
            {
                "nombre": "Cierre",
                "hora_inicio": "22:00",
                "hora_fin": "01:00",
                "cruza_medianoche": True
            }
        )

        self.assertLess(inicio, fin)
        self.assertEqual(fin - inicio, 180)


if __name__ == "__main__":

    unittest.main()
