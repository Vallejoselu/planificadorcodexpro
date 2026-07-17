import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QScrollArea

from views.guia_uso import VistaGuiaUso
from views.ventana_principal import VentanaPrincipal


class TestGuiaUso(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

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
