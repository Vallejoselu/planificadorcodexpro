import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

import database.database as database
import views.cuadrantes as cuadrantes_view
from database.database import (
    FECHA_INICIO_SEMANA_LEGADO,
    crear_base_datos,
    guardar_turno_calendario,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno,
    listar_semanas_calendario,
    obtener_calendario_semanal,
    obtener_restaurantes,
    obtener_turnos,
    reemplazar_calendario_semana,
    semana_tiene_calendario
)
from views.cuadrantes import VistaCuadrantes


class TestCuadrantesPlanningEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        self._crear_datos()
        self.information_original = cuadrantes_view.QMessageBox.information
        cuadrantes_view.QMessageBox.information = lambda *args, **kwargs: None

    def tearDown(self):

        cuadrantes_view.QMessageBox.information = self.information_original
        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_boton_generar_cuadrante_existe_en_la_vista(self):

        vista = VistaCuadrantes()

        self.assertEqual(
            vista.btn_generar.text(),
            "Generar cuadrante"
        )
        self.assertTrue(hasattr(vista, "selector_semana"))

    def test_cancelar_generacion_no_modifica_ninguna_semana(self):

        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 13))
        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True
        vista.generar_cuadrante()
        firma_semana_a = self._firma("2026-07-13")

        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.mostrar_resumen_generacion = lambda resultado: False
        vista.generar_cuadrante()

        self.assertEqual(self._firma("2026-07-13"), firma_semana_a)
        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])

    def test_dos_semanas_distintas_persisten_y_se_muestran_separadas(self):

        vista = VistaCuadrantes()
        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True

        vista.selector_semana.setDate(QDate(2026, 7, 13))
        vista.generar_cuadrante()
        firma_semana_a = self._firma("2026-07-13")

        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.generar_cuadrante()
        firma_semana_b = self._firma("2026-07-20")

        self.assertTrue(firma_semana_a)
        self.assertTrue(firma_semana_b)
        self.assertNotEqual(firma_semana_a, firma_semana_b)
        self.assertEqual(
            set(listar_semanas_calendario()),
            {"2026-07-13", "2026-07-20"}
        )

        vista.selector_semana.setDate(QDate(2026, 7, 13))
        self.assertEqual(self._firma_vista(vista), firma_semana_a)
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        self.assertEqual(self._firma_vista(vista), firma_semana_b)

    def test_sobrescribir_una_semana_no_modifica_otra(self):

        vista = VistaCuadrantes()
        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True

        vista.selector_semana.setDate(QDate(2026, 7, 13))
        vista.generar_cuadrante()
        firma_semana_a = self._firma("2026-07-13")

        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.generar_cuadrante()

        reemplazar_calendario_semana(
            "2026-07-20",
            {
                (
                    "lunes",
                    obtener_turnos()[0][0]
                ): [{
                    "restaurante_id": obtener_restaurantes()[0][0],
                    "repartidor_id": None
                }]
            }
        )

        self.assertEqual(self._firma("2026-07-13"), firma_semana_a)
        self.assertEqual(len(obtener_calendario_semanal("2026-07-20")), 1)

    def test_mismos_turnos_pueden_existir_en_semanas_distintas_sin_duplicar(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]

        guardar_turno_calendario(
            "viernes",
            turno_id,
            restaurante_id,
            None,
            "2026-07-13"
        )
        guardar_turno_calendario(
            "viernes",
            turno_id,
            restaurante_id,
            None,
            "2026-07-20"
        )
        guardar_turno_calendario(
            "viernes",
            turno_id,
            restaurante_id,
            None,
            "2026-07-20"
        )

        self.assertEqual(len(obtener_calendario_semanal("2026-07-13")), 1)
        self.assertEqual(len(obtener_calendario_semanal("2026-07-20")), 1)
        self.assertTrue(semana_tiene_calendario("2026-07-13"))
        self.assertTrue(semana_tiene_calendario("2026-07-20"))

    def test_actualizar_mantiene_la_semana_seleccionada(self):

        vista = VistaCuadrantes()
        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.generar_cuadrante()

        vista.cargar_datos()

        self.assertEqual(vista.fecha_inicio_semana(), "2026-07-20")
        self.assertEqual(
            self._firma_vista(vista),
            self._firma("2026-07-20")
        )

    def test_vista_por_local_muestra_asignaciones_de_la_semana(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno = obtener_turnos()[0]
        turno_id = turno[0]
        guardar_turno_calendario(
            "viernes",
            turno_id,
            restaurante_id,
            None,
            "2026-07-20"
        )
        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.selector_vista.setCurrentText("Por local")

        self.assertTrue(vista.tabla.isHidden())
        self.assertFalse(vista.tabla_locales.isHidden())
        self.assertEqual(
            vista.tabla_locales.item(0, 0).text(),
            "Ronda Centro"
        )
        self.assertIn(
            turno[2],
            vista.tabla_locales.item(
                0,
                database.DIAS_SEMANA.index("viernes") + 1
            ).text()
        )

    def test_deshacer_y_rehacer_no_afectan_otras_semanas(self):

        vista = VistaCuadrantes()
        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True

        vista.selector_semana.setDate(QDate(2026, 7, 13))
        vista.generar_cuadrante()
        firma_semana_a = self._firma("2026-07-13")

        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.generar_cuadrante()
        clave = next(iter(vista.asignaciones))
        vista.tabla.setCurrentCell(
            vista.fila_turno(clave[1]),
            database.DIAS_SEMANA.index(clave[0])
        )
        vista.eliminar()
        firma_semana_b_editada = self._firma("2026-07-20")
        vista.undo_stack.undo()
        firma_semana_b_rehecha = self._firma("2026-07-20")
        vista.undo_stack.redo()

        self.assertEqual(self._firma("2026-07-13"), firma_semana_a)
        self.assertNotEqual(firma_semana_b_editada, firma_semana_b_rehecha)
        self.assertEqual(self._firma("2026-07-20"), firma_semana_b_editada)

    def test_resultado_contiene_resumen_para_dialogo(self):

        vista = VistaCuadrantes()
        resultado, asignaciones = vista.generar_resultado_cuadrante()
        texto = vista.texto_resumen_generacion(resultado)

        self.assertIn("Repartidores asignados", texto)
        self.assertIn("Turnos cubiertos", texto)
        self.assertIn("Turnos sin cubrir", texto)
        self.assertIn("Incidencias", texto)
        self.assertIn("Horas totales", texto)
        self.assertTrue(asignaciones)

    def test_migracion_conserva_registros_antiguos_y_es_idempotente(self):

        database.RUTA_BD = Path(self.temporal.name) / "legacy.db"
        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.executescript("""
        CREATE TABLE turnos(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            nombre TEXT NOT NULL,
            hora_inicio TEXT NOT NULL,
            hora_fin TEXT NOT NULL,
            color TEXT NOT NULL,
            duracion REAL NOT NULL,
            activo INTEGER DEFAULT 1
        );
        CREATE TABLE restaurantes(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            direccion TEXT,
            zona TEXT,
            telefono TEXT,
            prioridad INTEGER DEFAULT 50,
            activo INTEGER DEFAULT 1,
            observaciones TEXT
        );
        CREATE TABLE calendario_semanal(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            turno_id INTEGER NOT NULL,
            restaurante_id INTEGER NOT NULL,
            repartidor_id INTEGER
        );
        INSERT INTO turnos(tipo,nombre,hora_inicio,hora_fin,color,duracion)
        VALUES('Cena','Cena','20:00','23:30','#16A34A',3.5);
        INSERT INTO restaurantes(nombre,zona) VALUES('R1','Ronda');
        INSERT INTO calendario_semanal(dia,turno_id,restaurante_id)
        VALUES('viernes',1,1);
        """)
        conexion.commit()
        conexion.close()

        crear_base_datos()
        crear_base_datos()

        calendario = obtener_calendario_semanal()
        self.assertEqual(len(calendario), 1)
        self.assertEqual(calendario[0][11], FECHA_INICIO_SEMANA_LEGADO)

    def test_reemplazo_de_semana_revierte_si_falla(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]
        asignaciones = {
            ("lunes", turno_id): [{
                "restaurante_id": restaurante_id,
                "repartidor_id": None
            }]
        }
        reemplazar_calendario_semana("2026-07-13", asignaciones)
        firma_original = self._firma("2026-07-13")

        with self.assertRaises(KeyError):

            reemplazar_calendario_semana(
                "2026-07-13",
                {
                    ("martes", turno_id): [{
                        "repartidor_id": None
                    }]
                }
            )

        self.assertEqual(self._firma("2026-07-13"), firma_original)

    def test_las_pruebas_usan_base_temporal(self):

        self.assertIn(
            self.temporal.name,
            str(database.RUTA_BD)
        )

    def _firma(self, semana):

        return sorted(
            (
                asignacion[1],
                asignacion[2],
                asignacion[6],
                asignacion[9]
            )
            for asignacion in obtener_calendario_semanal(semana)
        )

    def _firma_vista(self, vista):

        return sorted(
            (
                dia,
                turno_id,
                asignacion["restaurante_id"],
                asignacion["repartidor_id"]
            )
            for (dia, turno_id), asignaciones in vista.asignaciones.items()
            for asignacion in asignaciones
        )

    def _crear_datos(self):

        disponibilidad_total = {
            "lunes": "Ambos",
            "martes": "Ambos",
            "miercoles": "Ambos",
            "jueves": "Ambos",
            "viernes": "Ambos",
            "sabado": "Ambos",
            "domingo": "Ambos"
        }

        ana_id = insertar_repartidor(
            "Ana",
            40,
            "Ronda",
            1,
            1,
            80,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad=disponibilidad_total
        )
        insertar_repartidor(
            "Luis",
            40,
            "Ronda",
            1,
            1,
            50,
            80,
            50,
            descanso_inicio="miercoles",
            descanso_fin="jueves",
            disponibilidad=disponibilidad_total
        )
        insertar_repartidor(
            "Marta",
            40,
            "Ronda",
            1,
            1,
            60,
            60,
            50,
            descanso_inicio="jueves",
            descanso_fin="viernes",
            disponibilidad=disponibilidad_total
        )
        insertar_restaurante(
            "Ronda Centro",
            "Calle Real 1",
            "Ronda",
            "600000001",
            80,
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

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute("""
        INSERT INTO vacaciones(
            repartidor_id,
            fecha_inicio,
            fecha_fin,
            activo
        )
        VALUES(?,?,?,1)
        """,(
            ana_id,
            "2026-07-13",
            "2026-07-19"
        ))
        conexion.commit()
        conexion.close()


if __name__ == "__main__":

    unittest.main()
