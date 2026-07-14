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
    obtener_repartidores
)
from services.importacion_ausencias import ImportadorAusencias
from views.repartidores import VistaRepartidores


class TestImportacionAusencias(unittest.TestCase):

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

    def crear_repartidor(self, nombre):

        return insertar_repartidor(
            nombre,
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50
        )

    def obtener_repartidor_planificacion(self, repartidor_id):

        for repartidor in obtener_repartidores():

            if repartidor[0] == repartidor_id:

                return repartidor

        return None

    def test_importar_ausencias_csv_crea_vacaciones_y_bajas(self):

        ana_id = self.crear_repartidor("Ana")
        luis_id = self.crear_repartidor("Luis")
        ruta = Path(self.temporal.name) / "ausencias.csv"
        ruta.write_text(
            "\n".join([
                "nombre;tipo;fecha_inicio;fecha_fin;observaciones",
                "Ana;vacaciones;15/07/2026;20/07/2026;Verano",
                "Luis;baja;2026-07-21;;Medica"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorAusencias().importar(ruta)
        ana = self.obtener_repartidor_planificacion(ana_id)
        luis = self.obtener_repartidor_planificacion(luis_id)

        self.assertEqual(resultado["vacaciones"], 1)
        self.assertEqual(resultado["bajas"], 1)
        self.assertEqual(resultado["errores"], [])
        self.assertEqual(ana[12][0]["fecha_inicio"], "2026-07-15")
        self.assertEqual(ana[12][0]["fecha_fin"], "2026-07-20")
        self.assertEqual(luis[13][0]["fecha_inicio"], "2026-07-21")
        self.assertIsNone(luis[13][0]["fecha_fin"])
        self.assertEqual(
            obtener_historial_acciones()[0][1],
            "Importar vacaciones y bajas"
        )

    def test_importar_ausencias_excel(self):

        from openpyxl import Workbook

        ana_id = self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "ausencias.xlsx"
        libro = Workbook()
        hoja = libro.active
        hoja.append(["Nombre", "Tipo", "Inicio", "Fin"])
        hoja.append(["Ana", "Vacaciones", "2026-08-01", "2026-08-03"])
        libro.save(ruta)

        resultado = ImportadorAusencias().importar(ruta)
        ana = self.obtener_repartidor_planificacion(ana_id)

        self.assertEqual(resultado["vacaciones"], 1)
        self.assertEqual(ana[12][0]["fecha_inicio"], "2026-08-01")
        self.assertEqual(ana[12][0]["fecha_fin"], "2026-08-03")

    def test_importar_ausencias_no_duplica_registros_exactos(self):

        ana_id = self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "ausencias.csv"
        ruta.write_text(
            "\n".join([
                "nombre,tipo,fecha_inicio,fecha_fin",
                "Ana,vacaciones,2026-07-15,2026-07-15",
                "Ana,vacaciones,2026-07-15,2026-07-15"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorAusencias().importar(ruta)
        ana = self.obtener_repartidor_planificacion(ana_id)

        self.assertEqual(resultado["vacaciones"], 1)
        self.assertEqual(resultado["duplicados"], 1)
        self.assertEqual(len(ana[12]), 1)

    def test_importar_ausencias_informa_errores(self):

        self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "ausencias.csv"
        ruta.write_text(
            "\n".join([
                "nombre,tipo,fecha_inicio,fecha_fin",
                ",vacaciones,2026-07-15,2026-07-16",
                "Luis,vacaciones,2026-07-15,2026-07-16",
                "Ana,permiso,2026-07-15,2026-07-16",
                "Ana,vacaciones,no,2026-07-16",
                "Ana,vacaciones,2026-07-20,2026-07-16",
                "Ana,baja,2026-07-21,"
            ]),
            encoding="utf-8"
        )

        resultado = ImportadorAusencias().importar(ruta)

        self.assertEqual(resultado["bajas"], 1)
        self.assertEqual(len(resultado["errores"]), 5)

    def test_vista_repartidores_expone_boton_importar_ausencias(self):

        vista = VistaRepartidores()

        self.assertEqual(
            vista.btn_importar_ausencias.text(),
            "Importar ausencias"
        )

    def test_vista_importa_ausencias_y_muestra_resumen(self):

        self.crear_repartidor("Ana")
        ruta = Path(self.temporal.name) / "ausencias.csv"
        ruta.write_text(
            "nombre;tipo;fecha_inicio\nAna;vacaciones;2026-07-15\n",
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
            vista.importar_ausencias()

        finally:

            repartidores_view.QFileDialog.getOpenFileName = archivo_original
            repartidores_view.QMessageBox.information = info_original

        self.assertEqual(
            self.obtener_repartidor_planificacion(1)[12][0]["fecha_inicio"],
            "2026-07-15"
        )
        self.assertTrue(mensajes)


if __name__ == "__main__":

    unittest.main()
