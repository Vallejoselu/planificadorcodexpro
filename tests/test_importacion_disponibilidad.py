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
    obtener_repartidor
)
from services.importacion_disponibilidad import ImportadorDisponibilidad
from views.repartidores import VistaRepartidores


class TestImportacionDisponibilidad(unittest.TestCase):

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

    def crear_repartidor(self, nombre, disponibilidad=None):

        return insertar_repartidor(
            nombre,
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            disponibilidad=disponibilidad
        )

    def test_importar_disponibilidad_csv_semanal(self):

        ana_id = self.crear_repartidor("Ana")
        self.crear_repartidor("Luis")
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "\n".join([
                "nombre;lunes;martes;miercoles",
                "Ana;Comidas;No disponible;Ambos",
                "Luis;Cenas;Comidas;No"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorDisponibilidad().importar(ruta)
        ana = obtener_repartidor(ana_id)

        self.assertEqual(resultado["actualizados"], 2)
        self.assertEqual(resultado["errores"], [])
        self.assertEqual(ana["disponibilidad"]["lunes"], ["comida"])
        self.assertEqual(ana["disponibilidad"]["martes"], [])
        self.assertEqual(ana["disponibilidad"]["miercoles"], ["comida", "noche"])
        self.assertEqual(obtener_historial_acciones()[0][1], "Importar disponibilidad")

    def test_importar_disponibilidad_excel(self):

        from openpyxl import Workbook

        ana_id = self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "disponibilidad.xlsx"
        libro = Workbook()
        hoja = libro.active
        hoja.append(["Nombre", "Lunes", "Martes"])
        hoja.append(["Ana", "Cenas", "Comidas"])
        libro.save(ruta)

        resultado = ImportadorDisponibilidad().importar(ruta)
        ana = obtener_repartidor(ana_id)

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(ana["disponibilidad"]["lunes"], ["noche"])
        self.assertEqual(ana["disponibilidad"]["martes"], ["comida"])

    def test_importar_disponibilidad_larga_conserva_dias_no_incluidos(self):

        ana_id = self.crear_repartidor(
            "Ana",
            disponibilidad={
                "lunes": "Cenas",
                "martes": "Comidas"
            }
        )
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "\n".join([
                "nombre,dia,disponibilidad",
                "Ana,lunes,No disponible"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorDisponibilidad().importar(ruta)
        ana = obtener_repartidor(ana_id)

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(ana["disponibilidad"]["lunes"], [])
        self.assertEqual(ana["disponibilidad"]["martes"], ["comida"])

    def test_importar_disponibilidad_semanal_ignora_celdas_vacias(self):

        ana_id = self.crear_repartidor(
            "Ana",
            disponibilidad={
                "lunes": "Cenas",
                "martes": "Comidas"
            }
        )
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "nombre,lunes,martes\nAna,,No disponible\n",
            encoding="utf-8"
        )

        ImportadorDisponibilidad().importar(ruta)
        ana = obtener_repartidor(ana_id)

        self.assertEqual(ana["disponibilidad"]["lunes"], ["noche"])
        self.assertEqual(ana["disponibilidad"]["martes"], [])

    def test_importar_disponibilidad_informa_errores(self):

        self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "\n".join([
                "nombre,dia,disponibilidad",
                ",lunes,Comidas",
                "Luis,lunes,Comidas",
                "Ana,fiesta,Comidas",
                "Ana,lunes,Media tarde",
                "Ana,martes,Cenas"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorDisponibilidad().importar(ruta)

        self.assertEqual(resultado["actualizados"], 1)
        self.assertEqual(len(resultado["errores"]), 4)

    def test_importar_disponibilidad_por_turno_y_disponible(self):

        ana_id = self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "\n".join([
                "nombre,dia,turno,disponible",
                "Ana,lunes,noche,si",
                "Ana,martes,comida,no"
            ]),
            encoding="utf-8"
        )

        ImportadorDisponibilidad().importar(ruta)
        ana = obtener_repartidor(ana_id)

        self.assertEqual(ana["disponibilidad"]["lunes"], ["noche"])
        self.assertEqual(ana["disponibilidad"]["martes"], [])

    def test_vista_repartidores_expone_boton_importar_disponibilidad(self):

        vista = VistaRepartidores()

        self.assertEqual(
            vista.btn_importar_disponibilidad.text(),
            "Importar disponibilidad"
        )

    def test_vista_importa_disponibilidad_y_muestra_resumen(self):

        self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "disponibilidad.csv"
        ruta.write_text(
            "nombre;lunes\nAna;Comidas\n",
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
            vista.importar_disponibilidad()

        finally:

            repartidores_view.QFileDialog.getOpenFileName = archivo_original
            repartidores_view.QMessageBox.information = info_original

        self.assertEqual(
            obtener_repartidor(1)["disponibilidad"]["lunes"],
            ["comida"]
        )
        self.assertTrue(mensajes)


if __name__ == "__main__":

    unittest.main()
