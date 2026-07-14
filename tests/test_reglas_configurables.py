import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
from database.schema import SCHEMA_VERSION_ACTUAL
from services.reglas_runtime import obtener_reglas_motor, resetear_reglas_motor
from services.reglas_configurables import ReglasConfigurablesService
import views.reglas as reglas_view
from views.reglas import VistaReglas
from views.ventana_principal import VentanaPrincipal


class TestReglasConfigurables(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        resetear_reglas_motor()
        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_servicio_expone_reglas_en_modo_lectura(self):

        servicio = ReglasConfigurablesService()
        reglas = servicio.listar_reglas()
        resumen = servicio.resumen()

        self.assertGreaterEqual(len(reglas), 8)
        self.assertEqual(resumen["modo"], "preparacion")
        self.assertEqual(resumen["editables"], 5)
        self.assertEqual(resumen["configuradas"], 0)
        self.assertEqual(resumen["aplicadas_motor"], 3)
        self.assertTrue(
            any(regla["clave"] == "descanso_consecutivo" for regla in reglas)
        )
        self.assertTrue(
            any(regla["clave"] == "prioridad_demanda" for regla in reglas)
        )

    def test_migracion_crea_tabla_reglas_configuracion_idempotente(self):

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
            fila[1]
            for fila in cursor.execute(
                "PRAGMA index_list(reglas_configuracion)"
            ).fetchall()
        ]
        conexion.close()

        self.assertIn("reglas_configuracion", tablas)
        self.assertEqual(version, SCHEMA_VERSION_ACTUAL)
        self.assertIn("idx_reglas_configuracion_activo", indices)

    def test_servicio_guarda_y_lista_configuracion(self):

        servicio = ReglasConfigurablesService()

        resultado = servicio.guardar_configuracion({
            "max_horas_semanales": "36",
            "horas_complementarias": "prohibir",
            "penalizacion_desplazamiento": "2",
            "max_horas_diarias": "9,5",
            "max_dias_consecutivos": "4"
        })
        reglas = {
            regla["clave"]: regla
            for regla in servicio.listar_reglas()
        }

        self.assertEqual(resultado["guardadas"], 5)
        self.assertEqual(
            reglas["max_horas_semanales"]["valor_configurado"],
            "36"
        )
        self.assertEqual(
            reglas["horas_complementarias"]["valor_configurado"],
            "prohibir"
        )
        self.assertEqual(
            reglas["penalizacion_desplazamiento"]["valor_configurado"],
            "2"
        )
        self.assertEqual(
            reglas["max_horas_diarias"]["valor_configurado"],
            "9.5"
        )
        self.assertEqual(
            servicio.resumen()["configuradas"],
            5
        )
        self.assertEqual(
            obtener_reglas_motor()["horas_complementarias"],
            "prohibir"
        )

    def test_servicio_expone_configuracion_de_motor(self):

        servicio = ReglasConfigurablesService()
        servicio.guardar_configuracion({
            "max_horas_semanales": "35",
            "horas_complementarias": "permitir",
            "penalizacion_desplazamiento": "3"
        })

        configuracion = servicio.configuracion_motor()

        self.assertEqual(configuracion["max_horas_semanales"], 35)
        self.assertEqual(configuracion["horas_complementarias"], "permitir")
        self.assertEqual(configuracion["penalizacion_desplazamiento"], 3)

    def test_servicio_valida_reglas_editables(self):

        servicio = ReglasConfigurablesService()

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"descanso_consecutivo": "opcional"})

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"regla_desconocida": "1"})

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"max_horas_diarias": "30"})

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"max_horas_semanales": "100"})

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"penalizacion_desplazamiento": "20"})

        with self.assertRaises(ValueError):

            servicio.guardar_configuracion({"max_dias_consecutivos": "texto"})

    def test_servicio_restaura_valores_preparados(self):

        servicio = ReglasConfigurablesService()
        servicio.guardar_configuracion({"max_horas_diarias": "8"})

        resultado = servicio.restaurar_valores()

        self.assertEqual(resultado["restauradas"], 5)
        self.assertEqual(servicio.resumen()["configuradas"], 0)

    def test_vista_muestra_catalogo_con_edicion_controlada(self):

        vista = VistaReglas()

        self.assertEqual(vista.tabla.rowCount(), 12)
        self.assertEqual(vista.tabla.columnCount(), 6)
        self.assertIn("Modo preparacion", vista.resumen.text())
        self.assertTrue(
            bool(
                vista.tabla.item(
                    self.fila_por_clave(vista, "max_horas_diarias"),
                    2
                ).flags()
                & Qt.ItemIsEditable
            )
        )
        self.assertFalse(
            bool(
                vista.tabla.item(
                    self.fila_por_clave(vista, "descanso_consecutivo"),
                    2
                ).flags()
                & Qt.ItemIsEditable
            )
        )

    def test_vista_guarda_y_restaura_configuracion(self):

        vista = VistaReglas()
        fila = self.fila_por_clave(vista, "max_horas_diarias")
        info_original = reglas_view.QMessageBox.information
        mensajes = []

        reglas_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.tabla.item(fila, 2).setText("8")
            vista.guardar_configuracion()
            self.assertIn("5 configuradas", vista.resumen.text())
            vista.restaurar_valores()
            self.assertIn("0 configuradas", vista.resumen.text())

        finally:

            reglas_view.QMessageBox.information = info_original

    def test_ventana_principal_registra_pagina_reglas(self):

        ventana = VentanaPrincipal()

        try:

            self.assertIn("reglas", ventana.paginas)
            self.assertIn("reglas", ventana.botones)
            ventana.mostrar_pagina("reglas")
            self.assertIs(ventana.stack.currentWidget(), ventana.paginas["reglas"])

        finally:

            ventana.close()
            self.app.processEvents()

    def fila_por_clave(self, vista, clave):

        for fila in range(vista.tabla.rowCount()):

            if vista.tabla.item(fila, 0).data(Qt.UserRole) == clave:

                return fila

        self.fail(f"No se encontro la regla {clave}.")


if __name__ == "__main__":

    unittest.main()
