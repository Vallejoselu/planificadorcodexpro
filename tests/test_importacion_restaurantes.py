import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
import views.restaurantes as restaurantes_view
from database.database import (
    crear_base_datos,
    insertar_ciudad,
    insertar_restaurante,
    obtener_ciudades,
    obtener_historial_acciones,
    obtener_restaurantes
)
from services.importacion_restaurantes import ImportadorRestaurantes
from views.restaurantes import VistaRestaurantes


class TestImportacionRestaurantes(unittest.TestCase):

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

    def test_importar_restaurantes_csv_crea_registros_y_ciudades(self):

        ruta = Path(self.temporal.name) / "restaurantes.csv"
        ruta.write_text(
            "\n".join([
                "nombre;ciudad;zona;direccion;telefono;prioridad",
                "BK Centro;Santiago;Centro;Rua 1;981111111;70",
                "BK Norte;A Coruna;Norte;Rua 2;981222222;60"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorRestaurantes().importar(ruta)
        restaurantes = obtener_restaurantes()
        ciudades = [ciudad[1] for ciudad in obtener_ciudades()]

        self.assertEqual(resultado["creados"], 2)
        self.assertEqual(resultado["errores"], [])
        self.assertEqual(len(restaurantes), 2)
        self.assertIn("Santiago", ciudades)
        self.assertIn("A Coruna", ciudades)
        self.assertEqual(obtener_historial_acciones()[0][1], "Importar restaurantes")

    def test_importar_restaurantes_excel_actualiza_por_nombre(self):

        from openpyxl import Workbook

        santiago = insertar_ciudad("Santiago")
        insertar_restaurante(
            "BK Centro",
            "Direccion antigua",
            "Centro",
            "111",
            50,
            ciudad_id=santiago
        )
        ruta = Path(self.temporal.name) / "restaurantes.xlsx"
        libro = Workbook()
        hoja = libro.active
        hoja.append(["Nombre", "Ciudad", "Zona", "Direccion", "Telefono"])
        hoja.append(["BK Centro", "Ourense", "Sur", "Direccion nueva", "222"])
        libro.save(ruta)

        resultado = ImportadorRestaurantes().importar(ruta)
        restaurante = obtener_restaurantes()[0]

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(resultado["creados"], 0)
        self.assertEqual(restaurante[2], "Direccion nueva")
        self.assertEqual(restaurante[3], "Sur")
        self.assertEqual(restaurante[4], "222")
        self.assertEqual(restaurante[10], "Ourense")

    def test_importar_restaurantes_informa_filas_invalidas(self):

        ruta = Path(self.temporal.name) / "restaurantes.csv"
        ruta.write_text(
            "\n".join([
                "nombre,ciudad,prioridad",
                ",Santiago,50",
                "BK Norte,Santiago,no",
                "BK Sur,Santiago,40"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorRestaurantes().importar(ruta)

        self.assertEqual(resultado["creados"], 1)
        self.assertEqual(len(resultado["errores"]), 2)
        self.assertEqual(obtener_restaurantes()[0][1], "BK Sur")

    def test_importar_restaurantes_actualizacion_parcial_conserva_datos(self):

        ciudad = insertar_ciudad("Santiago")
        insertar_restaurante(
            "BK Centro",
            "Rua Antigua",
            "Centro",
            "111",
            50,
            activo=1,
            horario_comida="12:00-16:00",
            horario_cena="20:00-00:00",
            ciudad_id=ciudad
        )
        ruta = Path(self.temporal.name) / "restaurantes.csv"
        ruta.write_text(
            "nombre;telefono\nBK Centro;222\n",
            encoding="utf-8"
        )

        resultado = ImportadorRestaurantes().importar(ruta)
        restaurante = obtener_restaurantes()[0]

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(restaurante[2], "Rua Antigua")
        self.assertEqual(restaurante[3], "Centro")
        self.assertEqual(restaurante[4], "222")
        self.assertEqual(restaurante[7], "12:00-16:00")
        self.assertEqual(restaurante[8], "20:00-00:00")
        self.assertEqual(restaurante[10], "Santiago")

    def test_vista_restaurantes_expone_boton_importar(self):

        vista = VistaRestaurantes()

        self.assertEqual(vista.btn_importar.text(), "Importar")

    def test_vista_importa_y_muestra_resumen(self):

        ruta = Path(self.temporal.name) / "restaurantes.csv"
        ruta.write_text(
            "nombre;ciudad\nBK Centro;Santiago\n",
            encoding="utf-8"
        )
        archivo_original = restaurantes_view.QFileDialog.getOpenFileName
        info_original = restaurantes_view.QMessageBox.information
        mensajes = []

        restaurantes_view.QFileDialog.getOpenFileName = (
            lambda *args, **kwargs: (str(ruta), "")
        )
        restaurantes_view.QMessageBox.information = (
            lambda *args, **kwargs: mensajes.append(args)
        )

        try:

            vista = VistaRestaurantes()
            vista.importar_restaurantes()

        finally:

            restaurantes_view.QFileDialog.getOpenFileName = archivo_original
            restaurantes_view.QMessageBox.information = info_original

        self.assertEqual(len(obtener_restaurantes()), 1)
        self.assertTrue(mensajes)


if __name__ == "__main__":

    unittest.main()
