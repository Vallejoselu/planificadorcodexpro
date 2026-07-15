import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
from services.sincronizacion import (
    ESTADO_COMPLETADO,
    ESTADO_REINTENTO,
    ServicioSincronizacion
)
from views.configuracion import VistaConfiguracion


class TestConfiguracionSincronizacionesUi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_vista_muestra_ultimas_sincronizaciones(self):

        servicio = ServicioSincronizacion()
        completada_id = servicio.registrar_pendiente(
            "api_generica",
            "exportar_horarios",
            {"turnos": 2}
        )
        servicio.registrar_completado(
            completada_id,
            {"status": "ok"}
        )
        con_error_id = servicio.registrar_pendiente(
            "api_generica",
            "enviar_webhook",
            {"turnos": 4},
            max_reintentos=3
        )
        servicio.registrar_error(
            con_error_id,
            "timeout",
            ahora=datetime(2026, 7, 15, 10, 0, 0),
            base_minutos=10
        )

        vista = VistaConfiguracion()

        try:

            self.assertEqual(vista.tabla_sincronizaciones.rowCount(), 2)
            filas = [
                [
                    vista.tabla_sincronizaciones.item(fila, columna).text()
                    for columna in range(
                        vista.tabla_sincronizaciones.columnCount()
                    )
                ]
                for fila in range(vista.tabla_sincronizaciones.rowCount())
            ]

            contenido = "\n".join("|".join(fila) for fila in filas)
            self.assertIn("api_generica", contenido)
            self.assertIn("exportar_horarios", contenido)
            self.assertIn("enviar_webhook", contenido)
            self.assertIn(ESTADO_COMPLETADO, contenido)
            self.assertIn(ESTADO_REINTENTO, contenido)
            self.assertIn("timeout", contenido)
            self.assertIn("2026-07-15 10:10:00", contenido)

        finally:

            vista.close()
            self.app.processEvents()

    def test_actualizar_recarga_tabla_sincronizaciones(self):

        servicio = ServicioSincronizacion()
        vista = VistaConfiguracion()

        try:

            self.assertEqual(vista.tabla_sincronizaciones.rowCount(), 0)
            servicio.registrar_pendiente(
                "api_generica",
                "webhook_simulado",
                {"ok": True}
            )
            vista.cargar_sincronizaciones()

            self.assertEqual(vista.tabla_sincronizaciones.rowCount(), 1)
            self.assertEqual(
                vista.tabla_sincronizaciones.item(0, 1).text(),
                "webhook_simulado"
            )

        finally:

            vista.close()
            self.app.processEvents()


if __name__ == "__main__":

    unittest.main()
