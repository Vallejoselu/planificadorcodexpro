import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
import views.cuadrantes as cuadrantes_view
from database.database import crear_base_datos
from views.cuadrantes import VistaCuadrantes
from views.inicio import VistaInicio
from views.restaurantes import VistaRestaurantes
from views.turnos import VistaTurnos


class TestUxClaridadOperativa(unittest.TestCase):

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

    def test_botones_describen_acciones_reales(self):

        restaurantes = VistaRestaurantes()
        turnos = VistaTurnos()
        cuadrantes = VistaCuadrantes()

        self.assertEqual(restaurantes.btn_eliminar.text(), "Desactivar")
        self.assertIn("No borra", restaurantes.btn_eliminar.toolTip())
        self.assertEqual(turnos.btn_eliminar.text(), "Desactivar")
        self.assertIn("No borra", turnos.btn_eliminar.toolTip())
        self.assertEqual(
            cuadrantes.btn_eliminar.text(),
            "Quitar asignacion"
        )
        self.assertIn("No elimina", cuadrantes.btn_eliminar.toolTip())

    def test_inicio_muestra_guia_operativa(self):

        vista = VistaInicio()

        self.assertTrue(hasattr(vista, "guia_operativa"))
        self.assertIn("Antes de generar", vista.guia_operativa.text())
        self.assertIn("crear repartidores", vista.guia_operativa.text())

    def test_cuadrantes_avisa_si_quitar_sin_celda(self):

        avisos = []
        warning_original = cuadrantes_view.QMessageBox.warning
        cuadrantes_view.QMessageBox.warning = (
            lambda *args, **kwargs: avisos.append(args)
        )

        try:

            vista = VistaCuadrantes()
            vista.tabla.clearSelection()
            vista.eliminar()

        finally:

            cuadrantes_view.QMessageBox.warning = warning_original

        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0][1], "Quitar asignacion")
        self.assertIn("Selecciona una celda", avisos[0][2])
        self.assertIn("no elimina restaurantes", avisos[0][2].lower())


if __name__ == "__main__":

    unittest.main()
