import unittest

from models.calendario import AsignacionCalendario
from models.repartidor import Repartidor
from models.restaurante import Restaurante
from models.turno import Turno, TurnoRestaurante


class TestModelosDominioPorCapa(unittest.TestCase):

    def test_repartidor_from_row_expone_campos_de_negocio(self):

        fila = (
            1,
            "Ana",
            30,
            "Centro",
            1,
            0,
            80,
            40,
            50,
            "lunes",
            "martes",
            {"lunes": ["comida"]},
            [{"inicio": "2026-07-13", "fin": "2026-07-14"}],
            [{"dia": "viernes"}],
            [{"turno": "comida", "prioridad": 90}],
            2,
            7,
            1,
            4,
            8,
            5,
            [2, 3],
            [7, 8]
        )

        repartidor = Repartidor.from_row(fila)

        self.assertEqual(repartidor.nombre, "Ana")
        self.assertEqual(repartidor.horas, 30)
        self.assertFalse(repartidor.puede_hasta_la_una)
        self.assertEqual(repartidor.descanso_inicio, "lunes")
        self.assertEqual(repartidor.vacaciones[0]["inicio"], "2026-07-13")
        self.assertTrue(repartidor.apoyo_flexible)
        self.assertEqual(repartidor.ciudades_autorizadas, [2, 3])

    def test_restaurante_from_row_conserva_ciudad_y_zona(self):

        restaurante = Restaurante.from_row((
            7,
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000000",
            80,
            1,
            "13:00-16:00",
            "20:00-23:30",
            2,
            "Santiago"
        ))

        self.assertEqual(restaurante.id, 7)
        self.assertEqual(restaurante.zona, "Centro")
        self.assertEqual(restaurante.ciudad_id, 2)
        self.assertEqual(restaurante.ciudad, "Santiago")

    def test_turnos_from_row_distinguen_global_y_restaurante(self):

        turno = Turno.from_row((
            5,
            "Cena",
            "Cena",
            "20:00",
            "23:30",
            "#16A34A",
            3.5,
            1,
            12
        ))
        turno_restaurante = TurnoRestaurante.from_row((
            12,
            7,
            "Cierre",
            "22:00",
            "01:00",
            1,
            3,
            1
        ))

        self.assertEqual(turno.turno_restaurante_id, 12)
        self.assertTrue(turno_restaurante.cruza_medianoche)
        self.assertEqual(turno_restaurante.duracion, 3)

    def test_asignacion_calendario_from_row_incluye_semana(self):

        asignacion = AsignacionCalendario.from_row((
            1,
            "viernes",
            5,
            "Cena",
            "Cena",
            "#16A34A",
            7,
            "BK Centro",
            "Centro",
            10,
            "Ana",
            "2026-07-13"
        ))

        self.assertEqual(asignacion.dia, "viernes")
        self.assertEqual(asignacion.repartidor, "Ana")
        self.assertEqual(asignacion.fecha_inicio_semana, "2026-07-13")
        self.assertEqual(asignacion.to_dict()["restaurante"], "BK Centro")


if __name__ == "__main__":

    unittest.main()
