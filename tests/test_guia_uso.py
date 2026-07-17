import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QScrollArea

import database.database as database
from database.database import crear_base_datos
from views.guia_uso import VistaGuiaUso
from views.ventana_principal import VentanaPrincipal


class TestGuiaUso(unittest.TestCase):

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

    def test_guia_tiene_secciones_operativas(self):

        vista = VistaGuiaUso()

        self.assertGreaterEqual(len(vista.SECCIONES), 10)
        textos = " ".join(
            texto
            for _, texto in vista.SECCIONES
        )
        self.assertIn("Empezar de cero", textos)
        self.assertIn("Sin repartidor", textos)
        self.assertIn("demanda", textos.lower())
        self.assertTrue(vista.findChildren(QScrollArea))

    def test_ventana_principal_incluye_guia(self):

        ventana = VentanaPrincipal()

        self.assertIn("guia_uso", ventana.paginas)
        self.assertIn("guia_uso", ventana.botones)
        self.assertEqual(ventana.botones["guia_uso"].text(), "Guia de uso")


if __name__ == "__main__":

    unittest.main()
