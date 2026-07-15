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


class TestConfiguracionEmailUi(unittest.TestCase):

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

    def test_migracion_siembra_integracion_email(self):

        repositorio = IntegracionesRepository()
        email = repositorio.obtener_configuracion("email")

        self.assertIsNotNone(email)
        self.assertEqual(email[0], "email")
        self.assertEqual(email[1], "Email")

    def test_vista_guarda_configuracion_email_con_referencia(self):

        vista = VistaConfiguracion()
        info_original = configuracion_view.QMessageBox.information
        mensajes = []
        configuracion_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.campo_email_host.setText("smtp.example.test")
            vista.campo_email_puerto.setValue(2525)
            vista.selector_email_tls.setCurrentIndex(
                vista.selector_email_tls.findData(False)
            )
            vista.campo_email_remitente.setText("planificador@example.test")
            vista.campo_email_destinatarios.setText(
                "ana@example.test; luis@example.test"
            )
            vista.campo_email_credenciales.setText("local://email/principal")
            vista.guardar_configuracion_email()

        finally:

            configuracion_view.QMessageBox.information = info_original
            vista.close()
            self.app.processEvents()

        datos = IntegracionesRepository().obtener_configuracion("email")
        opciones = json.loads(datos[5])

        self.assertTrue(mensajes)
        self.assertEqual(datos[3], "smtp.example.test")
        self.assertEqual(datos[4], "local://email/principal")
        self.assertEqual(opciones["smtp_puerto"], 2525)
        self.assertFalse(opciones["smtp_tls"])
        self.assertEqual(
            opciones["destinatarios"],
            "ana@example.test; luis@example.test"
        )

    def test_vista_rechaza_credencial_directa(self):

        vista = VistaConfiguracion()
        warning_original = configuracion_view.QMessageBox.warning
        mensajes = []
        configuracion_view.QMessageBox.warning = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.campo_email_host.setText("smtp.example.test")
            vista.campo_email_remitente.setText("planificador@example.test")
            vista.campo_email_destinatarios.setText("ana@example.test")
            vista.campo_email_credenciales.setText("valor-directo")
            vista.guardar_configuracion_email()

        finally:

            configuracion_view.QMessageBox.warning = warning_original
            vista.close()
            self.app.processEvents()

        datos = IntegracionesRepository().obtener_configuracion("email")

        self.assertTrue(mensajes)
        self.assertEqual(datos[4] or "", "")


if __name__ == "__main__":

    unittest.main()
