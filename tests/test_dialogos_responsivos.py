import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit, QScrollArea

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
        self.assertIsInstance(dialogo.zona, QLineEdit)
        self.assertFalse(dialogo.selector_avanzado.isChecked())
        self.assertTrue(dialogo.bloque_avanzado.isHidden())
        self.assertIn("San Lazaro", dialogo.zona.placeholderText())
        dialogo.zona.setText("Fonsillon")
        self.assertEqual(dialogo.zona.text(), "Fonsillon")

    def test_dialogo_repartidor_muestra_y_valida_opciones_avanzadas(self):

        dialogo = NuevoRepartidor()

        dialogo.selector_avanzado.setChecked(True)
        dialogo.tipo_cobertura.setCurrentIndex(
            dialogo.tipo_cobertura.findData("solo_valle")
        )
        dialogo.hora_inicio_minima.setText("12:00")
        dialogo.hora_fin_maxima.setText("23:30")

        self.assertFalse(dialogo.bloque_avanzado.isHidden())
        self.assertEqual(dialogo.tipo_cobertura.currentData(), "solo_valle")
        dialogo.validar_restricciones_avanzadas()

        dialogo.hora_fin_maxima.setText("25:00")

        with self.assertRaises(ValueError):

            dialogo.validar_restricciones_avanzadas()

    def test_dialogo_restaurante_tiene_scroll_y_alto_limitado(self):

        dialogo = NuevoRestaurante()

        self.assert_dialogo_adaptado_a_pantalla(dialogo)
        self.assertEqual(dialogo.seccion_basica.title(), "Datos basicos")
        self.assertEqual(
            dialogo.seccion_planificacion.title(),
            "Turnos y demanda"
        )
        self.assertTrue(dialogo.seccion_avanzada.isHidden())
        self.assertFalse(dialogo.selector_avanzado.isChecked())
        self.assertEqual(
            dialogo.btn_configuracion_recomendada.text(),
            "Crear configuracion recomendada"
        )
        self.assertIsInstance(dialogo.zona, QLineEdit)
        self.assertIn("Santiago Centro", dialogo.zona.placeholderText())
        dialogo.zona.setText("San Lazaro")
        self.assertEqual(dialogo.zona.text(), "San Lazaro")

    def test_dialogo_restaurante_crea_configuracion_recomendada(self):

        dialogo = NuevoRestaurante()

        self.assertEqual(len(dialogo.turnos_propios), 2)
        self.assertEqual(len(dialogo.demandas), 14)
        self.assertEqual(dialogo.horario_comida.text(), "13:00 - 16:00")
        self.assertEqual(dialogo.horario_cena.text(), "20:00 - 23:30")

        dialogo.aplicar_configuracion_recomendada(silencioso=True)

        self.assertEqual(len(dialogo.turnos_propios), 2)
        self.assertEqual(len(dialogo.demandas), 14)

    def test_dialogo_restaurante_agrega_horas_valle_configurables(self):

        dialogo = NuevoRestaurante()

        dialogo.horario_valle.setText("16:00 - 20:00")
        dialogo.demanda_valle.setValue(2)

        resultado = dialogo.agregar_horas_valle(silencioso=True)

        self.assertEqual(resultado["turnos"], 1)
        self.assertEqual(resultado["demandas"], 7)
        self.assertEqual(len(dialogo.turnos_propios), 3)
        valle = dialogo.turnos_propios[-1]
        self.assertEqual(valle["nombre"], "Valle")
        self.assertEqual(valle["hora_inicio"], "16:00")
        self.assertEqual(valle["hora_fin"], "20:00")
        self.assertEqual(valle["duracion"], 4)
        self.assertTrue(all(
            demanda["repartidores_necesarios"] == 2
            for demanda in dialogo.demandas
            if demanda.get("indice_turno") == 2
        ))

        resultado = dialogo.agregar_horas_valle(silencioso=True)

        self.assertEqual(resultado["turnos"], 0)
        self.assertEqual(resultado["demandas"], 0)
        self.assertEqual(len(dialogo.turnos_propios), 3)
        self.assertEqual(len(dialogo.demandas), 21)

    def test_dialogo_restaurante_horas_valle_aceptan_madrugada(self):

        dialogo = NuevoRestaurante()

        dialogo.horario_valle.setText("00:30 - 04:30")

        dialogo.agregar_horas_valle(silencioso=True)

        valle = dialogo.turnos_propios[-1]
        self.assertEqual(valle["hora_inicio"], "00:30")
        self.assertEqual(valle["hora_fin"], "04:30")
        self.assertEqual(valle["cruza_medianoche"], 0)
        self.assertEqual(valle["duracion"], 4)

    def test_dialogo_restaurante_horas_valle_pueden_cruzar_medianoche(self):

        dialogo = NuevoRestaurante()

        dialogo.horario_valle.setText("23:30 - 02:30")

        dialogo.agregar_horas_valle(silencioso=True)

        valle = dialogo.turnos_propios[-1]
        self.assertEqual(valle["hora_inicio"], "23:30")
        self.assertEqual(valle["hora_fin"], "02:30")
        self.assertEqual(valle["cruza_medianoche"], 1)
        self.assertEqual(valle["duracion"], 3)

    def test_dialogo_restaurante_muestra_avanzado_solo_si_se_pide(self):

        dialogo = NuevoRestaurante()

        dialogo.selector_avanzado.setChecked(True)

        self.assertFalse(dialogo.seccion_avanzada.isHidden())

    def test_dialogo_restaurante_valida_nombre_turnos_y_demanda(self):

        dialogo = NuevoRestaurante()

        self.assertIn("nombre", dialogo.validar_formulario())

        dialogo.nombre.setText("Burger Centro")
        dialogo.turnos_propios = []
        dialogo.demandas = []

        self.assertIn("turno", dialogo.validar_formulario())

        dialogo.aplicar_configuracion_recomendada(silencioso=True)

        self.assertIsNone(dialogo.validar_formulario())
