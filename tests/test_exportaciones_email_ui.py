import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

import database.database as database
from database.database import crear_base_datos, guardar_integracion_api
import views.exportaciones as exportaciones_view
from views.exportaciones import VistaExportaciones


class TestExportacionesEmailUi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        guardar_integracion_api(
            "email",
            "Email",
            activo=1,
            base_url="smtp.example.test",
            credenciales_referencia="local://email/principal",
            opciones=json.dumps({
                "smtp_host": "smtp.example.test",
                "smtp_puerto": 2525,
                "smtp_tls": True,
                "remitente": "planificador@example.test",
                "destinatarios": "ana@example.test"
            })
        )

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_exporta_borrador_email_desde_vista(self):

        vista = VistaExportaciones()
        salida = Path(self.temporal.name) / "resumen.eml"
        dialogo_original = exportaciones_view.QFileDialog.getSaveFileName
        info_original = exportaciones_view.QMessageBox.information
        mensajes = []
        exportaciones_view.QFileDialog.getSaveFileName = (
            lambda *args, **kwargs: (str(salida), "Email (*.eml)")
        )
        exportaciones_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.exportar_email_eml()

        finally:

            exportaciones_view.QFileDialog.getSaveFileName = dialogo_original
            exportaciones_view.QMessageBox.information = info_original
            vista.close()
            self.app.processEvents()

        self.assertTrue(salida.exists())
        self.assertIn(
            "To: ana@example.test",
            salida.read_text(encoding="utf-8")
        )
        self.assertTrue(mensajes)

    def test_enviar_email_pide_confirmacion_y_delega_en_servicio(self):

        vista = VistaExportaciones()
        question_original = exportaciones_view.QMessageBox.question
        info_original = exportaciones_view.QMessageBox.information
        enviar_original = exportaciones_view.enviar_resumen_email_configurado
        llamadas = []
        exportaciones_view.QMessageBox.question = (
            lambda *args, **kwargs: QMessageBox.Yes
        )
        exportaciones_view.QMessageBox.information = (
            lambda *args, **kwargs: llamadas.append(("info", args))
        )
        exportaciones_view.enviar_resumen_email_configurado = (
            lambda fecha: {
                "enviado": True,
                "destinatarios": ["ana@example.test"],
                "asunto": f"Cuadrante semanal {fecha}"
            }
        )

        try:

            vista.enviar_email()

        finally:

            exportaciones_view.QMessageBox.question = question_original
            exportaciones_view.QMessageBox.information = info_original
            exportaciones_view.enviar_resumen_email_configurado = enviar_original
            vista.close()
            self.app.processEvents()

        self.assertTrue(llamadas)


if __name__ == "__main__":

    unittest.main()
