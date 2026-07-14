import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
import views.repartidores as repartidores_view
from database.database import (
    crear_base_datos,
    insertar_repartidor,
    obtener_historial_acciones,
    obtener_repartidor,
    obtener_repartidores
)
from services.importacion_repartidores import ImportadorRepartidores
from views.repartidores import VistaRepartidores


class TestImportacionRepartidores(unittest.TestCase):

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

    def test_importar_repartidores_csv_crea_registros(self):

        ruta = Path(self.temporal.name) / "repartidores.csv"
        ruta.write_text(
            "\n".join([
                "nombre;horas;zona;doble turno;puede hasta la una",
                "Ana;30;Centro;si;no",
                "Luis;20;Norte;no;si"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorRepartidores().importar(ruta)
        repartidores = obtener_repartidores()

        self.assertEqual(resultado["creados"], 2)
        self.assertEqual(resultado["errores"], [])
        self.assertEqual(len(repartidores), 2)
        self.assertEqual(repartidores[0][1], "Ana")
        self.assertEqual(repartidores[0][5], 0)
        self.assertEqual(obtener_historial_acciones()[0][1], "Importar repartidores")

    def test_importar_repartidores_excel_actualiza_por_nombre(self):

        from openpyxl import Workbook

        repartidor_id = insertar_repartidor(
            "Ana",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50
        )
        ruta = Path(self.temporal.name) / "repartidores.xlsx"
        libro = Workbook()
        hoja = libro.active
        hoja.append(["Nombre", "Horas", "Zona", "Horas complementarias"])
        hoja.append(["Ana", 20, "Sur", 5])
        libro.save(ruta)

        resultado = ImportadorRepartidores().importar(ruta)
        repartidor = obtener_repartidor(repartidor_id)

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(resultado["creados"], 0)
        self.assertEqual(repartidor["horas"], 20)
        self.assertEqual(repartidor["zona"], "Sur")
        self.assertEqual(repartidor["horas_complementarias"], 5)

    def test_importar_repartidores_informa_filas_invalidas(self):

        ruta = Path(self.temporal.name) / "repartidores.csv"
        ruta.write_text(
            "\n".join([
                "nombre,horas,zona",
                ",30,Centro",
                "Luis,99,Norte",
                "Marta,20,Sur"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorRepartidores().importar(ruta)

        self.assertEqual(resultado["creados"], 1)
        self.assertEqual(len(resultado["errores"]), 2)
        self.assertEqual(obtener_repartidores()[0][1], "Marta")

    def test_vista_repartidores_expone_boton_importar(self):

        vista = VistaRepartidores()

        self.assertEqual(vista.btn_importar.text(), "Importar")

    def test_vista_importa_y_muestra_resumen(self):

        ruta = Path(self.temporal.name) / "repartidores.csv"
        ruta.write_text(
            "nombre;horas\nAna;30\n",
            encoding="utf-8"
        )
        archivo_original = repartidores_view.QFileDialog.getOpenFileName
        info_original = repartidores_view.QMessageBox.information
        mensajes = []

        repartidores_view.QFileDialog.getOpenFileName = (
            lambda *args, **kwargs: (str(ruta), "")
        )
        repartidores_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista = VistaRepartidores()
            vista.importar_repartidores()

        finally:

            repartidores_view.QFileDialog.getOpenFileName = archivo_original
            repartidores_view.QMessageBox.information = info_original

        self.assertEqual(len(obtener_repartidores()), 1)
        self.assertTrue(mensajes)


if __name__ == "__main__":

    unittest.main()
