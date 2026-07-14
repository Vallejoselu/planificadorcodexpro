import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QAbstractItemView

import database.database as database
from database.database import crear_base_datos
from services.reglas_configurables import ReglasConfigurablesService
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

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_servicio_expone_reglas_en_modo_lectura(self):

        servicio = ReglasConfigurablesService()
        reglas = servicio.listar_reglas()
        resumen = servicio.resumen()

        self.assertGreaterEqual(len(reglas), 8)
        self.assertEqual(resumen["modo"], "lectura")
        self.assertEqual(resumen["editables"], 0)
        self.assertTrue(
            any(regla["clave"] == "descanso_consecutivo" for regla in reglas)
        )
        self.assertTrue(
            any(regla["clave"] == "prioridad_demanda" for regla in reglas)
        )

    def test_vista_muestra_catalogo_sin_edicion(self):

        vista = VistaReglas()

        self.assertEqual(vista.tabla.rowCount(), 10)
        self.assertIn("Modo lectura", vista.resumen.text())
        self.assertEqual(
            vista.tabla.editTriggers(),
            QAbstractItemView.NoEditTriggers
        )

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


if __name__ == "__main__":

    unittest.main()
