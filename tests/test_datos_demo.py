import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import crear_base_datos
from services.datos_demo import DatosDemoService


class TestDatosDemoService(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        self.servicio = DatosDemoService()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_cargar_demo_crea_empresa_de_ejemplo(self):

        resumen = self.servicio.cargar_demo()

        self.assertEqual(resumen["ciudades"], 3)
        self.assertEqual(resumen["restaurantes"], 4)
        self.assertEqual(resumen["turnos"], 8)
        self.assertEqual(resumen["repartidores"], 5)
        self.assertEqual(self.servicio.estado()["ciudades"], 3)
        self.assertGreater(self.contar("demanda_restaurante"), 0)

    def test_cargar_demo_es_idempotente(self):

        self.servicio.cargar_demo()
        antes = self.resumen_tablas()

        self.servicio.cargar_demo()
        despues = self.resumen_tablas()

        self.assertEqual(antes, despues)

    def test_limpiar_demo_no_desactiva_datos_reales(self):

        ciudad_real = database.insertar_ciudad("Ciudad real")
        restaurante_real = database.insertar_restaurante(
            "Restaurante real",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad_real
        )
        repartidor_real = database.insertar_repartidor(
            "Repartidor real",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50
        )

        self.servicio.cargar_demo()
        self.servicio.limpiar_demo()

        self.assertEqual(database.obtener_ciudad(ciudad_real)[2], 1)
        self.assertEqual(database.obtener_restaurante(restaurante_real)[6], 1)
        self.assertEqual(database.obtener_repartidor(repartidor_real)["nombre"], "Repartidor real")
        self.assertEqual(self.servicio.estado()["ciudades"], 0)
        self.assertEqual(self.servicio.estado()["restaurantes"], 0)
        self.assertEqual(self.servicio.estado()["repartidores"], 0)

    def test_cargar_demo_tras_limpiar_reactiva_sin_duplicar(self):

        self.servicio.cargar_demo()
        self.servicio.limpiar_demo()
        antes = self.contar("ciudades", incluir_inactivos=True)

        self.servicio.cargar_demo()

        self.assertEqual(self.contar("ciudades", incluir_inactivos=True), antes)
        self.assertEqual(self.servicio.estado()["ciudades"], 3)
        self.assertEqual(self.servicio.estado()["restaurantes"], 4)
        self.assertEqual(self.servicio.estado()["repartidores"], 5)

    def test_limpiar_demo_elimina_solo_calendario_demo(self):

        ciudad_real = database.insertar_ciudad("Ciudad real")
        restaurante_real = database.insertar_restaurante(
            "Restaurante real",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad_real
        )
        repartidor_real = database.insertar_repartidor(
            "Repartidor real",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50
        )
        turno_id = database.insertar_turno(
            "Comida",
            "Comida real",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )

        self.servicio.cargar_demo()
        demo_restaurante = self.id_por_nombre(
            "restaurantes",
            "[Demo] Burger King Santiago Centro"
        )
        demo_repartidor = self.id_por_nombre(
            "repartidores",
            "[Demo] Ana Demo"
        )
        self.insertar_calendario(
            turno_id,
            demo_restaurante,
            demo_repartidor
        )
        self.insertar_calendario(
            turno_id,
            restaurante_real,
            repartidor_real
        )

        self.servicio.limpiar_demo()

        self.assertEqual(self.contar("calendario_semanal", True), 1)
        self.assertEqual(self.calendario_restante()[0], restaurante_real)

    def test_empezar_de_cero_desactiva_datos_y_vacia_cuadrantes(self):

        ciudad_id = database.insertar_ciudad("Ciudad real")
        restaurante_id = database.insertar_restaurante(
            "Restaurante real",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad_id
        )
        repartidor_id = database.insertar_repartidor(
            "Repartidor real",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50
        )
        turno_id = database.insertar_turno(
            "Comida",
            "Comida real",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        self.insertar_calendario(turno_id, restaurante_id, repartidor_id)

        resumen = self.servicio.empezar_de_cero()

        self.assertTrue(Path(resumen["respaldo"]).exists())
        self.assertEqual(self.contar("ciudades"), 0)
        self.assertEqual(self.contar("restaurantes"), 0)
        self.assertEqual(self.contar("repartidores"), 0)
        self.assertEqual(self.contar("turnos"), 0)
        self.assertEqual(self.contar("calendario_semanal", True), 0)
        self.assertEqual(resumen["repartidores"], 1)
        self.assertEqual(resumen["cuadrantes"], 1)

    def test_empezar_de_cero_elimina_datos_demo(self):

        self.servicio.cargar_demo()

        resumen = self.servicio.empezar_de_cero()

        self.assertEqual(resumen["demo_eliminados"]["ciudades"], 3)
        self.assertEqual(resumen["demo_eliminados"]["restaurantes"], 4)
        self.assertEqual(resumen["demo_eliminados"]["repartidores"], 5)
        self.assertEqual(self.contar_demo("ciudades"), 0)
        self.assertEqual(self.contar_demo("restaurantes"), 0)
        self.assertEqual(self.contar_demo("repartidores"), 0)
        self.assertEqual(self.contar("calendario_semanal", True), 0)

    def resumen_tablas(self):

        return {
            "ciudades": self.contar("ciudades", incluir_inactivos=True),
            "restaurantes": self.contar("restaurantes", incluir_inactivos=True),
            "repartidores": self.contar("repartidores", incluir_inactivos=True),
            "restaurante_turnos": self.contar(
                "restaurante_turnos",
                incluir_inactivos=True
            ),
            "demanda_restaurante": self.contar(
                "demanda_restaurante",
                incluir_inactivos=True
            )
        }

    def contar(self, tabla, incluir_inactivos=False):

        conexion = database.conectar()
        cursor = conexion.cursor()
        condicion = "" if incluir_inactivos else " WHERE activo=1"
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}{condicion}")
        total = cursor.fetchone()[0]
        conexion.close()
        return total

    def contar_demo(self, tabla):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"SELECT COUNT(*) FROM {tabla} WHERE nombre LIKE '[Demo] %'"
        )
        total = cursor.fetchone()[0]
        conexion.close()
        return total

    def id_por_nombre(self, tabla, nombre):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(f"SELECT id FROM {tabla} WHERE nombre=?", (nombre,))
        fila = cursor.fetchone()
        conexion.close()
        return fila[0]

    def insertar_calendario(self, turno_id, restaurante_id, repartidor_id):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
        INSERT INTO calendario_semanal(
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id,
            repartidor_id
        )
        VALUES(?,?,?,?,?)
        """, (
            "2026-07-06",
            "lunes",
            turno_id,
            restaurante_id,
            repartidor_id
        ))
        conexion.commit()
        conexion.close()

    def calendario_restante(self):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
        SELECT restaurante_id, repartidor_id
        FROM calendario_semanal
        """)
        fila = cursor.fetchone()
        conexion.close()
        return fila


if __name__ == "__main__":

    unittest.main()
