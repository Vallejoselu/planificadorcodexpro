import sqlite3
import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import (
    CIUDAD_SIN_CIUDAD,
    actualizar_repartidor,
    crear_base_datos,
    guardar_demanda_zona,
    guardar_demanda_restaurante,
    guardar_repartidor_ciudades,
    guardar_repartidor_restaurantes_autorizados,
    guardar_restaurante_turnos,
    insertar_ciudad,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno,
    obtener_ciudades,
    obtener_demanda_zona,
    obtener_demanda_restaurante,
    obtener_repartidor,
    obtener_repartidor_ciudades,
    obtener_repartidor_restaurantes_autorizados,
    obtener_restaurante_turnos,
    obtener_restaurantes,
    obtener_zonas_restaurantes
)
from database.schema import SCHEMA_VERSION_ACTUAL


class TestModeloMulticiudad(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_migracion_desde_base_antigua_conserva_datos(self):

        self._crear_base_antigua()

        crear_base_datos()

        tablas = self._tablas()
        self.assertIn("ciudades", tablas)
        self.assertIn("schema_version", tablas)
        self.assertIn("restaurante_turnos", tablas)
        self.assertIn("demanda_restaurante", tablas)
        self.assertIn("demanda_zona", tablas)
        self.assertIn("repartidor_ciudades", tablas)
        self.assertIn("repartidor_restaurantes_autorizados", tablas)
        self.assertIn("calendario_semanal", tablas)

        restaurantes = obtener_restaurantes()
        self.assertEqual(len(restaurantes), 1)
        self.assertEqual(restaurantes[0][1], "BK antiguo")
        self.assertEqual(restaurantes[0][10], CIUDAD_SIN_CIUDAD)

        conexion = database.conectar()
        version = conexion.execute("""
        SELECT version
        FROM schema_version
        WHERE id=1
        """).fetchone()[0]
        conexion.close()
        self.assertEqual(version, SCHEMA_VERSION_ACTUAL)

    def test_migracion_repetida_no_duplica_sin_ciudad(self):

        crear_base_datos()
        crear_base_datos()
        crear_base_datos()

        ciudades = [
            ciudad
            for ciudad in obtener_ciudades()
            if ciudad[1] == CIUDAD_SIN_CIUDAD
        ]

        self.assertEqual(len(ciudades), 1)

    def test_conexion_activa_claves_foraneas(self):

        crear_base_datos()

        conexion = database.conectar()
        valor = conexion.execute("PRAGMA foreign_keys").fetchone()[0]
        conexion.close()

        self.assertEqual(valor, 1)

    def test_claves_foraneas_rechazan_registros_huerfanos(self):

        crear_base_datos()

        conexion = database.conectar()

        with self.assertRaises(sqlite3.IntegrityError):

            conexion.execute("""
            INSERT INTO restaurante_turnos(
                restaurante_id,
                nombre,
                hora_inicio,
                hora_fin,
                duracion
            )
            VALUES(999,'Turno huerfano','12:00','16:00',4)
            """)

        conexion.close()

    def test_schema_version_existe_y_es_idempotente(self):

        crear_base_datos()
        crear_base_datos()

        conexion = database.conectar()
        filas = conexion.execute("""
        SELECT id, version
        FROM schema_version
        """).fetchall()
        conexion.close()

        self.assertEqual(filas, [(1, SCHEMA_VERSION_ACTUAL)])

    def test_migracion_repetida_no_actualiza_schema_version_si_no_cambia(self):

        crear_base_datos()
        conexion = database.conectar()
        aplicado_en = conexion.execute("""
        SELECT aplicado_en
        FROM schema_version
        WHERE id=1
        """).fetchone()[0]
        conexion.close()

        crear_base_datos()
        conexion = database.conectar()
        aplicado_en_repetido = conexion.execute("""
        SELECT aplicado_en
        FROM schema_version
        WHERE id=1
        """).fetchone()[0]
        conexion.close()

        self.assertEqual(aplicado_en_repetido, aplicado_en)

    def test_varias_ciudades_y_restaurantes_por_ciudad(self):

        crear_base_datos()
        santiago = insertar_ciudad("Santiago")
        coruna = insertar_ciudad("A Coruna")
        ourense = insertar_ciudad("Ourense")

        for indice in range(3):

            insertar_restaurante(
                f"Burger King Santiago {indice + 1}",
                "",
                "Centro",
                "",
                50,
                ciudad_id=santiago
            )

        for indice in range(2):

            insertar_restaurante(
                f"Burger King Coruna {indice + 1}",
                "",
                "Centro",
                "",
                50,
                ciudad_id=coruna
            )
            insertar_restaurante(
                f"Burger King Ourense {indice + 1}",
                "",
                "Centro",
                "",
                50,
                ciudad_id=ourense
            )

        restaurantes = obtener_restaurantes()
        conteos = {}

        for restaurante in restaurantes:

            conteos[restaurante[10]] = conteos.get(restaurante[10], 0) + 1

        self.assertEqual(conteos["Santiago"], 3)
        self.assertEqual(conteos["A Coruna"], 2)
        self.assertEqual(conteos["Ourense"], 2)

    def test_turnos_y_demandas_diferentes_por_restaurante(self):

        crear_base_datos()
        ciudad = insertar_ciudad("Santiago")
        restaurante_a = insertar_restaurante(
            "Burger King A",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad
        )
        restaurante_b = insertar_restaurante(
            "Burger King B",
            "",
            "Norte",
            "",
            50,
            ciudad_id=ciudad
        )

        guardar_restaurante_turnos(
            restaurante_a,
            [{
                "nombre": "Comida A",
                "hora_inicio": "12:00",
                "hora_fin": "16:00",
                "cruza_medianoche": 0,
                "duracion": 4,
                "activo": 1
            }]
        )
        guardar_restaurante_turnos(
            restaurante_b,
            [{
                "nombre": "Cena B",
                "hora_inicio": "20:00",
                "hora_fin": "01:00",
                "cruza_medianoche": 1,
                "duracion": 5,
                "activo": 1
            }]
        )

        turno_a = obtener_restaurante_turnos(restaurante_a)[0]
        turno_b = obtener_restaurante_turnos(restaurante_b)[0]

        guardar_demanda_restaurante(
            restaurante_a,
            [{
                "turno_restaurante_id": turno_a[0],
                "dia_semana": "lunes",
                "repartidores_necesarios": 14,
                "activo": 1
            }]
        )
        guardar_demanda_restaurante(
            restaurante_b,
            [{
                "turno_restaurante_id": turno_b[0],
                "fecha": "2026-07-20",
                "repartidores_necesarios": 7,
                "activo": 1
            }]
        )

        self.assertEqual(turno_a[2], "Comida A")
        self.assertEqual(turno_b[5], 1)
        self.assertEqual(
            obtener_demanda_restaurante(restaurante_a)[0][5],
            14
        )
        self.assertEqual(
            obtener_demanda_restaurante(restaurante_b)[0][3],
            "2026-07-20"
        )

    def test_autorizacion_y_principales_de_repartidor(self):

        crear_base_datos()
        ciudad = insertar_ciudad("Santiago")
        restaurante = insertar_restaurante(
            "Burger King Santiago",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad
        )
        repartidor_id = insertar_repartidor(
            "Ana",
            20,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            ciudad_principal_id=ciudad,
            restaurante_principal_id=restaurante,
            apoyo_flexible=1,
            horas_complementarias=5,
            max_horas_diarias=8,
            max_dias_consecutivos=4,
            ciudades_autorizadas=[ciudad],
            restaurantes_autorizados=[restaurante]
        )

        repartidor = obtener_repartidor(repartidor_id)

        self.assertEqual(repartidor["ciudad_principal_id"], ciudad)
        self.assertEqual(repartidor["restaurante_principal_id"], restaurante)
        self.assertEqual(repartidor["apoyo_flexible"], 1)
        self.assertEqual(obtener_repartidor_ciudades(repartidor_id), [ciudad])
        self.assertEqual(
            obtener_repartidor_restaurantes_autorizados(repartidor_id),
            [restaurante]
        )

        actualizar_repartidor(
            repartidor_id,
            "Ana",
            20,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            ciudad_principal_id=ciudad,
            restaurante_principal_id=restaurante,
            ciudades_autorizadas=[ciudad],
            restaurantes_autorizados=[restaurante]
        )
        guardar_repartidor_ciudades(repartidor_id, [ciudad])
        guardar_repartidor_restaurantes_autorizados(
            repartidor_id,
            [restaurante]
        )

        self.assertEqual(obtener_repartidor_ciudades(repartidor_id), [ciudad])
        self.assertEqual(
            obtener_repartidor_restaurantes_autorizados(repartidor_id),
            [restaurante]
        )

    def test_demanda_admite_fecha_valida_sin_dia_semana(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        guardar_demanda_restaurante(
            restaurante,
            [{
                "turno_restaurante_id": turno,
                "fecha": "2026-07-20",
                "repartidores_necesarios": 3
            }]
        )

        self.assertEqual(
            obtener_demanda_restaurante(restaurante)[0][3],
            "2026-07-20"
        )

    def test_demanda_admite_dia_semana_valido_sin_fecha(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        guardar_demanda_restaurante(
            restaurante,
            [{
                "turno_restaurante_id": turno,
                "dia_semana": "lunes",
                "repartidores_necesarios": 3
            }]
        )

        self.assertEqual(
            obtener_demanda_restaurante(restaurante)[0][4],
            "lunes"
        )

    def test_demanda_rechaza_fecha_y_dia_vacios(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        with self.assertRaises(ValueError):

            guardar_demanda_restaurante(
                restaurante,
                [{
                    "turno_restaurante_id": turno,
                    "repartidores_necesarios": 3
                }]
            )

    def test_demanda_rechaza_fecha_y_dia_informados(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        with self.assertRaises(ValueError):

            guardar_demanda_restaurante(
                restaurante,
                [{
                    "turno_restaurante_id": turno,
                    "fecha": "2026-07-20",
                    "dia_semana": "lunes",
                    "repartidores_necesarios": 3
                }]
            )

    def test_demanda_rechaza_dia_semana_invalido(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        with self.assertRaises(ValueError):

            guardar_demanda_restaurante(
                restaurante,
                [{
                    "turno_restaurante_id": turno,
                    "dia_semana": "festivo",
                    "repartidores_necesarios": 3
                }]
            )

    def test_demanda_rechaza_duplicada_por_fecha(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        with self.assertRaises(ValueError):

            guardar_demanda_restaurante(
                restaurante,
                [{
                    "turno_restaurante_id": turno,
                    "fecha": "2026-07-20",
                    "repartidores_necesarios": 3
                }, {
                    "turno_restaurante_id": turno,
                    "fecha": "2026-07-20",
                    "repartidores_necesarios": 4
                }]
            )

    def test_demanda_rechaza_duplicada_por_dia_semana(self):

        restaurante, turno = self._crear_restaurante_con_turno()

        with self.assertRaises(ValueError):

            guardar_demanda_restaurante(
                restaurante,
                [{
                    "turno_restaurante_id": turno,
                    "dia_semana": "lunes",
                    "repartidores_necesarios": 3
                }, {
                    "turno_restaurante_id": turno,
                    "dia_semana": "lunes",
                    "repartidores_necesarios": 4
                }]
            )

    def test_demanda_zona_admite_fecha_dia_y_demanda_cero(self):

        turno = self._crear_turno_global()

        guardar_demanda_zona([{
            "zona": "Centro",
            "turno_id": turno,
            "fecha": "2026-07-20",
            "repartidores_necesarios": 0
        }, {
            "zona": "Norte",
            "turno_id": turno,
            "dia_semana": "lunes",
            "repartidores_necesarios": 3
        }])

        demandas = obtener_demanda_zona()

        self.assertEqual(len(demandas), 2)
        self.assertEqual(demandas[0][1], "Centro")
        self.assertEqual(demandas[0][5], 0)
        self.assertEqual(demandas[1][4], "lunes")

    def test_demanda_zona_rechaza_periodos_invalidos(self):

        turno = self._crear_turno_global()

        casos = (
            {
                "zona": "Centro",
                "turno_id": turno,
                "repartidores_necesarios": 1
            },
            {
                "zona": "Centro",
                "turno_id": turno,
                "fecha": "2026-07-20",
                "dia_semana": "lunes",
                "repartidores_necesarios": 1
            },
            {
                "zona": "Centro",
                "turno_id": turno,
                "dia_semana": "festivo",
                "repartidores_necesarios": 1
            }
        )

        for demanda in casos:

            with self.assertRaises(ValueError):

                guardar_demanda_zona([demanda])

    def test_demanda_zona_rechaza_duplicadas_por_fecha_y_dia(self):

        turno = self._crear_turno_global()

        with self.assertRaises(ValueError):

            guardar_demanda_zona([{
                "zona": "Centro",
                "turno_id": turno,
                "fecha": "2026-07-20",
                "repartidores_necesarios": 1
            }, {
                "zona": "centro",
                "turno_id": turno,
                "fecha": "2026-07-20",
                "repartidores_necesarios": 2
            }])

        with self.assertRaises(ValueError):

            guardar_demanda_zona([{
                "zona": "Centro",
                "turno_id": turno,
                "dia_semana": "lunes",
                "repartidores_necesarios": 1
            }, {
                "zona": "Centro",
                "turno_id": turno,
                "dia_semana": "lunes",
                "repartidores_necesarios": 2
            }])

    def test_demanda_zona_migracion_repetida_no_duplica_datos(self):

        turno = self._crear_turno_global()
        guardar_demanda_zona([{
            "zona": "Centro",
            "turno_id": turno,
            "dia_semana": "lunes",
            "repartidores_necesarios": 2
        }])

        crear_base_datos()
        crear_base_datos()

        demandas = obtener_demanda_zona()

        self.assertEqual(len(demandas), 1)
        self.assertEqual(demandas[0][5], 2)

    def test_obtener_zonas_restaurantes_lista_zonas_activas(self):

        crear_base_datos()
        ciudad = insertar_ciudad("Santiago")
        insertar_restaurante("BK Centro", "", "Centro", "", 50, ciudad_id=ciudad)
        insertar_restaurante("BK Norte", "", "Norte", "", 50, ciudad_id=ciudad)

        self.assertEqual(
            obtener_zonas_restaurantes(),
            ["Centro", "Norte"]
        )

    def _crear_base_antigua(self):

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
        CREATE TABLE calendario_semanal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            turno_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            repartidor_id INTEGER
        );
        INSERT INTO restaurantes(nombre,zona) VALUES('BK antiguo','Centro');
        INSERT INTO turnos(tipo,nombre,hora_inicio,hora_fin,color,duracion)
        VALUES('Cena','Cena','20:00','23:30','#16A34A',3.5);
        INSERT INTO calendario_semanal(dia,turno_id,restaurante_id)
        VALUES('viernes',1,1);
        """)
        conexion.commit()
        conexion.close()

    def _crear_restaurante_con_turno(self):

        crear_base_datos()
        ciudad = insertar_ciudad("Santiago")
        restaurante = insertar_restaurante(
            "Burger King Santiago",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad
        )
        guardar_restaurante_turnos(
            restaurante,
            [{
                "nombre": "Cena",
                "hora_inicio": "20:00",
                "hora_fin": "23:00",
                "duracion": 3,
                "activo": 1
            }]
        )
        turno = obtener_restaurante_turnos(restaurante)[0][0]

        return restaurante, turno

    def _crear_turno_global(self):

        crear_base_datos()

        return insertar_turno(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )

    def _tablas(self):

        conexion = sqlite3.connect(database.RUTA_BD)
        tablas = {
            fila[0]
            for fila in conexion.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        conexion.close()

        return tablas


if __name__ == "__main__":

    unittest.main()
