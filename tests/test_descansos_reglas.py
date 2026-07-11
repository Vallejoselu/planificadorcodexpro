import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import database.database as database
from database.database import (
    crear_base_datos,
    insertar_repartidor,
    obtener_repartidor,
    obtener_descansos_invalidos,
    validar_descanso
)
from services.asistente_horarios import responder
from services.planificador import generar_horarios
from services.rule_engine import (
    dias_no_disponibles,
    tiene_dias_consecutivos
)
from views.nuevo_repartidor import DESCANSO_NO_NECESARIO_TEXTO
from views.nuevo_repartidor import NuevoRepartidor


class TestReglasDescansos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def test_descansos_validos(self):

        validos = (
            ("lunes", "martes"),
            ("martes", "miercoles"),
            ("miercoles", "jueves"),
            ("jueves", "viernes")
        )

        for inicio, fin in validos:

            self.assertEqual(
                validar_descanso(inicio, fin),
                (inicio, fin)
            )

    def test_descansos_invalidos_fin_de_semana(self):

        invalidos = (
            ("viernes", "sabado"),
            ("sabado", "domingo"),
            ("domingo", "lunes")
        )

        for inicio, fin in invalidos:

            with self.assertRaises(ValueError):

                validar_descanso(inicio, fin)

    def test_formulario_no_ofrece_inicio_fin_de_semana(self):

        formulario = NuevoRepartidor()
        opciones = [
            formulario.descanso_inicio.itemText(indice)
            for indice in range(formulario.descanso_inicio.count())
        ]

        self.assertEqual(
            opciones,
            [
                DESCANSO_NO_NECESARIO_TEXTO,
                "lunes",
                "martes",
                "miercoles",
                "jueves"
            ]
        )
        self.assertNotIn("viernes", opciones)
        self.assertNotIn("sabado", opciones)
        self.assertNotIn("domingo", opciones)
        self.assertTrue(formulario.descanso_fin.isReadOnly())

    def test_formulario_calcula_segundo_dia(self):

        formulario = NuevoRepartidor()
        esperados = {
            "lunes": "martes",
            "martes": "miercoles",
            "miercoles": "jueves",
            "jueves": "viernes"
        }

        for inicio, fin in esperados.items():

            formulario.descanso_inicio.setCurrentText(inicio)
            self.assertEqual(formulario.descanso_fin.text(), fin)

    def test_roberto_lunes_jueves_no_recibe_descanso_adicional(self):

        resultado = generar_horarios(
            [self.roberto()],
            [self.restaurante()],
            turnos=self.turnos()
        )

        self.assertEqual(resultado["resumen"][0]["descanso"], [])

    def test_roberto_puede_recibir_turnos_lunes_a_jueves(self):

        resultado = generar_horarios(
            [self.roberto()],
            [self.restaurante()],
            turnos=self.turnos()
        )
        dias_asignados = {
            dia
            for dia, turnos in resultado["horario"].items()
            for asignaciones in turnos.values()
            if asignaciones
        }

        self.assertEqual(
            dias_asignados,
            {"lunes", "martes", "miercoles", "jueves"}
        )

    def test_roberto_no_recibe_turnos_viernes_sabado_domingo(self):

        resultado = generar_horarios(
            [self.roberto()],
            [self.restaurante()],
            turnos=self.turnos()
        )

        for dia in ("viernes", "sabado", "domingo"):

            for asignaciones in resultado["horario"][dia].values():

                self.assertEqual(asignaciones, [])

    def test_viernes_sabado_domingo_cuentan_como_descanso_suficiente(self):

        no_laborables = dias_no_disponibles(self.roberto())

        self.assertEqual(
            no_laborables,
            ["viernes", "sabado", "domingo"]
        )
        self.assertTrue(tiene_dias_consecutivos(no_laborables))

    def test_repartidor_disponible_siete_dias_necesita_descanso_adicional(self):

        repartidor = self.repartidor_disponible_todos()

        resultado = generar_horarios(
            [repartidor],
            [self.restaurante()],
            turnos=self.turnos()
        )

        self.assertIn(
            resultado["resumen"][0]["descanso"],
            [
                ["lunes", "martes"],
                ["martes", "miercoles"],
                ["miercoles", "jueves"],
                ["jueves", "viernes"]
            ]
        )

    def test_no_disponible_solo_domingo_necesita_descanso_adicional(self):

        repartidor = self.repartidor_disponible_todos()
        repartidor["disponibilidad"]["domingo"] = []

        resultado = generar_horarios(
            [repartidor],
            [self.restaurante()],
            turnos=self.turnos()
        )

        self.assertTrue(resultado["resumen"][0]["descanso"])

    def test_no_disponible_sabado_domingo_no_necesita_descanso_adicional(self):

        repartidor = self.repartidor_disponible_todos()
        repartidor["disponibilidad"]["sabado"] = []
        repartidor["disponibilidad"]["domingo"] = []

        resultado = generar_horarios(
            [repartidor],
            [self.restaurante()],
            turnos=self.turnos()
        )

        self.assertEqual(resultado["resumen"][0]["descanso"], [])

    def test_disponibilidad_y_descanso_se_guardan_por_separado(self):

        original = database.RUTA_BD

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"

            try:

                crear_base_datos()
                repartidor_id = insertar_repartidor(
                    "Roberto",
                    40,
                    "Ronda",
                    1,
                    1,
                    50,
                    50,
                    50,
                    disponibilidad=self.disponibilidad_roberto_opciones()
                )
                repartidor = obtener_repartidor(repartidor_id)

                self.assertIsNone(repartidor["descanso_inicio"])
                self.assertIsNone(repartidor["descanso_fin"])
                self.assertEqual(
                    repartidor["disponibilidad"]["viernes"],
                    []
                )

            finally:

                database.RUTA_BD = original

    def test_editar_disponibilidad_recalcula_si_hace_falta_descanso(self):

        formulario = NuevoRepartidor({
            "id": 1,
            "nombre": "Roberto",
            "horas": 40,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "prioridad_comida": 50,
            "prioridad_noche": 50,
            "prioridad_grela": 50,
            "observaciones": "",
            "descanso_inicio": None,
            "descanso_fin": None,
            "disponibilidad": self.disponibilidad_roberto_listas()
        })

        self.assertEqual(
            formulario.descanso_inicio.currentText(),
            DESCANSO_NO_NECESARIO_TEXTO
        )

        for dia in ("viernes", "sabado", "domingo"):

            formulario.disponibilidad[dia].setCurrentText("Ambos")

        formulario.actualizar_estado_descanso()

        self.assertEqual(formulario.descanso_inicio.currentText(), "lunes")

    def test_vacaciones_temporales_no_modifican_descanso_permanente(self):

        repartidor = self.repartidor_disponible_todos()
        repartidor["vacaciones"] = [{
            "fecha_inicio": "2026-07-13",
            "fecha_fin": "2026-07-19"
        }]

        resultado = generar_horarios(
            [repartidor],
            [self.restaurante()],
            turnos=self.turnos(),
            fecha_inicio="2026-07-13"
        )

        self.assertTrue(resultado["resumen"][0]["descanso"])

    def test_asistente_distingue_descanso_y_no_disponibilidad(self):

        contexto = {
            "repartidores": [self.roberto()],
            "turnos": self.turnos_asistente(),
            "restaurantes": [self.restaurante()],
            "calendario": [],
            "asignaciones_repartidor": []
        }

        respuesta = responder(
            "Roberto esta disponible?",
            contexto
        )

        self.assertIn(
            "Roberto puede trabajar de lunes, martes, miercoles, jueves",
            respuesta
        )
        self.assertIn("no necesita descanso adicional", respuesta)

    def test_generador_avisa_si_no_puede_completar_horas(self):

        repartidor = self.repartidor_disponible_todos()
        repartidor["disponibilidad"] = {
            "lunes": ["comida"],
            "martes": [],
            "miercoles": [],
            "jueves": [],
            "viernes": [],
            "sabado": [],
            "domingo": []
        }

        resultado = generar_horarios(
            [repartidor],
            [self.restaurante()],
            turnos=self.turnos()
        )

        self.assertTrue(
            any(
                "pendientes por falta de disponibilidad" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_planificador_no_genera_descansos_fin_de_semana(self):

        repartidores = [
            {
                "id": 1,
                "nombre": "Ana",
                "horas": 20,
                "zona": "Ronda",
                "doble_turno": 1,
                "puede_hasta_la_una": 1,
                "descanso": ["domingo", "lunes"],
                "disponibilidad": {
                    "lunes": ["comida", "noche"],
                    "martes": ["comida", "noche"],
                    "miercoles": ["comida", "noche"],
                    "jueves": ["comida", "noche"],
                    "viernes": ["comida", "noche"],
                    "sabado": ["comida", "noche"],
                    "domingo": ["comida", "noche"]
                }
            }
        ]
        restaurantes = [
            {
                "id": 1,
                "nombre": "R1",
                "zona": "Ronda"
            }
        ]

        resultado = generar_horarios(repartidores, restaurantes)
        descanso = resultado["resumen"][0]["descanso"]

        self.assertIn(
            descanso,
            [
                ["lunes", "martes"],
                ["martes", "miercoles"],
                ["miercoles", "jueves"],
                ["jueves", "viernes"]
            ]
        )
        self.assertNotIn("sabado", descanso)
        self.assertNotIn("domingo", descanso)

    def test_registros_antiguos_no_se_borran_automaticamente(self):

        original = database.RUTA_BD

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            database.RUTA_BD = ruta

            try:

                crear_base_datos()
                conexion = sqlite3.connect(ruta)
                cursor = conexion.cursor()
                cursor.execute("""
                INSERT INTO repartidores(
                    nombre,
                    horas,
                    zona
                )
                VALUES(?,?,?)
                """,(
                    "Antiguo",
                    20,
                    "Ronda"
                ))
                repartidor_id = cursor.lastrowid
                cursor.execute("""
                INSERT INTO descansos(
                    repartidor_id,
                    dia_inicio,
                    dia_fin,
                    activo
                )
                VALUES(?,?,?,1)
                """,(
                    repartidor_id,
                    "sabado",
                    "domingo"
                ))
                conexion.commit()
                conexion.close()

                invalidos = obtener_descansos_invalidos()

                conexion = sqlite3.connect(ruta)
                total = conexion.execute(
                    "SELECT COUNT(*) FROM descansos"
                ).fetchone()[0]
                conexion.close()

                self.assertEqual(total, 1)
                self.assertEqual(len(invalidos), 1)
                self.assertEqual(invalidos[0][1], "Antiguo")

            finally:

                database.RUTA_BD = original

    def roberto(self):

        return {
            "id": 1,
            "nombre": "Roberto",
            "horas": 40,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "disponibilidad": self.disponibilidad_roberto_listas()
        }

    def repartidor_disponible_todos(self):

        return {
            "id": 2,
            "nombre": "Ana",
            "horas": 40,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "disponibilidad": {
                dia: ["comida", "noche"]
                for dia in database.DIAS_SEMANA
            }
        }

    def disponibilidad_roberto_listas(self):

        return {
            "lunes": ["comida", "noche"],
            "martes": ["comida", "noche"],
            "miercoles": ["comida", "noche"],
            "jueves": ["comida", "noche"],
            "viernes": [],
            "sabado": [],
            "domingo": []
        }

    def disponibilidad_roberto_opciones(self):

        return {
            "lunes": "Ambos",
            "martes": "Ambos",
            "miercoles": "Ambos",
            "jueves": "Ambos",
            "viernes": "No disponible",
            "sabado": "No disponible",
            "domingo": "No disponible"
        }

    def restaurante(self):

        return {
            "id": 1,
            "nombre": "R1",
            "zona": "Ronda"
        }

    def turnos(self):

        return [
            {
                "nombre": "comida",
                "horas": 4
            },
            {
                "nombre": "noche",
                "horas": 4
            }
        ]

    def turnos_asistente(self):

        return [
            {
                "id": 1,
                "tipo": "Comida",
                "nombre": "Comida",
                "duracion": 4,
                "activo": 1
            },
            {
                "id": 2,
                "tipo": "Cena",
                "nombre": "Cena",
                "duracion": 4,
                "activo": 1
            }
        ]


if __name__ == "__main__":

    unittest.main()
