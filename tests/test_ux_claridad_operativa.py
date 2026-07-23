import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLabel, QScrollArea

import database.database as database
import views.cuadrantes as cuadrantes_view
from database.database import crear_base_datos
from views.cuadrantes import VistaCuadrantes
from views.configuracion import VistaConfiguracion
from views.inicio import VistaInicio
from views.puesta_marcha import VistaPuestaMarcha
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
        self.assertEqual(
            cuadrantes.btn_comprobar.text(),
            "Comprobar configuracion"
        )
        self.assertEqual(cuadrantes.selector_vista.currentData(), "empleado")
        self.assertIn("Sin repartidor", cuadrantes.leyenda_cuadrante.text())
        self.assertIn("plaza pendiente", cuadrantes.leyenda_cuadrante.text())

    def test_inicio_muestra_guia_operativa(self):

        vista = VistaInicio()

        self.assertTrue(hasattr(vista, "guia_operativa"))
        self.assertIn("Antes de generar", vista.guia_operativa.text())
        self.assertTrue(vista.estado_detalle.wordWrap())
        self.assertLessEqual(len(vista.pendientes_labels), 5)
        self.assertEqual(vista.btn_accion_principal.text(), "Resolver Restaurantes")
        self.assertEqual(vista.btn_comprobar.text(), "Comprobar configuracion")

    def test_configuracion_usa_scroll_para_no_aplastar_paneles(self):

        vista = VistaConfiguracion()
        scrolls = vista.findChildren(QScrollArea)

        self.assertTrue(scrolls)
        self.assertTrue(hasattr(vista, "scroll"))
        self.assertTrue(vista.scroll.widgetResizable())
        titulo = vista.panel_datos_locales.findChild(QLabel).text().lower()
        self.assertIn("datos locales", titulo)

    def test_configuracion_oculta_avanzado_por_defecto(self):

        vista = VistaConfiguracion()

        self.assertFalse(vista.selector_modo_avanzado.isChecked())
        self.assertTrue(vista.panel_email.isHidden())
        self.assertTrue(vista.panel_delivery_generico.isHidden())
        self.assertTrue(vista.panel_demanda_zona.isHidden())
        self.assertTrue(vista.tabla_integraciones.isHidden())

        vista.selector_modo_avanzado.setChecked(True)

        self.assertFalse(vista.panel_email.isHidden())
        self.assertFalse(vista.panel_delivery_generico.isHidden())
        self.assertFalse(vista.panel_demanda_zona.isHidden())
        self.assertFalse(vista.tabla_integraciones.isHidden())

    def test_puesta_marcha_explica_reinicio_limpio(self):

        vista = VistaPuestaMarcha()

        self.assertIn("checklist", vista.guia.text().lower())
        self.assertEqual(vista.resumen.objectName(), "infoPanel")
        self.assertEqual(vista.btn_empezar_cero.text(), "Empezar de cero")
        self.assertEqual(vista.btn_empezar_cero.property("variant"), "danger")

    def test_colores_cuadrante_tienen_contraste_en_empleados_y_alertas(self):

        vista = VistaCuadrantes()

        self.assertEqual(vista.color_celda_empleado("libre"), "#FCA5A5")
        self.assertEqual(
            vista.color_texto_celda_empleado("libre"),
            "#450A0A"
        )
        self.assertEqual(vista.color_celda_empleado("disponible"), "#E5E7EB")
        self.assertEqual(
            vista.color_texto_celda_empleado("disponible"),
            "#374151"
        )

    def test_cuadrantes_usa_paneles_adaptados_al_tema(self):

        vista = VistaCuadrantes()

        self.assertEqual(vista.guia_operativa.objectName(), "infoPanel")
        self.assertEqual(vista.leyenda_cuadrante.objectName(), "infoPanel")
        self.assertEqual(vista.aviso_modo_simple.objectName(), "infoPanel")
        self.assertEqual(vista.tabla_alertas.maximumHeight(), 150)

    def test_cuadrantes_oculta_herramientas_avanzadas_por_defecto(self):

        vista = VistaCuadrantes()

        self.assertFalse(vista.selector_modo_avanzado.isChecked())
        self.assertTrue(vista.barra_acciones_scroll.isHidden())
        self.assertTrue(vista.detalle_seleccion.isHidden())
        self.assertFalse(vista.aviso_modo_simple.isHidden())

        vista.selector_modo_avanzado.setChecked(True)

        self.assertFalse(vista.barra_acciones_scroll.isHidden())
        self.assertFalse(vista.detalle_seleccion.isHidden())
        self.assertTrue(vista.aviso_modo_simple.isHidden())

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

    def test_comprobar_configuracion_muestra_resultado_previo(self):

        avisos = []
        info_original = cuadrantes_view.QMessageBox.information
        cuadrantes_view.QMessageBox.information = (
            lambda *args, **kwargs: avisos.append(args)
        )

        try:

            vista = VistaCuadrantes()
            vista.comprobar_configuracion()

        finally:

            cuadrantes_view.QMessageBox.information = info_original

        self.assertEqual(len(avisos), 1)
        self.assertEqual(avisos[0][1], "Configuracion incompleta")
        self.assertIn("Comprobacion previa", avisos[0][2])
        self.assertIn("No hay repartidores activos", avisos[0][2])


if __name__ == "__main__":

    unittest.main()
