import unittest

from services.cuadrantes_service import CuadrantesService
from tests.test_servicios_aplicacion import (
    FakeCalendarioRepository,
    FakeHistorialRepository,
    FakeRepartidoresRepository,
    FakeRestaurantesRepository,
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


class FakePublicacionesRepository:

    def __init__(self):

        self.publicaciones = {}
        self.guardadas = []

    def obtener(self, fecha_inicio_semana):

        return self.publicaciones.get(fecha_inicio_semana)

    def guardar(self, fecha_inicio_semana, estado, resumen=""):

        self.guardadas.append((fecha_inicio_semana, estado, resumen))
        publicacion = (
            len(self.guardadas),
            fecha_inicio_semana,
            estado,
            resumen,
            "2026-07-13 10:00:00" if estado == "publicado" else None,
            "2026-07-13 10:00:00"
        )
        self.publicaciones[fecha_inicio_semana] = publicacion
        return publicacion[0]


class TestCuadrantesServicePorCapa(unittest.TestCase):

    def crear_servicio_aislado(self, **overrides):

        dependencias = {
            "calendario_repository": FakeCalendarioRepository(),
            "historial_repository": FakeHistorialRepository(),
            "publicaciones_repository": FakePublicacionesRepository(),
            "repartidores_repository": FakeRepartidoresRepository(),
            "restaurantes_repository": FakeRestaurantesRepository(),
            "turnos_repository": FakeTurnosRepository()
        }
        dependencias.update(overrides)

        return CuadrantesService(**dependencias)

    def test_guardar_cuadrante_normaliza_semana_y_delega_reemplazo(self):

        calendario = FakeCalendarioRepository()
        historial = FakeHistorialRepository()
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            historial_repository=historial
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
        self.assertEqual(historial.registros[0][0], "Crear cuadrante")

    def test_guardar_cuadrante_por_semana_no_mezcla_fechas(self):

        calendario = FakeCalendarioRepository()
        historial = FakeHistorialRepository()
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            historial_repository=historial
        )

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
        self.assertEqual(
            [registro[0] for registro in historial.registros],
            ["Editar asignacion", "Editar asignacion"]
        )

    def test_guardar_asignacion_vacia_registra_eliminar_turno(self):

        calendario = FakeCalendarioRepository()
        historial = FakeHistorialRepository()
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            historial_repository=historial
        )

        servicio.guardar_asignacion_turno(
            "2026-07-13",
            "lunes",
            5,
            []
        )

        self.assertEqual(historial.registros[0][0], "Eliminar turno")

    def test_copiar_semana_conserva_restaurante_turno_y_repartidor(self):

        calendario = FakeCalendarioRepository()
        historial = FakeHistorialRepository()
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
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            historial_repository=historial
        )

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
        self.assertEqual(historial.registros[0][0], "Crear cuadrante")

    def test_copiar_semana_rechaza_origen_vacio_y_misma_semana(self):

        servicio = self.crear_servicio_aislado(
            calendario_repository=FakeCalendarioRepository(),
            historial_repository=FakeHistorialRepository()
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
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            plantillas_repository=plantillas,
            historial_repository=FakeHistorialRepository()
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
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            plantillas_repository=plantillas,
            historial_repository=FakeHistorialRepository()
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
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            plantillas_repository=plantillas,
            historial_repository=FakeHistorialRepository()
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
            "13:00-16:00 (3 h)\nBK Centro - Ana"
        )
        self.assertEqual(
            estado["filas_locales"][0]["dias"]["lunes"],
            "Comida 13:00-16:00 (3 h) - Ana"
        )
        self.assertEqual(
            estado["estado_texto"],
            "Asignaciones: 1 | Todo cubierto"
        )

    def test_preparar_estado_semana_normaliza_fecha_intermedia(self):

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
        publicaciones = FakePublicacionesRepository()
        publicaciones.guardar("2026-07-13", "listo", "Semana revisada")
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            publicaciones_repository=publicaciones
        )

        estado = servicio.preparar_estado_semana(
            "2026-07-15",
            [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
            [(2, "BK Centro", "", "Centro", "", 50, 1)],
            [(10, "Ana")]
        )

        self.assertEqual(estado["indicadores"]["asignaciones"], 1)
        self.assertEqual(estado["publicacion"]["estado"], "listo")

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
            "Comida 13:00-16:00 (3 h) - Sin repartidor"
        )
        self.assertEqual(
            estado["estado_texto"],
            "Asignaciones: 1 | Con repartidor: 0 | Sin repartidor: 1"
        )
        self.assertIn(
            "Asignaciones sin repartidor",
            {alerta["tipo"] for alerta in estado["alertas"]}
        )

    def test_revisar_publicacion_bloquea_semana_sin_cuadrante(self):

        servicio = self.crear_servicio_aislado()

        revision = servicio.revisar_publicacion(
            "2026-07-13",
            [],
            [],
            []
        )

        self.assertFalse(revision["puede_publicar"])
        self.assertIn("No hay cuadrante guardado", revision["resumen"])

    def test_publicar_cuadrante_bloquea_alertas_criticas(self):

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
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario
        )

        with self.assertRaises(ValueError):

            servicio.publicar_cuadrante(
                "2026-07-13",
                [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
                [(2, "BK Centro", "", "Centro", "", 50, 1)],
                [(10, "Ana")]
            )

    def test_publicar_cuadrante_guarda_estado_e_historial(self):

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
        historial = FakeHistorialRepository()
        publicaciones = FakePublicacionesRepository()
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            historial_repository=historial,
            publicaciones_repository=publicaciones
        )

        revision = servicio.publicar_cuadrante(
            "2026-07-13",
            [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
            [(2, "BK Centro", "", "Centro", "", 50, 1)],
            [(10, "Ana")]
        )

        self.assertTrue(revision["puede_publicar"])
        self.assertEqual(publicaciones.guardadas[0][1], "publicado")
        self.assertEqual(historial.registros[0][0], "Publicar cuadrante")

    def test_marcar_cuadrante_listo_guarda_estado(self):

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
        publicaciones = FakePublicacionesRepository()
        servicio = self.crear_servicio_aislado(
            calendario_repository=calendario,
            publicaciones_repository=publicaciones
        )

        servicio.marcar_cuadrante_listo(
            "2026-07-13",
            [(5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)],
            [(2, "BK Centro", "", "Centro", "", 50, 1)],
            [(10, "Ana")]
        )

        self.assertEqual(publicaciones.guardadas[0][1], "listo")

    def test_alertas_estado_semana_cubren_panel_de_problemas(self):

        servicio = CuadrantesService()
        turnos = [
            (5, "Comida", "Comida", "13:00", "16:00", "#2563EB", 3, 1)
        ]
        restaurantes = [
            (2, "BK Centro", "", "Centro", "", 50, 1)
        ]
        repartidores = [
            {
                "id": 10,
                "nombre": "Ana",
                "horas": 2,
                "vacaciones": [{"dia": "lunes"}],
                "bajas": []
            },
            {
                "id": 11,
                "nombre": "Luis",
                "horas": 6,
                "vacaciones": [],
                "bajas": []
            }
        ]
        asignaciones = {
            ("lunes", 5): [
                {"restaurante_id": 2, "repartidor_id": None},
                {"restaurante_id": 2, "repartidor_id": 10}
            ],
            ("martes", 5): [
                {"restaurante_id": 2, "repartidor_id": 11}
            ]
        }
        calendario = [
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
            )
        ]

        alertas = servicio.alertas_estado_semana(
            "2026-07-13",
            calendario,
            asignaciones,
            {"asignaciones": 3, "sin_repartidor": 1},
            turnos,
            restaurantes,
            repartidores,
            demandas_restaurante=[],
            demandas_zona=[],
            demandas_ciudad=[]
        )
        tipos = {alerta["tipo"] for alerta in alertas}

        self.assertIn("Turnos sin cubrir", tipos)
        self.assertIn("Asignaciones sin repartidor", tipos)
        self.assertIn("Horas pendientes", tipos)
        self.assertIn("Horas extra", tipos)
        self.assertIn("Restaurantes sin demanda", tipos)
        self.assertIn("Conflictos por vacaciones/bajas", tipos)

    def test_alertas_generacion_clasifica_incidencias_y_horas_extra(self):

        servicio = CuadrantesService()

        alertas = servicio.alertas_generacion({
            "horario": {
                "lunes": {
                    "Comida": [{"repartidor_id": None}]
                }
            },
            "horas_complementarias": [{
                "nombre": "Ana",
                "usadas": 2,
                "limite": 4
            }],
            "incidencias": [
                {
                    "dia": "lunes",
                    "turno": "Comida",
                    "restaurante": "BK Centro",
                    "regla": "cobertura requerida por demanda",
                    "motivo": "Faltan 1 repartidores."
                },
                {
                    "motivo": "Luis tiene 3 horas pendientes."
                },
                {
                    "motivo": "Ana tiene ausencia, vacaciones o baja."
                }
            ]
        })
        tipos = [alerta["tipo"] for alerta in alertas]

        self.assertIn("Turnos sin cubrir", tipos)
        self.assertIn("Horas pendientes", tipos)
        self.assertIn("Horas extra", tipos)
        self.assertIn("Asignaciones sin repartidor", tipos)
        self.assertIn("Conflictos por vacaciones/bajas", tipos)

    def test_texto_resumen_generacion_muestra_resultado_y_advertencias(self):

        servicio = CuadrantesService()
        resultado = {
            "horario": {
                "lunes": {
                    "comida": [
                        {"repartidor_id": 1},
                        {"repartidor_id": None}
                    ]
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
        self.assertIn("El cuadrante aun no esta guardado.", texto)
        self.assertIn("Asignaciones generadas: 2", texto)
        self.assertIn("Asignaciones con repartidor: 1", texto)
        self.assertIn("Asignaciones sin repartidor: 1", texto)
        self.assertIn("Cobertura: 50%", texto)
        self.assertIn("Advertencias: 1", texto)
        self.assertIn("Turnos sin cubrir: 1", texto)
        self.assertIn("Horas complementarias", texto)
        self.assertIn("Ana: 2 h de 4 permitidas", texto)

    def test_precomprobar_generacion_detecta_configuracion_incompleta(self):

        servicio = CuadrantesService()

        precomprobacion = servicio.precomprobar_generacion(
            {
                "repartidores": [],
                "restaurantes": [],
                "turnos": [],
                "restaurante_turnos": [],
                "demandas_restaurante": [],
                "demandas_zona": [],
                "demandas_ciudad": []
            },
            "2026-07-13"
        )

        self.assertFalse(precomprobacion["puede_generar"])
        self.assertIn("No hay repartidores activos.", precomprobacion["texto"])
        self.assertIn("No hay restaurantes activos.", precomprobacion["texto"])

    def test_precomprobar_generacion_avisa_sin_demanda(self):

        servicio = CuadrantesService()

        precomprobacion = servicio.precomprobar_generacion(
            {
                "repartidores": [(1, "Ana", 30)],
                "restaurantes": [(2, "BK Centro", "", "Centro", "", 50, 1)],
                "turnos": [(5, "Comida", "Comida", "13:00", "16:00", "", 3, 1)],
                "restaurante_turnos": [],
                "demandas_restaurante": [],
                "demandas_zona": [],
                "demandas_ciudad": []
            },
            "2026-07-13"
        )

        self.assertTrue(precomprobacion["puede_generar"])
        self.assertIn("no tiene demanda configurada", precomprobacion["texto"])
        self.assertIn("No hay demanda configurada", precomprobacion["texto"])

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
