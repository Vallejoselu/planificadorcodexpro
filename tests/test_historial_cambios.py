import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import (
    crear_base_datos,
    insertar_restaurante,
    insertar_turno,
    obtener_historial_acciones,
    registrar_historial_accion
)
from database.schema import SCHEMA_VERSION_ACTUAL
from repositories.historial_repository import HistorialRepository
from scripts.restore_database import registrar_restauracion
from services.exportador import exportar_csv


class TestHistorialCambios(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_migracion_crea_historial_y_es_idempotente(self):

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
        version = cursor.execute(
            "SELECT version FROM schema_version WHERE id=1"
        ).fetchone()[0]
        indices = [
            fila[0]
            for fila in cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='index' AND tbl_name='historial_acciones'"
            )
        ]
        conexion.close()

        self.assertIn("historial_acciones", tablas)
        self.assertEqual(version, SCHEMA_VERSION_ACTUAL)
        self.assertEqual(indices.count("idx_historial_acciones_creado_en"), 1)

    def test_repositorio_registra_y_lista_acciones(self):

        historial = HistorialRepository()

        historial.registrar(
            "Crear cuadrante",
            "cuadrante",
            "Semana creada",
            "2026-07-13"
        )
        historial.registrar(
            "Editar asignacion",
            "calendario_semanal",
            "lunes turno 5",
            "2026-07-20"
        )

        semana = historial.listar(fecha_inicio_semana="2026-07-13")
        todos = historial.listar()

        self.assertEqual(semana[0][1], "Crear cuadrante")
        self.assertEqual(todos[0][1], "Editar asignacion")

    def test_exportar_csv_registra_historial(self):

        insertar_restaurante("BK Centro", "", "Centro", "", 50)
        insertar_turno("Comida", "Comida", "13:00", "16:00", "#2563EB", 3)
        salida = Path(self.temporal.name) / "calendario.csv"

        exportar_csv(salida, "2026-07-13")

        historial = obtener_historial_acciones()
        self.assertEqual(historial[0][1], "Exportar")
        self.assertIn("CSV", historial[0][3])

    def test_registrar_restauracion_backup_en_base_restaurada(self):

        backup = Path(self.temporal.name) / "backup.db"
        crear_base_datos()
        backup.write_bytes(database.RUTA_BD.read_bytes())

        registrar_restauracion(database.RUTA_BD, backup)

        historial = obtener_historial_acciones()
        self.assertEqual(historial[0][1], "Restaurar backup")
        self.assertIn("backup.db", historial[0][3])

    def test_registrar_historial_rechaza_accion_vacia(self):

        with self.assertRaises(ValueError):

            registrar_historial_accion("")


if __name__ == "__main__":

    unittest.main()
