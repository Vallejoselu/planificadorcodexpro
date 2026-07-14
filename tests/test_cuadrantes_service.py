import unittest

from services.cuadrantes_service import CuadrantesService
from tests.test_servicios_aplicacion import (
    FakeCalendarioRepository,
    FakeTurnosRepository
)


class FakePlantillasRepository:

    def __init__(self):

        self.plantillas = []
        self.asignaciones = {}
        self.creadas = []
        self.siguiente_id = 1

    def listar(self):

        return self.plantillas

    def obtener_por_id(self, plantilla_id):

        for plantilla in self.plantillas:

            if plantilla[0] == plantilla_id:

                return plantilla

        return None

    def crear(
        self,
        nombre,
        descripcion,
        incluir_repartidores,
        asignaciones
    ):

        plantilla_id = self.siguiente_id
        self.siguiente_id += 1
        plantilla = (
            plantilla_id,
            nombre,
            descripcion,
            1 if incluir_repartidores else 0,
            1,
            "2026-07-13",
            sum(len(items) for items in asignaciones.values())
        )
        self.plantillas.append(plantilla)
        self.asignaciones[plantilla_id] = asignaciones
        self.creadas.append((
            nombre,
            descripcion,
            incluir_repartidores,
            asignaciones
        ))

        return plantilla_id

    def obtener_asignaciones(self, plantilla_id):

        return self.asignaciones.get(plantilla_id, {})


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

    def test_copiar_semana_conserva_restaurante_turno_y_repartidor(self):

        calendario = FakeCalendarioRepository()
        calendario.semanas["2026-07-13"] = [
            (
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
            ),
            (
                2,
                "martes",
                6,
                "Cena",
                "Cena",
                "#674EA7",
                3,
                "BK Norte",
                "Norte",
                None,
                None,
                "2026-07-13"
            )
        ]
        servicio = CuadrantesService(calendario_repository=calendario)

        resultado = servicio.copiar_semana("2026-07-13", "2026-07-20")

        self.assertEqual(resultado["total_asignaciones"], 2)
        self.assertEqual(calendario.reemplazos, [(
            "2026-07-20",
            {
                ("lunes", 5): [{
                    "restaurante_id": 2,
                    "repartidor_id": 10
                }],
                ("martes", 6): [{
                    "restaurante_id": 3,
                    "repartidor_id": None
                }]
            }
        )])

    def test_copiar_semana_rechaza_origen_vacio_y_misma_semana(self):

        servicio = CuadrantesService(
            calendario_repository=FakeCalendarioRepository()
        )

        with self.assertRaises(ValueError):

            servicio.copiar_semana("2026-07-13", "2026-07-13")

        with self.assertRaises(ValueError):

            servicio.copiar_semana("2026-07-13", "2026-07-20")

    def test_crear_plantilla_desde_semana_incluye_repartidores(self):

        calendario = FakeCalendarioRepository()
        plantillas = FakePlantillasRepository()
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
        servicio = CuadrantesService(
            calendario_repository=calendario,
            plantillas_repository=plantillas
        )

        resultado = servicio.crear_plantilla_desde_semana(
            "2026-07-13",
            "Semana base",
            "Descripcion",
            incluir_repartidores=True
        )

        self.assertEqual(resultado["plantilla_id"], 1)
        self.assertEqual(resultado["total_asignaciones"], 1)
        self.assertEqual(
            plantillas.creadas[0][3],
            {("lunes", 5): [{
                "restaurante_id": 2,
                "repartidor_id": 10
            }]}
        )

    def test_crear_plantilla_desde_semana_puede_omitir_repartidores(self):

        calendario = FakeCalendarioRepository()
        plantillas = FakePlantillasRepository()
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
        servicio = CuadrantesService(
            calendario_repository=calendario,
            plantillas_repository=plantillas
        )

        servicio.crear_plantilla_desde_semana(
            "2026-07-13",
            "Semana sin nombres",
            incluir_repartidores=False
        )

        self.assertFalse(plantillas.creadas[0][2])
        self.assertEqual(
            plantillas.creadas[0][3],
            {("lunes", 5): [{
                "restaurante_id": 2,
                "repartidor_id": None
            }]}
        )

    def test_aplicar_plantilla_guarda_cuadrante_en_semana_destino(self):

        calendario = FakeCalendarioRepository()
        plantillas = FakePlantillasRepository()
        servicio = CuadrantesService(
            calendario_repository=calendario,
            plantillas_repository=plantillas
        )
        plantillas.crear(
            "Base",
            "",
            True,
            {("martes", 5): [{
                "restaurante_id": 2,
                "repartidor_id": 10
            }]}
        )

        resultado = servicio.aplicar_plantilla(1, "2026-07-20")

        self.assertEqual(resultado["nombre"], "Base")
        self.assertEqual(calendario.reemplazos, [(
            "2026-07-20",
            {("martes", 5): [{
                "restaurante_id": 2,
                "repartidor_id": 10
            }]}
        )])

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
        self.assertEqual(
            estado["estado_texto"],
            "Asignaciones: 1 | Todo cubierto"
        )

    def test_preparar_estado_semana_muestra_estado_vacio_accionable(self):

        servicio = CuadrantesService(
            calendario_repository=FakeCalendarioRepository()
        )

        estado = servicio.preparar_estado_semana(
            "2026-07-13",
            [],
            [],
            []
        )

        self.assertIn("Sin cuadrante guardado", estado["estado_texto"])
        self.assertIn("Genera uno", estado["estado_texto"])
        self.assertEqual(estado["indicadores"]["asignaciones"], 0)
        self.assertEqual(estado["indicadores"]["sin_repartidor"], 0)

    def test_preparar_estado_semana_indica_asignaciones_sin_repartidor(self):

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
            None,
            None,
            "2026-07-13"
        )]
        servicio = CuadrantesService(calendario_repository=calendario)

        estado = servicio.preparar_estado_semana(
            "2026-07-13",
            [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
            [(2, "BK Centro", "", "Centro", "", 50, 1)],
            [(10, "Ana")]
        )
        celda = estado["celdas_semana"][("lunes", 5)]

        self.assertIn("Sin repartidor", celda["texto"])
        self.assertIn("Pendientes sin repartidor: 1", celda["tooltip"])
        self.assertEqual(celda["estado"], "pendiente")
        self.assertEqual(estado["indicadores"]["sin_repartidor"], 1)
        self.assertEqual(
            estado["filas_locales"][0]["dias"]["lunes"],
            "Comida - Sin repartidor"
        )
        self.assertEqual(
            estado["estado_texto"],
            "Asignaciones: 1 | Con repartidor: 0 | Sin repartidor: 1"
        )

    def test_texto_resumen_generacion_muestra_resultado_y_advertencias(self):

        servicio = CuadrantesService()
        resultado = {
            "horario": {
                "lunes": {
                    "comida": [{"repartidor_id": 1}]
                }
            },
            "resumen": [{"nombre": "Ana", "horas": 3}],
            "horas_complementarias": [{
                "nombre": "Ana",
                "limite": 4,
                "usadas": 2
            }],
            "incidencias": [{
                "dia": "lunes",
                "turno": "cena",
                "restaurante": "BK Centro",
                "motivo": "No hay repartidor disponible"
            }]
        }

        texto = servicio.texto_resumen_generacion(resultado)

        self.assertIn("Resultado: Con advertencias", texto)
        self.assertIn("Asignaciones generadas: 1", texto)
        self.assertIn("Advertencias: 1", texto)
        self.assertIn("Turnos sin cubrir: 1", texto)
        self.assertIn("Horas complementarias", texto)
        self.assertIn("Ana: 2 h de 4 permitidas", texto)

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
