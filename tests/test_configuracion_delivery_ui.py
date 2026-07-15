import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
from repositories.integraciones_repository import IntegracionesRepository
import views.configuracion as configuracion_view
from views.configuracion import VistaConfiguracion


class TestConfiguracionDeliveryUi(unittest.TestCase):

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

    def test_vista_guarda_webhook_generico(self):

        vista = VistaConfiguracion()
        info_original = configuracion_view.QMessageBox.information
        mensajes = []
        configuracion_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.campo_delivery_webhook.setText(
                "https://example.test/webhook"
            )
            vista.selector_delivery_modo.setCurrentIndex(
                vista.selector_delivery_modo.findData(True)
            )
            vista.campo_delivery_credenciales.setText(
                "local://api_generica/principal"
            )
            vista.guardar_configuracion_delivery_generico()

        finally:

            configuracion_view.QMessageBox.information = info_original
            vista.close()
            self.app.processEvents()

        datos = IntegracionesRepository().obtener_configuracion("api_generica")
        opciones = json.loads(datos[5])

        self.assertTrue(mensajes)
        self.assertEqual(datos[3], "https://example.test/webhook")
        self.assertEqual(datos[4], "local://api_generica/principal")
        self.assertEqual(opciones["webhook_url"], "https://example.test/webhook")
        self.assertTrue(opciones["simulado"])
        self.assertEqual(opciones["schema"], "planificador.delivery.v1")

    def test_vista_rechaza_webhook_sin_http(self):

        vista = VistaConfiguracion()
        warning_original = configuracion_view.QMessageBox.warning
        mensajes = []
        configuracion_view.QMessageBox.warning = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.campo_delivery_webhook.setText("ftp://example.test/webhook")
            vista.guardar_configuracion_delivery_generico()

        finally:

            configuracion_view.QMessageBox.warning = warning_original
            vista.close()
            self.app.processEvents()

        datos = IntegracionesRepository().obtener_configuracion("api_generica")

        self.assertTrue(mensajes)
        self.assertEqual(datos[3] or "", "")

    def test_vista_rechaza_credencial_directa(self):

        vista = VistaConfiguracion()
        warning_original = configuracion_view.QMessageBox.warning
        mensajes = []
        configuracion_view.QMessageBox.warning = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.campo_delivery_webhook.setText(
                "https://example.test/webhook"
            )
            vista.campo_delivery_credenciales.setText("valor-directo")
            vista.guardar_configuracion_delivery_generico()

        finally:

            configuracion_view.QMessageBox.warning = warning_original
            vista.close()
            self.app.processEvents()

        datos = IntegracionesRepository().obtener_configuracion("api_generica")

        self.assertTrue(mensajes)
        self.assertEqual(datos[4] or "", "")


if __name__ == "__main__":

    unittest.main()
