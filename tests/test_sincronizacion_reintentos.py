import sqlite3
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import database.database as database
from database.database import crear_base_datos
from database.schema import SCHEMA_VERSION_ACTUAL
from repositories.sincronizaciones_repository import SincronizacionesRepository
from services.sincronizacion import (
    ESTADO_AGOTADO,
    ESTADO_COMPLETADO,
    ESTADO_PENDIENTE,
    ESTADO_REINTENTO,
    ServicioSincronizacion,
    calcular_proximo_intento
)


class TestSincronizacionReintentos(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_migracion_crea_tabla_e_indices_idempotente(self):

        crear_base_datos()
        crear_base_datos()
        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        tablas = {
            fila[0]
            for fila in cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        indices = [
            fila[1]
            for fila in cursor.execute(
                "PRAGMA index_list(integraciones_sincronizaciones)"
            ).fetchall()
        ]
        version = cursor.execute(
            "SELECT version FROM schema_version WHERE id=1"
        ).fetchone()[0]
        conexion.close()

        self.assertIn("integraciones_sincronizaciones", tablas)
        self.assertEqual(version, SCHEMA_VERSION_ACTUAL)
        self.assertEqual(
            indices.count("idx_integraciones_sincronizaciones_estado"),
            1
        )

    def test_repositorio_registra_y_lista_sincronizaciones(self):

        repositorio = SincronizacionesRepository()

        sincronizacion_id = repositorio.registrar(
            "api_generica",
            "webhook_simulado",
            ESTADO_PENDIENTE,
            '{"ok": true}',
            max_reintentos=2
        )
        fila = repositorio.obtener(sincronizacion_id)
        listado = repositorio.listar(proveedor="api_generica")

        self.assertEqual(fila[1], "api_generica")
        self.assertEqual(fila[2], "webhook_simulado")
        self.assertEqual(fila[3], ESTADO_PENDIENTE)
        self.assertEqual(listado[0][0], sincronizacion_id)

    def test_servicio_registra_completado(self):

        servicio = ServicioSincronizacion()
        sincronizacion_id = servicio.registrar_pendiente(
            "api_generica",
            "exportar_horarios",
            {"turnos": 1}
        )

        fila = servicio.registrar_completado(
            sincronizacion_id,
            {"status": "ok"}
        )

        self.assertEqual(fila[3], ESTADO_COMPLETADO)
        self.assertIn('"status": "ok"', fila[5])
        self.assertEqual(fila[7], 0)

    def test_servicio_programa_reintento_con_backoff(self):

        servicio = ServicioSincronizacion()
        ahora = datetime(2026, 7, 15, 10, 0, 0)
        sincronizacion_id = servicio.registrar_pendiente(
            "api_generica",
            "webhook_simulado",
            {"turnos": []},
            max_reintentos=3
        )

        fila = servicio.registrar_error(
            sincronizacion_id,
            "timeout",
            ahora=ahora,
            base_minutos=10
        )

        self.assertEqual(fila[3], ESTADO_REINTENTO)
        self.assertEqual(fila[6], "timeout")
        self.assertEqual(fila[7], 1)
        self.assertEqual(fila[9], "2026-07-15 10:10:00")

    def test_servicio_agota_reintentos(self):

        servicio = ServicioSincronizacion()
        ahora = datetime(2026, 7, 15, 10, 0, 0)
        sincronizacion_id = servicio.registrar_pendiente(
            "api_generica",
            "webhook_simulado",
            {"turnos": []},
            max_reintentos=1
        )

        fila = servicio.registrar_error(
            sincronizacion_id,
            "error permanente",
            ahora=ahora
        )

        self.assertEqual(fila[3], ESTADO_AGOTADO)
        self.assertEqual(fila[7], 1)
        self.assertIsNone(fila[9])

    def test_lista_solo_pendientes_vencidos(self):

        servicio = ServicioSincronizacion()
        repositorio = SincronizacionesRepository()
        vencido = "2026-07-15 10:00:00"
        futuro = "2026-07-15 12:00:00"
        repositorio.registrar(
            "api_generica",
            "vencido",
            ESTADO_REINTENTO,
            max_reintentos=3,
            intentos=1,
            proximo_intento=vencido
        )
        repositorio.registrar(
            "api_generica",
            "futuro",
            ESTADO_REINTENTO,
            max_reintentos=3,
            intentos=1,
            proximo_intento=futuro
        )
        repositorio.registrar(
            "api_generica",
            "agotado",
            ESTADO_REINTENTO,
            max_reintentos=1,
            intentos=1,
            proximo_intento=vencido
        )

        pendientes = servicio.listar_pendientes("2026-07-15 11:00:00")

        self.assertEqual([fila[2] for fila in pendientes], ["vencido"])

    def test_calculo_backoff_duplica_espera(self):

        ahora = datetime(2026, 7, 15, 10, 0, 0)

        self.assertEqual(
            calcular_proximo_intento(2, ahora, base_minutos=15),
            "2026-07-15 10:30:00"
        )


if __name__ == "__main__":

    unittest.main()
