import unittest

from services.cuadrantes_service import CuadrantesService
from tests.test_servicios_aplicacion import (
    FakeCalendarioRepository,
    FakeTurnosRepository
)


class TestCuadrantesServicePorCapa(unittest.TestCase):

    def test_guardar_cuadrante_normaliza_semana_y_delega_reemplazo(self):

        calendario = FakeCalendarioRepository()
        servicio = CuadrantesService(
            calendario_repository=calendario,
            turnos_repository=FakeTurnosRepository()
        )
        asignaciones = {
            ("martes", 5): [{
                "restaurante_id": 2,
                "repartidor_id": 10
            }]
        }

        servicio.guardar_cuadrante("2026-07-15", asignaciones)

        self.assertEqual(calendario.reemplazos, [(
            "2026-07-13",
            asignaciones
        )])

    def test_guardar_cuadrante_por_semana_no_mezcla_fechas(self):

        calendario = FakeCalendarioRepository()
        servicio = CuadrantesService(calendario_repository=calendario)

        servicio.guardar_asignacion_turno(
            "2026-07-13",
            "lunes",
            5,
            [{"restaurante_id": 2, "repartidor_id": 10}]
        )
        servicio.guardar_asignacion_turno(
            "2026-07-20",
            "lunes",
            5,
            [{"restaurante_id": 3, "repartidor_id": 11}]
        )

        self.assertEqual(
            calendario.guardados[0],
            ("lunes", 5, 2, 10, "2026-07-13")
        )
        self.assertEqual(
            calendario.guardados[1],
            ("lunes", 5, 3, 11, "2026-07-20")
        )

    def test_preparar_estado_semana_devuelve_celdas_y_vista_local(self):

        calendario = FakeCalendarioRepository()
        calendario.semanas["2026-07-13"] = [(
            1,
            "lunes",
            5,
            "Comida",
            "Comida",
            "#2563EB",
            2,
            "BK Centro",
            "Centro",
            10,
            "Ana",
            "2026-07-13"
        )]
        servicio = CuadrantesService(calendario_repository=calendario)

        estado = servicio.preparar_estado_semana(
            "2026-07-13",
            [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
            [(2, "BK Centro", "", "Centro", "", 50, 1)],
            [(10, "Ana")]
        )

        self.assertEqual(
            estado["celdas_semana"][("lunes", 5)]["texto"],
            "BK Centro - Ana"
        )
        self.assertEqual(
            estado["filas_locales"][0]["dias"]["lunes"],
            "Comida - Ana"
        )

    def test_preparar_cambio_no_duplica_mismo_repartidor_mismo_turno(self):

        servicio = CuadrantesService()
        asignaciones = {
            ("lunes", 5): [{"restaurante_id": 2, "repartidor_id": 10}]
        }

        cambio = servicio.preparar_cambio_asignacion(
            asignaciones,
            "lunes",
            5,
            2,
            10
        )

        self.assertEqual(cambio["nuevo"], cambio["anterior"])
        self.assertEqual(len(cambio["nuevo"]), 1)


if __name__ == "__main__":

    unittest.main()
