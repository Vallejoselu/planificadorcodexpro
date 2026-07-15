import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication, QScrollArea

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
from services.cuadrantes_service import CuadrantesService
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
        self.assertEqual(vista.btn_copiar_semana.text(), "Copiar semana")
        self.assertEqual(
            vista.btn_guardar_plantilla.text(),
            "Guardar plantilla"
        )
        self.assertEqual(
            vista.btn_aplicar_plantilla.text(),
            "Aplicar plantilla"
        )

    def test_barras_superiores_no_comprimen_controles(self):

        vista = VistaCuadrantes()
        barras = vista.findChildren(QScrollArea)

        self.assertIn(vista.barra_filtros_scroll, barras)
        self.assertIn(vista.barra_acciones_scroll, barras)
        self.assertGreaterEqual(len(barras), 2)
        self.assertGreater(
            vista.barra_acciones_widget.minimumWidth(),
            vista.barra_acciones_scroll.width()
        )
        self.assertGreaterEqual(
            vista.btn_generar.minimumWidth(),
            vista.btn_generar.sizeHint().width()
        )
        self.assertGreaterEqual(
            vista.btn_guardar_plantilla.minimumWidth(),
            vista.btn_guardar_plantilla.sizeHint().width()
        )

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

    def test_cuadrante_muestra_horario_real_del_turno(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno = obtener_turnos()[0]
        guardar_turno_calendario(
            "viernes",
            turno[0],
            restaurante_id,
            None,
            "2026-07-20"
        )

        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        item = vista.tabla.item(
            vista.fila_turno(turno[0]),
            database.DIAS_SEMANA.index("viernes")
        )
        horario = f"{turno[3]}-{turno[4]}"

        self.assertIn(horario, item.text())
        self.assertIn(f"{float(turno[6]):g} h", item.text())
        self.assertIn(horario, item.toolTip())

    def test_asignacion_manual_respeta_dias_libres(self):

        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]
        ana_id = self._id_repartidor("Ana")
        avisos = []
        warning_original = cuadrantes_view.QMessageBox.warning
        cuadrantes_view.QMessageBox.warning = (
            lambda *args, **kwargs: avisos.append(
                "\n".join(str(arg) for arg in args)
            ) or None
        )

        try:

            self._seleccionar_combo(vista.selector_restaurante, restaurante_id)
            self._seleccionar_combo(vista.selector_turno, turno_id)
            self._seleccionar_combo(vista.selector_repartidor, ana_id)
            vista.tabla.setCurrentCell(
                vista.fila_turno(turno_id),
                database.DIAS_SEMANA.index("lunes")
            )
            vista.asignar_seleccion()

        finally:

            cuadrantes_view.QMessageBox.warning = warning_original

        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])
        self.assertTrue(avisos)
        self.assertIn("descanso", avisos[0])

    def test_generador_no_asigna_repartidor_no_disponible(self):

        servicio = CuadrantesService()
        resultado = servicio.generar_cuadrante(
            {
                "ciudades": [],
                "restaurante_turnos": [],
                "demandas_restaurante": [],
                "demandas_zona": [],
                "demandas_ciudad": [],
                "repartidores": [{
                    "id": 1,
                    "nombre": "Pedro",
                    "horas": 40,
                    "zona": "Ronda",
                    "doble_turno": 1,
                    "puede_hasta_la_una": 1,
                    "prioridad_comida": 50,
                    "prioridad_noche": 50,
                    "prioridad_grela": 50,
                    "descanso": ["jueves", "viernes"],
                    "disponibilidad": {
                        "lunes": "Ambos",
                        "martes": "No disponible",
                        "miercoles": "Ambos",
                        "jueves": "No disponible",
                        "viernes": "No disponible",
                        "sabado": "Ambos",
                        "domingo": "Ambos"
                    }
                }],
                "restaurantes": [{
                    "id": 1,
                    "nombre": "Ronda Centro",
                    "zona": "Ronda"
                }],
                "turnos": [(
                    1,
                    "Comida",
                    "Comida",
                    "13:00",
                    "16:00",
                    "#2563EB",
                    3,
                    1
                )]
            },
            "2026-07-20"
        )["resultado"]

        asignados_martes = [
            asignacion.get("repartidor_id")
            for asignacion in resultado["horario"]["martes"]["comida"]
        ]
        self.assertNotIn(1, asignados_martes)

    def test_asignacion_manual_en_no_disponible_se_bloquea(self):

        pedro_id = self._crear_pedro_martes_no_disponible()
        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = self._turno_por_nombre("Comida")[0]
        avisos = []
        warning_original = cuadrantes_view.QMessageBox.warning
        cuadrantes_view.QMessageBox.warning = (
            lambda *args, **kwargs: avisos.append(
                "\n".join(str(arg) for arg in args)
            ) or None
        )

        try:

            self._seleccionar_combo(vista.selector_restaurante, restaurante_id)
            self._seleccionar_combo(vista.selector_turno, turno_id)
            self._seleccionar_combo(vista.selector_repartidor, pedro_id)
            vista.tabla.setCurrentCell(
                vista.fila_turno(turno_id),
                database.DIAS_SEMANA.index("martes")
            )
            vista.asignar_seleccion()

        finally:

            cuadrantes_view.QMessageBox.warning = warning_original

        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])
        self.assertTrue(avisos)
        self.assertIn("disponibilidad", avisos[0])

    def test_servicio_bloquea_guardado_directo_en_dia_no_disponible(self):

        pedro_id = self._crear_pedro_martes_no_disponible()
        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = self._turno_por_nombre("Comida")[0]

        with self.assertRaisesRegex(ValueError, "disponibilidad"):

            CuadrantesService().guardar_asignacion_turno(
                "2026-07-20",
                "martes",
                turno_id,
                [{
                    "restaurante_id": restaurante_id,
                    "repartidor_id": pedro_id
                }]
            )

        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])

    def test_vista_por_empleado_muestra_libre_en_no_disponible(self):

        self._crear_pedro_martes_no_disponible()
        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.selector_vista.setCurrentText("Por empleado")
        fila = self._fila_empleado(vista, "Pedro")
        columna_martes = database.DIAS_SEMANA.index("martes") + 2
        item = vista.tabla_empleados.item(fila, columna_martes)

        self.assertFalse(vista.tabla_empleados.isHidden())
        self.assertEqual(item.text(), "LIBRE")
        self.assertEqual(item.toolTip(), "No disponible")

    def test_vista_por_empleado_muestra_doble_y_horarios(self):

        restaurante_id = obtener_restaurantes()[0][0]
        luis_id = self._id_repartidor("Luis")
        comida = self._turno_por_nombre("Comida")
        cena = self._turno_por_nombre("Cena")
        guardar_turno_calendario(
            "lunes",
            comida[0],
            restaurante_id,
            luis_id,
            "2026-07-20"
        )
        guardar_turno_calendario(
            "lunes",
            cena[0],
            restaurante_id,
            luis_id,
            "2026-07-20"
        )
        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.selector_vista.setCurrentText("Por empleado")
        fila = self._fila_empleado(vista, "Luis")
        item = vista.tabla_empleados.item(
            fila,
            database.DIAS_SEMANA.index("lunes") + 2
        )

        self.assertIn("DOBLE", item.text())
        self.assertIn("COMIDA", item.text())
        self.assertIn("13:00-16:00", item.text())
        self.assertIn("CENA", item.text())
        self.assertIn("20:00-23:30", item.text())

    def test_vista_por_empleado_muestra_comida_y_cena_con_horario(self):

        restaurante_id = obtener_restaurantes()[0][0]
        luis_id = self._id_repartidor("Luis")
        comida = self._turno_por_nombre("Comida")
        cena = self._turno_por_nombre("Cena")
        guardar_turno_calendario(
            "lunes",
            comida[0],
            restaurante_id,
            luis_id,
            "2026-07-20"
        )
        guardar_turno_calendario(
            "martes",
            cena[0],
            restaurante_id,
            luis_id,
            "2026-07-20"
        )
        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 20))
        vista.selector_vista.setCurrentText("Por empleado")
        fila = self._fila_empleado(vista, "Luis")
        lunes = vista.tabla_empleados.item(
            fila,
            database.DIAS_SEMANA.index("lunes") + 2
        )
        martes = vista.tabla_empleados.item(
            fila,
            database.DIAS_SEMANA.index("martes") + 2
        )

        self.assertIn("COMIDA", lunes.text())
        self.assertIn("13:00-16:00", lunes.text())
        self.assertIn("CENA", martes.text())
        self.assertIn("20:00-23:30", martes.text())

    def test_copiar_semana_no_crea_asignaciones_invalidas(self):

        pedro_id = self._crear_pedro_martes_no_disponible()
        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = self._turno_por_nombre("Comida")[0]
        guardar_turno_calendario(
            "martes",
            turno_id,
            restaurante_id,
            pedro_id,
            "2026-07-13"
        )

        with self.assertRaisesRegex(ValueError, "disponibilidad"):

            CuadrantesService().copiar_semana(
                "2026-07-13",
                "2026-07-20"
            )

        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])

    def test_aplicar_plantilla_no_crea_asignaciones_invalidas(self):

        pedro_id = self._crear_pedro_martes_no_disponible()
        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = self._turno_por_nombre("Comida")[0]
        guardar_turno_calendario(
            "martes",
            turno_id,
            restaurante_id,
            pedro_id,
            "2026-07-13"
        )
        servicio = CuadrantesService()
        plantilla_id = servicio.crear_plantilla_desde_semana(
            "2026-07-13",
            "Plantilla invalida antigua",
            incluir_repartidores=True
        )["plantilla_id"]

        with self.assertRaisesRegex(ValueError, "disponibilidad"):

            servicio.aplicar_plantilla(
                plantilla_id,
                "2026-07-20"
            )

        self.assertEqual(obtener_calendario_semanal("2026-07-20"), [])

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
        servicio = CuadrantesService()
        generacion = servicio.generar_cuadrante(
            vista.contexto_cuadrante(),
            vista.fecha_inicio_semana()
        )
        texto = servicio.texto_resumen_generacion(generacion["resultado"])

        self.assertIn("Repartidores asignados", texto)
        self.assertIn("Turnos cubiertos", texto)
        self.assertIn("Turnos sin cubrir", texto)
        self.assertIn("Incidencias", texto)
        self.assertIn("Horas totales", texto)
        self.assertTrue(generacion["asignaciones"])

    def test_copiar_semana_reemplaza_destino_con_confirmacion(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]
        repartidor_id = insertar_repartidor(
            "Luis",
            20,
            "Ronda",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="miercoles",
            descanso_fin="jueves"
        )
        guardar_turno_calendario(
            "lunes",
            turno_id,
            restaurante_id,
            repartidor_id,
            fecha_inicio_semana="2026-07-13"
        )
        guardar_turno_calendario(
            "martes",
            turno_id,
            restaurante_id,
            None,
            fecha_inicio_semana="2026-07-20"
        )
        dialogo_original = cuadrantes_view.DialogoCopiarSemana

        class DialogoFalso:

            def __init__(self, parent, fecha_origen):

                pass

            def exec(self):

                return cuadrantes_view.QDialog.Accepted

            def fecha_origen(self):

                return "2026-07-13"

            def fecha_destino(self):

                return "2026-07-20"

        confirmaciones = []
        cuadrantes_view.DialogoCopiarSemana = DialogoFalso

        try:

            vista = VistaCuadrantes()
            vista.confirmar_sobrescritura_destino = (
                lambda fecha: confirmaciones.append(fecha) or True
            )
            vista.copiar_semana()

        finally:

            cuadrantes_view.DialogoCopiarSemana = dialogo_original

        self.assertEqual(confirmaciones, ["2026-07-20"])
        self.assertEqual(
            self._firma("2026-07-20"),
            [("lunes", turno_id, restaurante_id, repartidor_id)]
        )
        self.assertEqual(
            self._firma("2026-07-13"),
            [("lunes", turno_id, restaurante_id, repartidor_id)]
        )

    def test_guardar_y_aplicar_plantilla_desde_vista(self):

        restaurante_id = obtener_restaurantes()[0][0]
        turno_id = obtener_turnos()[0][0]
        repartidor_id = insertar_repartidor(
            "Luis",
            20,
            "Ronda",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="miercoles",
            descanso_fin="jueves"
        )
        guardar_turno_calendario(
            "lunes",
            turno_id,
            restaurante_id,
            repartidor_id,
            fecha_inicio_semana="2026-07-13"
        )
        guardar_dialogo_original = cuadrantes_view.DialogoGuardarPlantilla
        aplicar_dialogo_original = cuadrantes_view.DialogoAplicarPlantilla

        class DialogoGuardarFalso:

            def __init__(self, parent, fecha_origen):

                pass

            def exec(self):

                return cuadrantes_view.QDialog.Accepted

            def nombre(self):

                return "Base sin repartidores"

            def descripcion(self):

                return "Plantilla de prueba"

            def incluir_repartidores(self):

                return False

        class DialogoAplicarFalso:

            def __init__(self, parent, plantillas, fecha_destino):

                self.plantillas = plantillas

            def exec(self):

                return cuadrantes_view.QDialog.Accepted

            def plantilla_id(self):

                return self.plantillas[0][0]

            def fecha_destino(self):

                return "2026-07-20"

        cuadrantes_view.DialogoGuardarPlantilla = DialogoGuardarFalso
        cuadrantes_view.DialogoAplicarPlantilla = DialogoAplicarFalso

        try:

            vista = VistaCuadrantes()
            vista.selector_semana.setDate(QDate(2026, 7, 13))
            vista.guardar_plantilla()
            vista.aplicar_plantilla()

        finally:

            cuadrantes_view.DialogoGuardarPlantilla = guardar_dialogo_original
            cuadrantes_view.DialogoAplicarPlantilla = aplicar_dialogo_original

        self.assertEqual(
            self._firma("2026-07-20"),
            [("lunes", turno_id, restaurante_id, None)]
        )
        self.assertEqual(
            self._firma("2026-07-13"),
            [("lunes", turno_id, restaurante_id, repartidor_id)]
        )

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

    def _seleccionar_combo(self, combo, valor):

        indice = combo.findData(valor)
        self.assertNotEqual(indice, -1)
        combo.setCurrentIndex(indice)

    def _id_repartidor(self, nombre):

        for repartidor in database.obtener_repartidores():

            if repartidor[1] == nombre:

                return repartidor[0]

        self.fail(f"No existe el repartidor {nombre}")

    def _turno_por_nombre(self, nombre):

        for turno in obtener_turnos():

            if turno[2] == nombre:

                return turno

        self.fail(f"No existe el turno {nombre}")

    def _fila_empleado(self, vista, nombre):

        for fila in range(vista.tabla_empleados.rowCount()):

            item = vista.tabla_empleados.item(fila, 0)

            if item and item.text() == nombre:

                return fila

        self.fail(f"No existe la fila de empleado {nombre}")

    def _crear_pedro_martes_no_disponible(self):

        return insertar_repartidor(
            "Pedro",
            30,
            "Ronda",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="jueves",
            descanso_fin="viernes",
            disponibilidad={
                "lunes": "Ambos",
                "martes": "No disponible",
                "miercoles": "Ambos",
                "jueves": "No disponible",
                "viernes": "No disponible",
                "sabado": "Ambos",
                "domingo": "Ambos"
            }
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
