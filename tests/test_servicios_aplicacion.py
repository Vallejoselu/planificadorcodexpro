import unittest

from services.cuadrantes_service import CuadrantesService
from services.repartidores_service import RepartidoresService
from services.restaurantes_service import RestaurantesService
from services.turnos_service import TurnosService


class FakeCalendarioRepository:

    def __init__(self):

        self.reemplazos = []
        self.eliminados = []
        self.guardados = []
        self.semanas = {}

    def reemplazar_semana(self, fecha_inicio_semana, asignaciones):

        self.reemplazos.append((fecha_inicio_semana, asignaciones))

    def listar_semana(self, fecha_inicio_semana):

        return self.semanas.get(fecha_inicio_semana, [])

    def semana_tiene_datos(self, fecha_inicio_semana):

        return bool(self.semanas.get(fecha_inicio_semana))

    def eliminar_turno(
        self,
        dia,
        turno_id,
        restaurante_id=None,
        fecha_inicio_semana=None
    ):

        self.eliminados.append((dia, turno_id, restaurante_id, fecha_inicio_semana))

    def guardar_turno(
        self,
        dia,
        turno_id,
        restaurante_id,
        repartidor_id=None,
        fecha_inicio_semana=None
    ):

        self.guardados.append((
            dia,
            turno_id,
            restaurante_id,
            repartidor_id,
            fecha_inicio_semana
        ))


class FakeTurnosRepository:

    def __init__(self):

        self.turnos = []

    def listar_activos(self):

        return self.turnos

    def listar_todos(self):

        return self.turnos

    def obtener_por_id(self, turno_id):

        return next(
            turno
            for turno in self.turnos
            if turno[0] == turno_id
        )

    def desactivar(self, turno_id):

        self.turnos = [
            turno
            for turno in self.turnos
            if turno[0] != turno_id
        ]

    def obtener_o_crear_para_restaurante(self, turno_restaurante_id):

        return 900 + turno_restaurante_id


class FakePlanningEngine:

    def __init__(self, resultado):

        self.resultado = resultado
        self.llamadas = []

    def generar(self, *args, **kwargs):

        self.llamadas.append(("generar", args, kwargs))
        return self.resultado

    def generar_multiciudad(self, *args, **kwargs):

        self.llamadas.append(("generar_multiciudad", args, kwargs))
        return self.resultado


class FakeRepartidoresRepository:

    def __init__(self):

        self.repartidores = []

    def listar_activos(self):

        return self.repartidores

    def obtener_por_id(self, repartidor_id):

        return {"id": repartidor_id, "nombre": "Ana"}

    def desactivar(self, repartidor_id):

        self.repartidores = [
            repartidor
            for repartidor in self.repartidores
            if repartidor[0] != repartidor_id
        ]


class FakeRestaurantesRepository:

    def __init__(self):

        self.restaurantes = []
        self.fijos = {}
        self.turnos = {}
        self.demandas = {}

    def listar_activos(self):

        return [
            restaurante
            for restaurante in self.restaurantes
            if restaurante[6]
        ]

    def listar_todos(self):

        return self.restaurantes

    def obtener_por_id(self, restaurante_id):

        return next(
            restaurante
            for restaurante in self.restaurantes
            if restaurante[0] == restaurante_id
        )

    def obtener_repartidores_fijos(self, restaurante_id):

        return self.fijos.get(restaurante_id, [])

    def listar_turnos(self, restaurante_id):

        return self.turnos.get(restaurante_id, [])

    def listar_demanda(self, restaurante_id):

        return self.demandas.get(restaurante_id, [])

    def desactivar(self, restaurante_id):

        self.restaurantes = [
            restaurante
            for restaurante in self.restaurantes
            if restaurante[0] != restaurante_id
        ]


class FakeCiudadesRepository:

    def __init__(self):

        self.ciudades = []

    def listar_activas(self):

        return self.ciudades


