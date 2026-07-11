import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import (
    FECHA_INICIO_SEMANA_LEGADO,
    actualizar_repartidor,
    crear_base_datos,
    eliminar_repartidor,
    guardar_turno_calendario,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno,
    obtener_calendario_semanal,
    obtener_repartidor,
    obtener_repartidores,
    obtener_restaurantes,
    obtener_turnos
)
from services.asistente_horarios import responder
from services.exportador import (
    exportar_csv,
    exportar_excel,
    exportar_pdf,
    preparar_datos_exportacion
)
from services.planificador import generar_horarios
from ui.theme_manager import ThemeManager
from views.ventana_principal import VentanaPrincipal
from views.repartidores import VistaRepartidores
from views.cuadrantes import VistaCuadrantes


class TestAuditoriaFlujoCompleto(unittest.TestCase):

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
        ThemeManager.set_theme("light")

    def test_flujo_operativo_temporal_no_contamina_base_real(self):

        insertar_repartidor(
            "Ana",
            10,
            "Ronda",
            1,
            1,
            80,
            50,
            20,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={
                "lunes": "No disponible",
                "martes": "No disponible",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Cenas",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        )
        insertar_repartidor(
            "Luis",
            20,
            "Ronda",
            1,
            1,
            50,
            80,
            20,
            descanso_inicio="martes",
            descanso_fin="miercoles",
            disponibilidad={
                "lunes": "Ambos",
                "martes": "No disponible",
                "miercoles": "No disponible",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        )
        insertar_repartidor(
            "Marta",
            30,
            "Grela",
            1,
            1,
            50,
            50,
            90,
            descanso_inicio="jueves",
            descanso_fin="viernes",
            disponibilidad={
                "lunes": "Ambos",
                "martes": "Ambos",
                "miercoles": "Ambos",
                "jueves": "No disponible",
                "viernes": "No disponible",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
        )

        repartidores = obtener_repartidores()
        self.assertEqual(len(repartidores), 3)
        eliminar_repartidor(repartidores[2][0])
        self.assertEqual(len(obtener_repartidores()), 2)

        insertar_restaurante(
            "Ronda Centro",
            "Calle Real 1",
            "Ronda",
            "600000001",
            80,
            horario_comida="13:00-16:00",
            horario_cena="20:00-23:30"
        )
        insertar_restaurante(
            "Grela Norte",
            "Poligono 2",
            "Grela",
            "600000002",
            60,
            horario_comida="13:00-16:00",
            horario_cena="20:00-23:30"
        )
        insertar_turno(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        insertar_turno(
            "Cena",
            "Cena",
            "20:00",
            "23:30",
            "#16A34A",
            3.5
        )

        restaurantes = obtener_restaurantes()
        turnos = obtener_turnos()
        comida_id = next(turno[0] for turno in turnos if turno[2] == "Comida")
        cena_id = next(turno[0] for turno in turnos if turno[2] == "Cena")

        guardar_turno_calendario("viernes", cena_id, restaurantes[0][0])
        guardar_turno_calendario("viernes", comida_id, restaurantes[1][0])
        guardar_turno_calendario("viernes", cena_id, restaurantes[1][0])

        calendario = obtener_calendario_semanal()
        self.assertEqual(len(calendario), 3)

        resultado = generar_horarios(
            obtener_repartidores(),
            restaurantes,
            turnos=[{
                "nombre": "comida",
                "horas": 3,
                "hora_inicio": "13:00",
                "hora_fin": "16:00"
            }, {
                "nombre": "noche",
                "horas": 3.5,
                "hora_inicio": "20:00",
                "hora_fin": "23:30"
            }]
        )

        for resumen in resultado["resumen"]:
            self.assertLessEqual(
                resumen["horas"],
                resumen["maximo"]
            )
            self.assertNotIn("sabado", resumen["descanso"])
            self.assertNotIn("domingo", resumen["descanso"])

        for dia, turnos_dia in resultado["horario"].items():
            for nombre_turno, asignaciones in turnos_dia.items():
                ids = [
                    asignacion["repartidor_id"]
                    for asignacion in asignaciones
                ]
                self.assertEqual(len(ids), len(set(ids)))
                for asignacion in asignaciones:
                    descanso = next(
                        item["descanso"]
                        for item in resultado["resumen"]
                        if item["id"] == asignacion["repartidor_id"]
                    )
                    self.assertNotIn(dia, descanso, nombre_turno)

        respuesta_sin_cubrir = responder("Que turnos estan sin cubrir?")
        self.assertIn("Turnos sin cubrir", respuesta_sin_cubrir)

        respuesta_candidatos = responder(
            "Quien puede cubrir la cena del viernes?"
        )
        self.assertIn("puede cubrir", respuesta_candidatos)

        conteos_antes = self._conteos_tablas()
        respuesta_simulacion = responder(
            "Que ocurre si Ana esta de vacaciones el viernes?"
        )
        self.assertIn("Simulacion", respuesta_simulacion)
        self.assertEqual(conteos_antes, self._conteos_tablas())

        carpeta_exportacion = Path(self.temporal.name) / "exportaciones"
        carpeta_exportacion.mkdir()
        ruta_csv = carpeta_exportacion / "horario.csv"
        ruta_excel = carpeta_exportacion / "horario.xlsx"
        ruta_pdf = carpeta_exportacion / "horario.pdf"

        exportar_csv(ruta_csv)
        exportar_excel(ruta_excel)
        exportar_pdf(str(ruta_pdf))

        self.assertGreater(ruta_csv.stat().st_size, 0)
        self.assertGreater(ruta_excel.stat().st_size, 0)
        self.assertGreater(ruta_pdf.stat().st_size, 0)

        ventana = VentanaPrincipal()
        for pagina in ventana.paginas:
            ventana.mostrar_pagina(pagina)

        ThemeManager.set_theme("dark")
        self.assertEqual(ThemeManager.current_theme(), "dark")
        ThemeManager.set_theme("light")
        self.assertEqual(ThemeManager.current_theme(), "light")

        crear_base_datos()
        self.assertEqual(len(obtener_repartidores()), 2)
        self.assertEqual(len(obtener_restaurantes()), 2)
        self.assertEqual(len(obtener_turnos()), 2)

    def test_calendario_guarda_varios_restaurantes_mismo_dia_turno(self):

        insertar_restaurante("R1", "", "Ronda", "", 50)
        insertar_restaurante("R2", "", "Ronda", "", 50)
        insertar_turno("Cena", "Cena", "20:00", "23:30", "#16A34A", 3.5)

        restaurantes = obtener_restaurantes()
        turno_id = obtener_turnos()[0][0]

        guardar_turno_calendario("viernes", turno_id, restaurantes[0][0])
        guardar_turno_calendario("viernes", turno_id, restaurantes[1][0])
        guardar_turno_calendario("viernes", turno_id, restaurantes[0][0])

        calendario = obtener_calendario_semanal()

        self.assertEqual(len(calendario), 2)
        self.assertEqual(
            {asignacion[6] for asignacion in calendario},
            {restaurantes[0][0], restaurantes[1][0]}
        )

        vista = VistaCuadrantes()
        vista.selector_semana.setDate(
            QDate.fromString(
                FECHA_INICIO_SEMANA_LEGADO,
                "yyyy-MM-dd"
            )
        )
        clave = ("viernes", turno_id)

        self.assertEqual(len(vista.asignaciones[clave]), 2)
        fila = vista.fila_turno(turno_id)
        columna = database.DIAS_SEMANA.index("viernes")
        texto = vista.tabla.item(fila, columna).text()

        self.assertIn("R1", texto)
        self.assertIn("R2", texto)

    def test_calendario_persiste_repartidor_y_asistente_calcula_horas(self):

        repartidor_id = insertar_repartidor(
            "Ana",
            10,
            "Ronda",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={"viernes": "Ambos"}
        )
        insertar_restaurante("R1", "", "Ronda", "", 50)
        insertar_turno("Cena", "Cena", "20:00", "23:30", "#16A34A", 3.5)

        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]
        guardar_turno_calendario(
            "viernes",
            turno_id,
            restaurante_id,
            repartidor_id
        )

        asignacion = obtener_calendario_semanal()[0]
        self.assertEqual(asignacion[9], repartidor_id)

        respuesta = responder("Quien lleva menos horas esta semana?")

        self.assertIn("3.5", respuesta)
        self.assertNotIn("calendario actual no guarda repartidor", respuesta)

    def test_exportacion_filtra_por_semana(self):

        insertar_restaurante("R1", "", "Ronda", "", 50)
        insertar_restaurante("R2", "", "Ronda", "", 50)
        insertar_turno("Cena", "Cena", "20:00", "23:30", "#16A34A", 3.5)

        restaurantes = obtener_restaurantes()
        turno_id = obtener_turnos()[0][0]
        guardar_turno_calendario(
            "lunes",
            turno_id,
            restaurantes[0][0],
            fecha_inicio_semana="2026-07-13"
        )
        guardar_turno_calendario(
            "lunes",
            turno_id,
            restaurantes[1][0],
            fecha_inicio_semana="2026-07-20"
        )

        semana_a = preparar_datos_exportacion("2026-07-13")
        semana_b = preparar_datos_exportacion("2026-07-20")

        self.assertEqual(semana_a["horarios"][0][3], "R1")
        self.assertEqual(semana_b["horarios"][0][3], "R2")

    def test_repartidor_se_puede_editar_y_desactivar(self):

        repartidor_id = insertar_repartidor(
            "Ana",
            10,
            "Ronda",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={"viernes": "Ambos"}
        )

        actualizar_repartidor(
            repartidor_id,
            "Ana Editada",
            20,
            "Grela",
            0,
            1,
            40,
            60,
            70,
            "Actualizada",
            descanso_inicio="martes",
            descanso_fin="miercoles",
            disponibilidad={"viernes": "Cenas"}
        )

        repartidor = obtener_repartidor(repartidor_id)

        self.assertEqual(repartidor["nombre"], "Ana Editada")
        self.assertEqual(repartidor["horas"], 20)
        self.assertEqual(repartidor["descanso_inicio"], "martes")
        self.assertEqual(repartidor["disponibilidad"]["viernes"], ["noche"])

        vista = VistaRepartidores()
        self.assertTrue(hasattr(vista, "btn_editar"))
        self.assertTrue(hasattr(vista, "btn_eliminar"))

        eliminar_repartidor(repartidor_id)

        self.assertEqual(obtener_repartidores(), [])

    def _conteos_tablas(self):

        conexion = database.conectar()
        cursor = conexion.cursor()
        tablas = [
            fila[0]
            for fila in cursor.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type=? AND name NOT LIKE ?",
                ("table", "sqlite_%")
            )
        ]
        conteos = {
            tabla: cursor.execute(
                "SELECT COUNT(*) FROM " + tabla
            ).fetchone()[0]
            for tabla in tablas
        }
        conexion.close()

        return conteos


if __name__ == "__main__":

    unittest.main()
