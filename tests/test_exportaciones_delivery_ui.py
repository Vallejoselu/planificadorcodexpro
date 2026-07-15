import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
import views.exportaciones as exportaciones_view
from views.exportaciones import VistaExportaciones


class TestExportacionesDeliveryUi(unittest.TestCase):

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

    def test_exporta_delivery_json_desde_vista(self):

        vista = VistaExportaciones()
        salida = Path(self.temporal.name) / "delivery.json"
        dialogo_original = exportaciones_view.QFileDialog.getSaveFileName
        info_original = exportaciones_view.QMessageBox.information
        mensajes = []
        exportaciones_view.QFileDialog.getSaveFileName = (
            lambda *args, **kwargs: (str(salida), "JSON (*.json)")
        )
        exportaciones_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista.exportar_delivery_json()

        finally:

            exportaciones_view.QFileDialog.getSaveFileName = dialogo_original
            exportaciones_view.QMessageBox.information = info_original
            vista.close()
            self.app.processEvents()

        payload = json.loads(salida.read_text(encoding="utf-8"))

        self.assertEqual(payload["schema"], "planificador.delivery.v1")
        self.assertEqual(payload["turnos"], [])
        self.assertTrue(mensajes)


if __name__ == "__main__":

    unittest.main()
