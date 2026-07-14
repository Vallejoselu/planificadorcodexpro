import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import crear_base_datos
from views.ventana_principal import VentanaPrincipal


class TestSmokeAplicacion(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def test_ventana_principal_carga_vistas_esenciales(self):

        original = database.RUTA_BD

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"

            try:

                crear_base_datos()
                ventana = VentanaPrincipal()

                for pagina in (
                    "inicio",
                    "repartidores",
                    "ciudades",
                    "restaurantes",
                    "turnos",
                    "cuadrantes",
                    "asistente",
                    "reglas",
                    "estadisticas",
                    "exportar",
                    "configuracion"
                ):

                    self.assertIn(pagina, ventana.paginas)
                    ventana.mostrar_pagina(pagina)

                ventana.close()
                self.app.processEvents()

            finally:

                database.RUTA_BD = original


if __name__ == "__main__":

    unittest.main()
