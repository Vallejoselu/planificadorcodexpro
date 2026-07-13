import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import views.nuevo_restaurante as nuevo_restaurante_view
from views.nuevo_restaurante import NuevoRestaurante


class FakeCiudadesRepository:

    def listar_activas(self):

        return [(1, "Santiago", 1)]


class FakeRepartidoresRepository:

    def listar_activos(self):

        return []


class FakeRestaurantesRepository:

    def listar_turnos(self, restaurante_id):

        return []

    def listar_demanda(self, restaurante_id):

        return []


class TestDemandaRestauranteUI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ciudades_original = nuevo_restaurante_view.ciudades_repository
        self.repartidores_original = (
            nuevo_restaurante_view.repartidores_repository
        )
        self.restaurantes_original = (
            nuevo_restaurante_view.restaurantes_repository
        )
        self.warning_original = nuevo_restaurante_view.QMessageBox.warning
        self.advertencias = []
        nuevo_restaurante_view.ciudades_repository = FakeCiudadesRepository()
        nuevo_restaurante_view.repartidores_repository = (
            FakeRepartidoresRepository()
        )
        nuevo_restaurante_view.restaurantes_repository = (
            FakeRestaurantesRepository()
        )
        nuevo_restaurante_view.QMessageBox.warning = self.capturar_warning

    def tearDown(self):

        nuevo_restaurante_view.ciudades_repository = self.ciudades_original
        nuevo_restaurante_view.repartidores_repository = (
            self.repartidores_original
        )
        nuevo_restaurante_view.restaurantes_repository = (
            self.restaurantes_original
        )
        nuevo_restaurante_view.QMessageBox.warning = self.warning_original

    def capturar_warning(self, parent, titulo, texto):

        self.advertencias.append((titulo, texto))

    def crear_dialogo_con_turno(self):

        dialogo = NuevoRestaurante()
        dialogo.turnos_propios = [{
            "id": 10,
            "nombre": "Cena",
            "hora_inicio": "20:00",
            "hora_fin": "23:30",
            "cruza_medianoche": 0,
            "duracion": 3.5,
            "activo": 1
        }]
        dialogo.refrescar_turnos()

        return dialogo

    def test_demanda_restaurante_turno_permite_cero_repartidores(self):

        dialogo = self.crear_dialogo_con_turno()
        dialogo.demanda_dia.setCurrentText("lunes")
        dialogo.demanda_repartidores.setValue(0)

        dialogo.agregar_demanda()

        self.assertEqual(dialogo.demandas[0]["repartidores_necesarios"], 0)

    def test_demanda_restaurante_turno_rechaza_periodo_invalido_y_duplicado(self):

        dialogo = self.crear_dialogo_con_turno()

        dialogo.agregar_demanda()
        self.assertEqual(len(dialogo.demandas), 0)
        self.assertIn("fecha concreta o un dia", self.advertencias[-1][1])

        dialogo.demanda_dia.setCurrentText("lunes")
        dialogo.agregar_demanda()
        dialogo.agregar_demanda()

        self.assertEqual(len(dialogo.demandas), 1)
        self.assertIn("Ya existe una demanda", self.advertencias[-1][1])

    def test_demanda_restaurante_turno_elimina_fila_seleccionada(self):

        dialogo = self.crear_dialogo_con_turno()
        dialogo.demanda_dia.setCurrentText("lunes")
        dialogo.agregar_demanda()
        dialogo.demanda_dia.setCurrentText("martes")
        dialogo.agregar_demanda()

        dialogo.tabla_demanda.selectRow(0)
        dialogo.eliminar_demanda()

        self.assertEqual(len(dialogo.demandas), 1)
        self.assertEqual(dialogo.demandas[0]["dia_semana"], "martes")


if __name__ == "__main__":

    unittest.main()
