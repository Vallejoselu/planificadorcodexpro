import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import crear_base_datos
from services.cuadrantes_service import CuadrantesService
from services.datos_iniciales import DatosInicialesService


class TestDatosInicialesService(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        self.servicio = DatosInicialesService()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_crear_datos_minimos_prepara_base_sin_repartidores_demo(self):

        resumen = self.servicio.crear_datos_minimos()

        self.assertTrue(resumen["ciudad_creada"])
        self.assertTrue(resumen["restaurante_creado"])
        self.assertEqual(resumen["turnos_creados"], 2)
        self.assertEqual(resumen["demandas_creadas"], 14)
        self.assertEqual(resumen["repartidores_creados"], 0)
        self.assertEqual(self.contar_por_nombre("ciudades", "Ciudad principal"), 1)
        self.assertEqual(self.contar("restaurantes"), 1)
        self.assertEqual(self.contar("restaurante_turnos"), 2)
        self.assertEqual(self.contar("demanda_restaurante"), 14)
        self.assertEqual(self.contar("repartidores"), 0)
        self.assertEqual(self.contar_demo("ciudades"), 0)
        self.assertEqual(self.contar_demo("restaurantes"), 0)
        self.assertEqual(
            database.obtener_restaurante(resumen["restaurante_id"])[9],
            resumen["ciudad_id"]
        )

    def test_crear_datos_minimos_es_idempotente(self):

        self.servicio.crear_datos_minimos()
        antes = self.resumen_tablas()

        resumen = self.servicio.crear_datos_minimos()

        self.assertFalse(resumen["ciudad_creada"])
        self.assertFalse(resumen["restaurante_creado"])
        self.assertEqual(resumen["turnos_creados"], 0)
        self.assertEqual(resumen["demandas_creadas"], 0)
        self.assertEqual(self.resumen_tablas(), antes)

    def test_crear_datos_minimos_reactiva_base_existente(self):

        self.servicio.crear_datos_minimos()
        self.desactivar_todo()

        resumen = self.servicio.crear_datos_minimos()

        self.assertFalse(resumen["ciudad_creada"])
        self.assertFalse(resumen["restaurante_creado"])
        self.assertEqual(self.contar_por_nombre("ciudades", "Ciudad principal"), 1)
        self.assertEqual(self.contar("restaurantes"), 1)
        self.assertEqual(self.contar("restaurante_turnos"), 2)
        self.assertEqual(self.contar("demanda_restaurante"), 14)

    def test_flujo_base_limpia_genera_primer_cuadrante_real(self):

        semana = "2026-08-03"
        resumen = self.servicio.crear_datos_minimos()
        ana = self.crear_repartidor_real(
            "Ana",
            {
                "lunes": "No disponible",
                "martes": "No disponible",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            },
            resumen
        )
        luis = self.crear_repartidor_real(
            "Luis",
            {
                "lunes": "Ambos",
                "martes": "Ambos",
                "miercoles": "No disponible",
                "jueves": "No disponible",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            },
            resumen
        )
        servicio_cuadrantes = CuadrantesService()
        contexto = servicio_cuadrantes.obtener_contexto()

        precomprobacion = servicio_cuadrantes.precomprobar_generacion(
            contexto,
            semana
        )
        generacion = servicio_cuadrantes.generar_cuadrante(contexto, semana)
        resumen_generacion = servicio_cuadrantes.resumen_generacion(
            generacion["resultado"]
        )
        servicio_cuadrantes.guardar_cuadrante(
            semana,
            generacion["asignaciones"]
        )
        calendario = database.obtener_calendario_semanal(semana)

        self.assertTrue(precomprobacion["puede_generar"])
        self.assertEqual(precomprobacion["errores"], [])
        self.assertEqual(precomprobacion["advertencias"], [])
        self.assertEqual(resumen_generacion["estado"]["clave"], "avisos")
        self.assertEqual(resumen_generacion["asignaciones_generadas"], 14)
        self.assertEqual(resumen_generacion["asignaciones_con_repartidor"], 14)
        self.assertEqual(resumen_generacion["asignaciones_sin_repartidor"], 0)
        self.assertEqual(len(calendario), 14)
        self.assertFalse(
            any(
                fila[1] in {"lunes", "martes"} and fila[9] == ana
                for fila in calendario
            )
        )
        self.assertFalse(
            any(
                fila[1] in {"miercoles", "jueves"} and fila[9] == luis
                for fila in calendario
            )
        )

    def resumen_tablas(self):

        return {
            "ciudades": self.contar("ciudades", incluir_inactivos=True),
            "restaurantes": self.contar(
                "restaurantes",
                incluir_inactivos=True
            ),
            "repartidores": self.contar(
                "repartidores",
                incluir_inactivos=True
            ),
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

    def crear_repartidor_real(self, nombre, disponibilidad, resumen):

        return database.insertar_repartidor(
            nombre,
            30,
            "Zona principal",
            1,
            1,
            70,
            70,
            50,
            disponibilidad=disponibilidad,
            ciudad_principal_id=resumen["ciudad_id"],
            restaurante_principal_id=resumen["restaurante_id"],
            ciudades_autorizadas=[resumen["ciudad_id"]],
            restaurantes_autorizados=[resumen["restaurante_id"]]
        )

    def contar_demo(self, tabla):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"SELECT COUNT(*) FROM {tabla} WHERE nombre LIKE '[Demo] %'"
        )
        total = cursor.fetchone()[0]
        conexion.close()
        return total

    def contar_por_nombre(self, tabla, nombre):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"SELECT COUNT(*) FROM {tabla} WHERE nombre=? AND activo=1",
            (nombre,)
        )
        total = cursor.fetchone()[0]
        conexion.close()
        return total

    def desactivar_todo(self):

        conexion = database.conectar()
        cursor = conexion.cursor()

        for tabla in (
            "ciudades",
            "restaurantes",
            "restaurante_turnos",
            "demanda_restaurante"
        ):

            cursor.execute(f"UPDATE {tabla} SET activo=0")

        conexion.commit()
        conexion.close()


if __name__ == "__main__":

    unittest.main()
