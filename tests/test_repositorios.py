import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import crear_base_datos, insertar_ciudad
from repositories.ausencias_repository import AusenciasRepository
from repositories.calendario_repository import CalendarioRepository
from repositories.integraciones_repository import IntegracionesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository


class TestRepositorios(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_repartidores_repository_crea_actualiza_y_desactiva(self):

        repositorio = RepartidoresRepository()
        repartidor_id = repositorio.crear(
            "Ana",
            30,
            "Centro",
            1,
            1,
            70,
            40,
            20
        )

        self.assertEqual(repositorio.obtener_por_id(repartidor_id)["nombre"], "Ana")

        repositorio.actualizar(
            repartidor_id,
            "Ana Maria",
            20,
            "Centro",
            1,
            1,
            70,
            40,
            20
        )
        self.assertEqual(
            repositorio.obtener_por_id(repartidor_id)["nombre"],
            "Ana Maria"
        )

        repositorio.desactivar(repartidor_id)

        self.assertEqual(repositorio.listar_activos(), [])

    def test_restaurantes_y_turnos_repository_guardan_configuracion(self):

        ciudad_id = insertar_ciudad("Santiago")
        restaurantes = RestaurantesRepository()
        turnos = TurnosRepository()
        restaurante_id = restaurantes.crear(
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000000",
            50,
            ciudad_id=ciudad_id
        )
        turno_id = turnos.crear(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )

        restaurantes.guardar_turnos(restaurante_id, [{
            "nombre": "Cena local",
            "hora_inicio": "20:00",
            "hora_fin": "23:30",
            "cruza_medianoche": 0,
            "duracion": 3.5,
            "activo": 1
        }])
        turno_restaurante_id = restaurantes.listar_turnos(restaurante_id)[0][0]
        restaurantes.guardar_demanda(restaurante_id, [{
            "turno_restaurante_id": turno_restaurante_id,
            "dia_semana": "lunes",
            "fecha": None,
            "repartidores_necesarios": 3,
            "activo": 1
        }])

        self.assertEqual(restaurantes.obtener_por_id(restaurante_id)[1], "BK Centro")
        self.assertEqual(turnos.obtener_por_id(turno_id)[2], "Comida")
        self.assertEqual(restaurantes.listar_demanda(restaurante_id)[0][5], 3)

    def test_calendario_repository_reemplaza_semana(self):

        restaurantes = RestaurantesRepository()
        turnos = TurnosRepository()
        calendario = CalendarioRepository()
        restaurante_id = restaurantes.crear(
            "BK Centro",
            "",
            "Centro",
            "",
            50
        )
        turno_id = turnos.crear(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )

        calendario.guardar_turno(
            "lunes",
            turno_id,
            restaurante_id,
            fecha_inicio_semana="2026-07-13"
        )
        self.assertTrue(calendario.semana_tiene_datos("2026-07-13"))

        calendario.reemplazar_semana(
            "2026-07-13",
            {
                ("martes", turno_id): [{
                    "restaurante_id": restaurante_id,
                    "repartidor_id": None
                }]
            }
        )

        datos = calendario.listar_semana("2026-07-13")

        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0][1], "martes")

    def test_calendario_repository_reemplaza_semana_sin_tocar_anteriores(self):

        restaurantes = RestaurantesRepository()
        turnos = TurnosRepository()
        calendario = CalendarioRepository()
        restaurante_id = restaurantes.crear(
            "BK Centro",
            "",
            "Centro",
            "",
            50
        )
        turno_id = turnos.crear(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        asignacion_lunes = {
            ("lunes", turno_id): [{
                "restaurante_id": restaurante_id,
                "repartidor_id": None
            }]
        }
        asignacion_martes = {
            ("martes", turno_id): [{
                "restaurante_id": restaurante_id,
                "repartidor_id": None
            }]
        }

        calendario.reemplazar_semana("2026-07-13", asignacion_lunes)
        calendario.reemplazar_semana("2026-07-20", asignacion_martes)
        calendario.reemplazar_semana("2026-07-20", asignacion_lunes)

        self.assertEqual(
            [fila[1] for fila in calendario.listar_semana("2026-07-13")],
            ["lunes"]
        )
        self.assertEqual(
            [fila[1] for fila in calendario.listar_semana("2026-07-20")],
            ["lunes"]
        )

    def test_integraciones_repository_guarda_y_lista_eventos(self):

        repositorio = IntegracionesRepository()

        repositorio.guardar_configuracion(
            "shipday",
            "Shipday",
            activo=1,
            base_url="https://example.test"
        )
        repositorio.registrar_evento(
            "shipday",
            "sync",
            "ok",
            "Sincronizado"
        )

        self.assertEqual(
            repositorio.obtener_configuracion("shipday")[1],
            "Shipday"
        )
        self.assertEqual(repositorio.listar_eventos()[0][3], "Sincronizado")

    def test_ausencias_repository_guarda_descansos_y_disponibilidad(self):

        repartidores = RepartidoresRepository()
        ausencias = AusenciasRepository()
        repartidor_id = repartidores.crear(
            "Ana",
            30,
            "Centro",
            1,
            1,
            70,
            40,
            20
        )

        ausencias.insertar_descanso(repartidor_id, "lunes", "martes")
        ausencias.insertar_disponibilidad(
            repartidor_id,
            {"lunes": "Comidas"}
        )

        self.assertEqual(ausencias.obtener_descansos_invalidos(), [])
        disponibilidad = repartidores.obtener_por_id(
            repartidor_id
        )["disponibilidad"]

        self.assertEqual(disponibilidad["lunes"], ["comida"])


if __name__ == "__main__":

    unittest.main()
