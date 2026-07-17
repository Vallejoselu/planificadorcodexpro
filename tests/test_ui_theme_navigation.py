import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
from ui.theme_manager import ThemeManager
from views.ventana_principal import VentanaPrincipal


class TestUiThemeNavigation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.previous_theme = ThemeManager.current_theme()
        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        ThemeManager.set_theme(self.previous_theme)
        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_carga_tema_claro(self):

        ThemeManager.set_theme("light")

        self.assertEqual(ThemeManager.current_theme(), "light")
        self.assertIn("#F4F7FB", self.app.styleSheet())

    def test_carga_tema_oscuro(self):

        ThemeManager.set_theme("dark")

        self.assertEqual(ThemeManager.current_theme(), "dark")
        self.assertIn("#111827", self.app.styleSheet())

    def test_persistencia_preferencia(self):

        ThemeManager.set_theme("dark")

        self.assertEqual(ThemeManager.current_theme(), "dark")

    def test_paginas_stack(self):

        ventana = VentanaPrincipal()

        self.assertEqual(ventana.stack.count(), 12)
        self.assertIn("inicio", ventana.paginas)
        self.assertIn("puesta_marcha", ventana.paginas)
        self.assertIn("ciudades", ventana.paginas)
        self.assertIn("reglas", ventana.paginas)
        self.assertIn("configuracion", ventana.paginas)

    def test_cambio_pagina_desde_menu(self):

        ventana = VentanaPrincipal()
        ventana.mostrar_pagina("turnos")

        self.assertIs(
            ventana.stack.currentWidget(),
            ventana.paginas["turnos"]
        )
        self.assertTrue(ventana.botones["turnos"].isChecked())

    def test_exclusividad_botones_menu(self):

        ventana = VentanaPrincipal()
        ventana.mostrar_pagina("repartidores")
        ventana.mostrar_pagina("restaurantes")

        activos = [
            boton
            for boton in ventana.botones.values()
            if boton.isChecked()
        ]

        self.assertEqual(len(activos), 1)
        self.assertTrue(ventana.botones["restaurantes"].isChecked())


if __name__ == "__main__":

    unittest.main()
