import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QScrollArea

import views.nuevo_repartidor as nuevo_repartidor_view
import views.nuevo_restaurante as nuevo_restaurante_view
from views.nuevo_repartidor import NuevoRepartidor
from views.nuevo_restaurante import NuevoRestaurante


class FakeCiudadesRepository:

    def listar_activas(self):

        return [(1, "Santiago", 1), (2, "A Coruna", 1)]


class FakeRepartidoresRepository:

    def listar_activos(self):

        return [(1, "Ana"), (2, "Luis")]


class FakeRestaurantesRepository:

    def listar_activos(self):

        return [(1, "BK Santiago Centro"), (2, "BK Ourense")]

    def listar_turnos(self, restaurante_id):

        return []

    def listar_demanda(self, restaurante_id):

        return []


class TestDialogosResponsivos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.repartidor_ciudades_original = (
            nuevo_repartidor_view.ciudades_repository
        )
        self.repartidor_restaurantes_original = (
            nuevo_repartidor_view.restaurantes_repository
        )
        self.restaurante_ciudades_original = (
            nuevo_restaurante_view.ciudades_repository
        )
        self.restaurante_repartidores_original = (
            nuevo_restaurante_view.repartidores_repository
        )
        self.restaurante_restaurantes_original = (
            nuevo_restaurante_view.restaurantes_repository
        )

        nuevo_repartidor_view.ciudades_repository = FakeCiudadesRepository()
        nuevo_repartidor_view.restaurantes_repository = (
            FakeRestaurantesRepository()
        )
        nuevo_restaurante_view.ciudades_repository = FakeCiudadesRepository()
        nuevo_restaurante_view.repartidores_repository = (
            FakeRepartidoresRepository()
        )
        nuevo_restaurante_view.restaurantes_repository = (
            FakeRestaurantesRepository()
        )

    def tearDown(self):

        nuevo_repartidor_view.ciudades_repository = (
            self.repartidor_ciudades_original
        )
        nuevo_repartidor_view.restaurantes_repository = (
            self.repartidor_restaurantes_original
        )
        nuevo_restaurante_view.ciudades_repository = (
            self.restaurante_ciudades_original
        )
        nuevo_restaurante_view.repartidores_repository = (
            self.restaurante_repartidores_original
        )
        nuevo_restaurante_view.restaurantes_repository = (
            self.restaurante_restaurantes_original
        )

    def assert_dialogo_adaptado_a_pantalla(self, dialogo):

        scrolls = dialogo.findChildren(QScrollArea)
        self.assertGreaterEqual(len(scrolls), 1)
        self.assertTrue(scrolls[0].widgetResizable())
        self.assertLess(dialogo.maximumHeight(), 16777215)
        self.assertLessEqual(dialogo.height(), dialogo.maximumHeight())

    def test_dialogo_repartidor_tiene_scroll_y_alto_limitado(self):

        dialogo = NuevoRepartidor()

        self.assert_dialogo_adaptado_a_pantalla(dialogo)
        self.assertEqual(dialogo.seccion_basica.title(), "Datos basicos")
        self.assertEqual(
            dialogo.seccion_disponibilidad.title(),
            "Disponibilidad semanal"
        )
        self.assertFalse(dialogo.selector_avanzado.isChecked())
        self.assertTrue(dialogo.seccion_avanzada.isHidden())
        self.assertEqual(
            dialogo.btn_configuracion_recomendada.text(),
            "Aplicar configuracion recomendada"
        )

    def test_dialogo_repartidor_muestra_avanzado_solo_si_se_pide(self):

        dialogo = NuevoRepartidor()

        dialogo.selector_avanzado.setChecked(True)

        self.assertFalse(dialogo.seccion_avanzada.isHidden())

    def test_dialogo_repartidor_aplica_configuracion_recomendada(self):

        dialogo = NuevoRepartidor()

        dialogo.horas.setCurrentText("10")
        dialogo.permite_horas_complementarias.setChecked(True)
        dialogo.horas_complementarias.setValue(4)
        dialogo.max_horas_diarias.setValue(6)
        dialogo.btn_configuracion_recomendada.click()

        self.assertEqual(dialogo.horas.currentText(), "30")
        self.assertFalse(dialogo.permite_horas_complementarias.isChecked())
        self.assertEqual(dialogo.horas_complementarias.value(), 0)
        self.assertEqual(dialogo.max_horas_diarias.value(), 10)
        self.assertEqual(dialogo.descanso_inicio.currentText(), "lunes")

    def test_dialogo_repartidor_valida_destino_para_generador(self):

        dialogo = NuevoRepartidor()
        dialogo.nombre.setText("Ana")

        self.assertIn("Asigna una ciudad", dialogo.validar_formulario())

        dialogo.apoyo_flexible.setChecked(True)

        self.assertIsNone(dialogo.validar_formulario())

    def test_dialogo_restaurante_tiene_scroll_y_alto_limitado(self):

        dialogo = NuevoRestaurante()

        self.assert_dialogo_adaptado_a_pantalla(dialogo)
