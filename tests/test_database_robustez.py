import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import (
    crear_base_datos,
    diagnosticar_base_datos,
    reparar_base_datos
)
from database.schema import CIUDAD_SIN_CIUDAD, SCHEMA_VERSION_ACTUAL


class TestRobustezBaseDatos(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_diagnostico_limpio_en_base_nueva(self):

        crear_base_datos()

        diagnostico = diagnosticar_base_datos()

        self.assertTrue(diagnostico["ok"])
        self.assertEqual(diagnostico["errores"], [])
        self.assertEqual(diagnostico["advertencias"], [])
        self.assertIn("Indices esperados presentes.", diagnostico["info"])

    def test_diagnostico_avisa_datos_antiguos_invalidos(self):

        crear_base_datos()
        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("""
        INSERT INTO repartidores(
            nombre,
            horas,
            zona,
            activo
        )
        VALUES('Horas antiguas', 37, 'Centro', 1)
        """)
        repartidor_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO descansos(repartidor_id, dia_inicio, dia_fin, activo)
        VALUES(?, 'sabado', 'domingo', 1)
        """,(repartidor_id,))
        cursor.execute("""
        INSERT INTO restaurantes(nombre, zona, activo)
        VALUES('Restaurante sin ciudad', 'Centro', 1)
        """)
        restaurante_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO restaurante_turnos(
            restaurante_id,
            nombre,
            hora_inicio,
            hora_fin,
            duracion,
            activo
        )
        VALUES(?, 'Comida', '13:00', '16:00', 3, 1)
        """,(restaurante_id,))
        turno_restaurante_id = cursor.lastrowid
        cursor.execute("""
        INSERT INTO demanda_restaurante(
            restaurante_id,
            turno_restaurante_id,
            fecha,
            dia_semana,
            repartidores_necesarios,
            activo
        )
        VALUES(?, ?, NULL, NULL, -1, 1)
        """,(restaurante_id, turno_restaurante_id))
        conexion.commit()
        conexion.close()

        diagnostico = diagnosticar_base_datos()
        texto = " ".join(diagnostico["advertencias"])

        self.assertFalse(diagnostico["ok"])
        self.assertIn("horas contratadas no validas", texto)
        self.assertIn("Descansos antiguos no validos", texto)
        self.assertIn("restaurantes antiguos no tienen ciudad", texto)
        self.assertIn("Demandas antiguas invalidas", texto)

    def test_reparacion_migra_base_antigua_con_duplicados(self):

        self._crear_base_antigua_con_duplicados()

        diagnostico = reparar_base_datos()

        self.assertTrue(diagnostico["ok"])
        self.assertIn("acciones", diagnostico)

        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT version FROM schema_version WHERE id=1")
        self.assertEqual(cursor.fetchone()[0], SCHEMA_VERSION_ACTUAL)
        cursor.execute("SELECT COUNT(*) FROM ciudades WHERE nombre=?", (
            CIUDAD_SIN_CIUDAD,
        ))
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute("""
        SELECT COUNT(*)
        FROM demanda_restaurante
        WHERE activo=1
        """)
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute("SELECT COUNT(*) FROM calendario_semanal")
        self.assertEqual(cursor.fetchone()[0], 1)
        conexion.close()

    def test_reparacion_es_idempotente_y_no_duplica_sin_ciudad(self):

        self._crear_base_antigua_con_duplicados()

        reparar_base_datos()
        reparar_base_datos()

        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) FROM ciudades WHERE nombre=?", (
            CIUDAD_SIN_CIUDAD,
        ))
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute("""
        SELECT COUNT(*)
        FROM demanda_restaurante
        WHERE activo=1
        """)
        self.assertEqual(cursor.fetchone()[0], 1)
        conexion.close()

    def test_diagnostico_detecta_clave_foranea_rota(self):

        crear_base_datos()
        conexion = sqlite3.connect(database.RUTA_BD)
        conexion.execute("PRAGMA foreign_keys=OFF")
        conexion.execute("""
        INSERT INTO calendario_semanal(
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id,
            repartidor_id
        )
        VALUES('2026-07-13', 'lunes', 999, 999, NULL)
        """)
        conexion.commit()
        conexion.close()

        diagnostico = diagnosticar_base_datos()

        self.assertFalse(diagnostico["ok"])
        self.assertTrue(
            any("Clave foranea rota" in error for error in diagnostico["errores"])
        )

    def _crear_base_antigua_con_duplicados(self):

        conexion = sqlite3.connect(database.RUTA_BD)
        cursor = conexion.cursor()
        cursor.executescript("""
        CREATE TABLE repartidores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            horas INTEGER NOT NULL,
            zona TEXT,
            doble_turno INTEGER DEFAULT 1,
            puede_hasta_la_una INTEGER DEFAULT 1,
            prioridad_comida INTEGER DEFAULT 50,
            prioridad_noche INTEGER DEFAULT 50,
            prioridad_grela INTEGER DEFAULT 50,
            activo INTEGER DEFAULT 1,
            observaciones TEXT
        );
        CREATE TABLE restaurantes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            zona TEXT,
            telefono TEXT,
            prioridad INTEGER DEFAULT 50,
            activo INTEGER DEFAULT 1,
            observaciones TEXT
        );
        CREATE TABLE turnos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            color TEXT NOT NULL,
            duracion REAL NOT NULL,
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE restaurante_turnos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurante_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            cruza_medianoche INTEGER DEFAULT 0,
            duracion REAL NOT NULL,
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE demanda_restaurante(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            restaurante_id INTEGER NOT NULL,
            turno_restaurante_id INTEGER NOT NULL,
            fecha TEXT,
            dia_semana TEXT,
            repartidores_necesarios INTEGER NOT NULL,
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE calendario_semanal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            turno_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            repartidor_id INTEGER
        );
        INSERT INTO repartidores(nombre, horas, zona)
        VALUES('Ana', 40, 'Centro');
        INSERT INTO restaurantes(nombre, zona)
        VALUES('BK Centro', 'Centro');
        INSERT INTO turnos(tipo, nombre, hora_inicio, hora_fin, color, duracion)
        VALUES('Comida', 'Comida', '13:00', '16:00', '#2563EB', 3);
        INSERT INTO restaurante_turnos(
            restaurante_id,
            nombre,
            hora_inicio,
            hora_fin,
            duracion
        )
        VALUES(1, 'Comida', '13:00', '16:00', 3);
        INSERT INTO demanda_restaurante(
            restaurante_id,
            turno_restaurante_id,
            fecha,
            repartidores_necesarios,
            activo
        )
        VALUES(1, 1, '2026-07-13', 2, 1);
        INSERT INTO demanda_restaurante(
            restaurante_id,
            turno_restaurante_id,
            fecha,
            repartidores_necesarios,
            activo
        )
        VALUES(1, 1, '2026-07-13', 3, 1);
        INSERT INTO calendario_semanal(dia, turno_id, restaurante_id, repartidor_id)
        VALUES('lunes', 1, 1, 1);
        INSERT INTO calendario_semanal(dia, turno_id, restaurante_id, repartidor_id)
        VALUES('lunes', 1, 1, 1);
        """)
        conexion.commit()
        conexion.close()


if __name__ == "__main__":

    unittest.main()