class TestServiciosAplicacion(unittest.TestCase):

    def test_cuadrantes_service_convierte_resultado_legacy(self):

        servicio = CuadrantesService()
        resultado = {
            "horario": {
                "lunes": {
                    "comida": [
                        {"restaurante_id": 1, "repartidor_id": 10},
                        {"restaurante_id": 1, "repartidor_id": 10}
                    ]
                }
            }
        }

        asignaciones = servicio.convertir_resultado_planificador(
            resultado,
            {"comida": 5}
        )

        self.assertEqual(
            asignaciones,
            {("lunes", 5): [{"restaurante_id": 1, "repartidor_id": 10}]}
        )

    def test_cuadrantes_service_convierte_resultado_multiciudad(self):

        servicio = CuadrantesService()
        resultado = {
            "horario": {
                "lunes": {
                    "restaurante_1_turno_7": [{
                        "restaurante_id": 1,
                        "turno_restaurante_id": 7,
                        "repartidor_id": 10
                    }]
                }
            }
        }

        asignaciones = servicio.convertir_resultado_multiciudad(resultado)

        self.assertEqual(
            asignaciones,
            {
                ("lunes", ("restaurante_turno", 7)): [{
                    "restaurante_id": 1,
                    "repartidor_id": 10
                }]
            }
        )

    def test_cuadrantes_service_guarda_resolviendo_turno_de_restaurante(self):

        calendario = FakeCalendarioRepository()
        turnos = FakeTurnosRepository()
        servicio = CuadrantesService(
            calendario_repository=calendario,
            turnos_repository=turnos
        )

        servicio.guardar_cuadrante(
            "2026-07-15",
            {
                ("miercoles", ("restaurante_turno", 7)): [{
                    "restaurante_id": 1,
                    "repartidor_id": None
                }]
            }
        )

        self.assertEqual(calendario.reemplazos[0][0], "2026-07-13")
        self.assertEqual(
            calendario.reemplazos[0][1],
            {
                ("miercoles", 907): [{
                    "restaurante_id": 1,
                    "repartidor_id": None
                }]
            }
        )

    def test_cuadrantes_service_valida_contexto_de_generacion(self):

        servicio = CuadrantesService()

        with self.assertRaisesRegex(ValueError, "repartidores"):

            servicio.validar_contexto_generacion({
                "repartidores": [],
                "restaurantes": [(1,)],
                "turnos": [(1,)],
                "restaurante_turnos": []
            })

    def test_cuadrantes_service_generar_usa_planificador_sin_ui(self):

        resultado = {
            "horario": {
                "lunes": {
                    "comida": [{"restaurante_id": 1, "repartidor_id": 10}]
                }
            },
            "resumen": [],
            "incidencias": []
        }
        engine = FakePlanningEngine(resultado)
        servicio = CuadrantesService(planning_engine=engine)

        generado = servicio.generar_cuadrante(
            {
                "ciudades": [],
                "turnos": [(5, "Comida", "Comida", "13:00", "16:00", "", 3, 1)],
                "restaurantes": [(1, "", "", "", "", "", 1)],
                "restaurante_turnos": [],
                "demandas_restaurante": [],
                "repartidores": [(10, "Ana")]
            },
            "2026-07-15"
        )

        self.assertEqual(engine.llamadas[0][0], "generar")
        self.assertEqual(
            generado["asignaciones"],
            {("lunes", 5): [{"restaurante_id": 1, "repartidor_id": 10}]}
        )

    def test_repartidores_service_formatea_descanso_y_disponibilidad(self):

        servicio = RepartidoresService()
        repartidor = (
            1,
            "Ana",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            "lunes",
            "martes",
            {"lunes": ["comida"], "martes": ["comida", "noche"]}
        )

        self.assertEqual(
            servicio.formatear_descanso(repartidor),
            "lunes - martes"
        )
        self.assertEqual(
            servicio.formatear_disponibilidad(repartidor[11]),
            "lunes: comidas | martes: ambos"
        )

    def test_restaurantes_service_prepara_texto_de_repartidores_fijos(self):

        restaurantes_repo = FakeRestaurantesRepository()
        restaurantes_repo.restaurantes = [
            (1, "Local A", "", "Centro", "", "", 1, "", "", None, "Santiago")
        ]
        restaurantes_repo.fijos = {1: [10]}
        repartidores_repo = FakeRepartidoresRepository()
        repartidores_repo.repartidores = [(10, "Ana")]
        servicio = RestaurantesService(
            restaurantes_repository=restaurantes_repo,
            repartidores_repository=repartidores_repo
        )

        datos = servicio.listar_tabla()

        self.assertEqual(datos[0]["repartidores_fijos_texto"], "Ana")

    def test_turnos_service_delega_operaciones_basicas(self):

        turnos_repo = FakeTurnosRepository()
        turnos_repo.turnos = [
            (1, "Comida", "Comida", "13:00", "16:00", "", 3, 1)
        ]
        servicio = TurnosService(turnos_repo)

        self.assertEqual(servicio.obtener_por_id(1)[2], "Comida")
        servicio.desactivar(1)
        self.assertEqual(servicio.listar_todos(), [])


if __name__ == "__main__":

    unittest.main()
