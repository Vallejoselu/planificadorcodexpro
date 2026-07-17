import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import crear_base_datos
from repositories.publicaciones_repository import PublicacionesRepository


class TestPublicacionCuadrante(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_migracion_crea_tabla_publicaciones(self):

        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='cuadrante_publicaciones'
        """)
        tabla = cursor.fetchone()
        cursor.execute("SELECT version FROM schema_version WHERE id=1")
        version = cursor.fetchone()[0]
        conexion.close()

        self.assertIsNotNone(tabla)
        self.assertGreaterEqual(version, 8)

    def test_guardar_publicacion_actualiza_misma_semana(self):

        repositorio = PublicacionesRepository()

        repositorio.guardar("2026-07-15", "listo", "Listo")
        repositorio.guardar("2026-07-13", "publicado", "Publicado")

        publicaciones = repositorio.listar()

        self.assertEqual(len(publicaciones), 1)
        self.assertEqual(publicaciones[0][1], "2026-07-13")
        self.assertEqual(publicaciones[0][2], "publicado")
        self.assertEqual(publicaciones[0][3], "Publicado")

    def test_estado_publicacion_rechaza_valor_invalido(self):

        repositorio = PublicacionesRepository()

        with self.assertRaises(ValueError):

            repositorio.guardar("2026-07-13", "cerrado")


if __name__ == "__main__":

    unittest.main()
