import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import (
    crear_base_datos,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno,
    obtener_calendario_semanal,
    obtener_repartidores,
    obtener_restaurantes,
    obtener_turnos
)
from services.asistente_horarios import responder
from services.cuadrantes_service import CuadrantesService
from services.exportador import exportar_csv, exportar_excel, exportar_ics, exportar_pdf
from ui.theme_manager import ThemeManager
from views.ventana_principal import VentanaPrincipal


class TestValidacionFuncionalCompleta(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        ThemeManager.set_theme("light")

    def tearDown(self):

        ThemeManager.set_theme("light")
        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_checklist_funcional_completo_como_usuario(self):

        semana_actual = "2026-07-13"
        semana_siguiente = "2026-07-20"

        repartidores = self.crear_repartidores()
        restaurantes = self.crear_restaurantes()
        turnos = self.crear_turnos()

        self.assertEqual(len(obtener_repartidores()), 3)
        self.assertEqual(len(obtener_restaurantes()), 2)
        self.assertEqual(len(obtener_turnos()), 2)

        servicio = CuadrantesService()
        generacion = servicio.generar_cuadrante(
            servicio.obtener_contexto(),
            semana_actual
        )
        servicio.guardar_cuadrante(
            semana_actual,
            generacion["asignaciones"]
        )

        calendario_generado = obtener_calendario_semanal(semana_actual)
        self.assertTrue(calendario_generado)

        comida_id = turnos["comida"]
        servicio.guardar_asignacion_turno(
            semana_actual,
            "viernes",
            comida_id,
            [{
                "restaurante_id": restaurantes["centro"],
                "repartidor_id": repartidores["ana"]
            }]
        )
        calendario_editado = obtener_calendario_semanal(semana_actual)
        self.assertTrue(
            any(
                asignacion[1] == "viernes"
                and asignacion[2] == comida_id
                and asignacion[6] == restaurantes["centro"]
                and asignacion[9] == repartidores["ana"]
                for asignacion in calendario_editado
            )
        )

        servicio.guardar_asignacion_turno(
            semana_siguiente,
            "lunes",
            comida_id,
            [{
                "restaurante_id": restaurantes["norte"],
                "repartidor_id": repartidores["luis"]
            }]
        )

        self.assertTrue(obtener_calendario_semanal(semana_siguiente))
        self.assertNotEqual(
            self.firma_calendario(semana_actual),
            self.firma_calendario(semana_siguiente)
        )
        self.assertTrue(obtener_calendario_semanal(semana_actual))

        carpeta_exportacion = Path(self.temporal.name) / "exportaciones"
        carpeta_exportacion.mkdir()
        ruta_excel = carpeta_exportacion / "cuadrante.xlsx"
        ruta_pdf = carpeta_exportacion / "cuadrante.pdf"
        ruta_csv = carpeta_exportacion / "cuadrante.csv"
        ruta_ics = carpeta_exportacion / "cuadrante.ics"

        exportar_excel(ruta_excel, semana_actual)
        exportar_pdf(str(ruta_pdf), semana_actual)
        exportar_csv(ruta_csv, semana_actual)
        exportar_ics(ruta_ics, semana_actual)

        for ruta in (ruta_excel, ruta_pdf, ruta_csv, ruta_ics):

            self.assertTrue(ruta.exists())
            self.assertGreater(ruta.stat().st_size, 0)

        respuesta_asistente = responder(
            "Quien puede cubrir la comida del viernes?"
        )
        self.assertIn("puede cubrir", respuesta_asistente)

        ThemeManager.set_theme("dark")
        self.assertEqual(ThemeManager.current_theme(), "dark")
        self.assertEqual(QApplication.instance().property("theme"), "dark")
        ThemeManager.set_theme("light")
        self.assertEqual(ThemeManager.current_theme(), "light")

        firma_antes_reinicio = self.firma_calendario(semana_actual)

        ventana = VentanaPrincipal()
        for pagina in ventana.paginas:

            ventana.mostrar_pagina(pagina)

        ventana.close()
        crear_base_datos()
        ventana_reiniciada = VentanaPrincipal()
        ventana_reiniciada.mostrar_pagina("cuadrantes")

        self.assertEqual(len(obtener_repartidores()), 3)
        self.assertEqual(len(obtener_restaurantes()), 2)
        self.assertEqual(len(obtener_turnos()), 2)
        self.assertEqual(
            firma_antes_reinicio,
            self.firma_calendario(semana_actual)
        )
        ventana_reiniciada.close()

    def test_generar_cuadrante_crea_turnos_base_si_no_existen(self):

        semana = "2026-07-13"
        insertar_repartidor(
            "Ana",
            40,
            "Centro",
            1,
            1,
            80,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={
                "lunes": "No disponible",
                "martes": "No disponible",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        )
        insertar_restaurante(
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000001",
            80,
            horario_comida="13:00-16:00",
            horario_cena="20:00-23:30"
        )
        self.assertEqual(obtener_turnos(), [])

        servicio = CuadrantesService()
        generacion = servicio.generar_cuadrante(
            servicio.obtener_contexto(),
            semana
        )
        servicio.guardar_cuadrante(
            semana,
            generacion["asignaciones"]
        )

        nombres_turnos = {turno[2] for turno in obtener_turnos()}

        self.assertIn("Comida", nombres_turnos)
        self.assertIn("Cena", nombres_turnos)
        self.assertTrue(obtener_calendario_semanal(semana))

    def crear_repartidores(self):

        disponibilidad_total = {
            "lunes": "Ambos",
            "martes": "Ambos",
            "miercoles": "Ambos",
            "jueves": "Ambos",
            "viernes": "Ambos",
            "sabado": "Ambos",
            "domingo": "Ambos"
        }

        return {
            "ana": insertar_repartidor(
                "Ana",
                40,
                "Centro",
                1,
                1,
                80,
                50,
                50,
                descanso_inicio="lunes",
                descanso_fin="martes",
                disponibilidad=disponibilidad_total
            ),
            "luis": insertar_repartidor(
                "Luis",
                40,
                "Centro",
                1,
                1,
                50,
                80,
                50,
                descanso_inicio="martes",
                descanso_fin="miercoles",
                disponibilidad=disponibilidad_total
            ),
            "marta": insertar_repartidor(
                "Marta",
                40,
                "Norte",
                1,
                1,
                50,
                50,
                80,
                descanso_inicio="jueves",
                descanso_fin="viernes",
                disponibilidad=disponibilidad_total
            )
        }

    def crear_restaurantes(self):

        return {
            "centro": insertar_restaurante(
                "BK Centro",
                "Rua 1",
                "Centro",
                "600000001",
                80,
                horario_comida="13:00-16:00",
                horario_cena="20:00-23:30"
            ),
            "norte": insertar_restaurante(
                "BK Norte",
                "Rua 2",
                "Norte",
                "600000002",
                60,
                horario_comida="13:00-16:00",
                horario_cena="20:00-23:30"
            )
        }

    def crear_turnos(self):

        return {
            "comida": insertar_turno(
                "Comida",
                "Comida",
                "13:00",
                "16:00",
                "#2563EB",
                3
            ),
            "cena": insertar_turno(
                "Cena",
                "Cena",
                "20:00",
                "23:30",
                "#16A34A",
                3.5
            )
        }

    def firma_calendario(self, semana):

        return sorted(
            (
                asignacion[1],
                asignacion[2],
                asignacion[6],
                asignacion[9]
            )
            for asignacion in obtener_calendario_semanal(semana)
        )


if __name__ == "__main__":

    unittest.main()
