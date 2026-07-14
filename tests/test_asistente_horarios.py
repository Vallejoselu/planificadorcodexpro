import unittest
import sqlite3
import tempfile
from datetime import date
from pathlib import Path

import database.database as database
from database.database import crear_base_datos
from services.asistente_horarios import (
    buscar_candidatos,
    detectar_intencion,
    responder,
    solapa_turno
)


class TestAsistenteHorarios(unittest.TestCase):

    def contexto_base(self):

        return {
            "repartidores": [
                {
                    "id": 1,
                    "nombre": "Ana",
                    "horas": 20,
                    "zona": "Ronda",
                    "doble_turno": 1,
                    "puede_hasta_la_una": 1,
                    "descanso": ["lunes", "martes"],
                    "disponibilidad": {
                        "viernes": ["comida", "noche"],
                        "sabado": ["comida", "noche"]
                    },
                    "vacaciones": [],
                    "bajas": [],
                    "preferencias": []
                },
                {
                    "id": 2,
                    "nombre": "Luis",
                    "horas": 10,
                    "zona": "Ronda",
                    "doble_turno": 1,
                    "puede_hasta_la_una": 1,
                    "descanso": ["martes", "miercoles"],
                    "disponibilidad": {
                        "viernes": ["noche"],
                        "sabado": ["noche"]
                    },
                    "vacaciones": [],
                    "bajas": [],
                    "preferencias": [
                        {
                            "restaurante_id": 1,
                            "zona": "Ronda",
                            "turno": "Cena",
                            "prioridad": 80
                        }
                    ]
                },
                {
                    "id": 3,
                    "nombre": "Marta",
                    "horas": 10,
                    "zona": "Grela",
                    "doble_turno": 1,
                    "puede_hasta_la_una": 1,
                    "descanso": ["miercoles", "jueves"],
                    "disponibilidad": {
                        "viernes": ["noche"]
                    },
                    "vacaciones": [
                        {
                            "fecha_inicio": "2026-07-10",
                            "fecha_fin": "2026-07-12"
                        }
                    ],
                    "bajas": [],
                    "preferencias": []
                }
            ],
            "turnos": [
                {
                    "id": 1,
                    "tipo": "Cena",
                    "nombre": "Cena",
                    "hora_inicio": "20:00",
                    "hora_fin": "23:30",
                    "duracion": 3.5,
                    "activo": 1
                },
                {
                    "id": 2,
                    "tipo": "Comida",
                    "nombre": "Comida",
                    "hora_inicio": "13:00",
                    "hora_fin": "16:00",
                    "duracion": 3,
                    "activo": 1
                }
            ],
            "restaurantes": [
                {
                    "id": 1,
                    "nombre": "Ronda Centro",
                    "zona": "Ronda",
                    "activo": 1
                }
            ],
            "calendario": [],
            "asignaciones_repartidor": [
                {
                    "repartidor_id": 1,
                    "dia": "viernes",
                    "turno_id": 2,
                    "restaurante_id": 1,
                    "duracion": 3,
                    "hora_inicio": "13:00",
                    "hora_fin": "16:00"
                },
                {
                    "repartidor_id": 2,
                    "dia": "viernes",
                    "turno_id": 1,
                    "restaurante_id": 1,
                    "duracion": 8,
                    "hora_inicio": "20:00",
                    "hora_fin": "22:00"
                }
            ]
        }

    def test_deteccion_intenciones(self):

        self.assertEqual(
            detectar_intencion("Quien lleva menos horas esta semana?"),
            "menos_horas"
        )
        self.assertEqual(
            detectar_intencion("Que turnos estan sin cubrir?"),
            "turnos_sin_cubrir"
        )
        self.assertEqual(
            detectar_intencion("Quien puede cubrir la cena?"),
            "candidatos"
        )

    def test_horas_pendientes(self):

        respuesta = responder(
            "Cuantas horas le faltan a Ana?",
            self.contexto_base()
        )

        self.assertIn("Ana", respuesta)
        self.assertIn("17", respuesta)

    def test_descansos(self):

        respuesta = responder(
            "Quien descansa el lunes?",
            self.contexto_base()
        )

        self.assertIn("Ana", respuesta)
        self.assertNotIn("Luis", respuesta)

    def test_solapamientos(self):

        contexto = self.contexto_base()
        turno = contexto["turnos"][0]
        repartidor = contexto["repartidores"][1]

        self.assertTrue(
            solapa_turno(contexto, repartidor, "viernes", turno)
        )

    def test_seleccion_candidatos(self):

        contexto = self.contexto_base()
        turno = contexto["turnos"][0]
        restaurante = contexto["restaurantes"][0]

        candidatos, rechazos = buscar_candidatos(
            contexto,
            "viernes",
            turno,
            restaurante,
            None
        )

        self.assertEqual(candidatos[0]["repartidor"]["nombre"], "Ana")
        self.assertIn("tienen otro turno solapado", rechazos)

    def test_sin_candidatos(self):

        contexto = self.contexto_base()

        for repartidor in contexto["repartidores"]:

            repartidor["disponibilidad"] = {
                "viernes": []
            }

        respuesta = responder(
            "Quien puede cubrir la cena del viernes?",
            contexto
        )

        self.assertIn("No hay repartidores disponibles", respuesta)
        self.assertIn("no tienen disponibilidad", respuesta)

    def test_asistente_identifica_descanso_antiguo_invalido(self):

        contexto = self.contexto_base()
        contexto["repartidores"][1]["descanso"] = ["domingo", "lunes"]

        respuesta = responder(
            "Quien descansa el lunes?",
            contexto
        )

        self.assertIn("Configuracion no valida", respuesta)
        self.assertIn("Luis", respuesta)

    def test_pregunta_no_reconocida(self):

        respuesta = responder(
            "Como esta el tiempo?",
            self.contexto_base()
        )

        self.assertIn("No he reconocido", respuesta)

    def test_vacaciones_con_fecha(self):

        respuesta = responder(
            "Quien puede cubrir la cena de manana?",
            self.contexto_base(),
            fecha_referencia=date(2026, 7, 10)
        )

        self.assertNotIn("Marta puede cubrir", respuesta)

    def test_trabajar_sin_superar_horas(self):

        respuesta = responder(
            "Quien puede trabajar sin superar sus horas contratadas?",
            self.contexto_base()
        )

        self.assertIn("Ana", respuesta)
        self.assertIn("pendientes", respuesta)

    def test_quien_trabaja_en_turno(self):

        respuesta = responder(
            "Quien trabaja el viernes en comida?",
            self.contexto_base()
        )

        self.assertIn("Trabajan el viernes", respuesta)
        self.assertIn("Ana", respuesta)
        self.assertNotIn("Luis", respuesta)

    def test_resumen_cuadrante(self):

        respuesta = responder(
            "Dame un resumen del cuadrante",
            self.contexto_base()
        )

        self.assertIn("Resumen del cuadrante", respuesta)
        self.assertIn("2 asignaciones", respuesta)
        self.assertIn("horas pendientes", respuesta)

    def test_explica_por_que_no_puede_cubrir_turno(self):

        respuesta = responder(
            "Por que Luis no puede cubrir la comida del viernes?",
            self.contexto_base()
        )

        self.assertIn("Luis no puede cubrir", respuesta)
        self.assertIn("disponibilidad", respuesta)

    def test_explica_que_si_puede_cubrir_turno(self):

        respuesta = responder(
            "Por que Ana no puede cubrir la cena del viernes?",
            self.contexto_base()
        )

        self.assertIn("Ana puede cubrir", respuesta)
        self.assertIn("no tiene bloqueos", respuesta)

    def test_simulacion_vacaciones_no_modifica_contexto(self):

        contexto = self.contexto_base()
        vacaciones_antes = list(contexto["repartidores"][0]["vacaciones"])

        respuesta = responder(
            "Que ocurre si Ana esta de vacaciones el viernes?",
            contexto
        )

        self.assertIn("Simulacion", respuesta)
        self.assertIn("No se ha guardado", respuesta)
        self.assertEqual(
            contexto["repartidores"][0]["vacaciones"],
            vacaciones_antes
        )

    def test_simulacion_eliminar_turno_no_modifica_contexto(self):

        contexto = self.contexto_base()
        total_asignaciones = len(contexto["asignaciones_repartidor"])

        respuesta = responder(
            "Que ocurre si elimino a Luis del turno del viernes?",
            contexto
        )

        self.assertIn("eliminar a Luis", respuesta)
        self.assertIn("Turnos que quedarian descubiertos", respuesta)
        self.assertEqual(
            len(contexto["asignaciones_repartidor"]),
            total_asignaciones
        )

    def test_simulacion_propone_accion_aplicable(self):

        respuesta = responder(
            "Que ocurre si elimino a Luis del turno del viernes?",
            self.contexto_base()
        )

        self.assertIn("Accion sugerida", respuesta)
        self.assertIn("asignar a Ana", respuesta)
        self.assertIn("editando el cuadrante", respuesta)

    def test_simulacion_no_modifica_base_real(self):

        original = database.RUTA_BD

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"
            crear_base_datos()

            try:

                antes = self.contar_tablas(database.RUTA_BD)

                responder("Que ocurre si un restaurante necesita un repartidor adicional?")

                despues = self.contar_tablas(database.RUTA_BD)

                self.assertEqual(antes, despues)

            finally:

                database.RUTA_BD = original

    def contar_tablas(self, ruta):

        uri = "file:" + str(ruta).replace("\\", "/") + "?mode=ro"
        conexion = sqlite3.connect(uri, uri=True)
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
