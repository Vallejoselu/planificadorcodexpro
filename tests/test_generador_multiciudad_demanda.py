import os
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

import database.database as database
import views.cuadrantes as cuadrantes_view
from database.database import (
    crear_base_datos,
    guardar_demanda_restaurante,
    guardar_restaurante_turnos,
    insertar_ciudad,
    insertar_repartidor,
    insertar_restaurante,
    obtener_calendario_semanal,
    obtener_demanda_restaurante,
    obtener_o_crear_turno_calendario_restaurante,
    obtener_restaurante_turnos
)
from services.cuadrantes_service import CuadrantesService
from services.planning_engine import PlanningEngine
from views.cuadrantes import VistaCuadrantes


class TestGeneradorMulticiudadDemanda(unittest.TestCase):

    def test_demanda_por_fecha_tiene_prioridad_sobre_dia_semana(self):

        datos = self._datos_base()
        datos["demandas"].append({
            "restaurante_id": 1,
            "turno_restaurante_id": 10,
            "fecha": "2026-07-13",
            "repartidores_necesarios": 2,
            "activo": 1
        })

        resultado = self._generar(datos)

        self.assertEqual(
            len(resultado["horario"]["lunes"]["restaurante_1_turno_10"]),
            2
        )

    def test_demanda_cero_no_crea_asignaciones_ni_incidencia(self):

        datos = self._datos_base(necesarios=0)

        resultado = self._generar(datos)

        self.assertEqual(resultado["horario"]["lunes"], {})
        self.assertFalse(resultado["incidencias"])

    def test_demanda_de_catorce_crea_catorce_asignaciones_distintas(self):

        datos = self._datos_base(necesarios=14)
        datos["repartidores"] = [
            self._repartidor(indice, restaurante=1, ciudad=1)
            for indice in range(1, 15)
        ]

        resultado = self._generar(datos)
        asignaciones = resultado["horario"]["lunes"]["restaurante_1_turno_10"]

        self.assertEqual(len(asignaciones), 14)
        self.assertEqual(
            len({asignacion["repartidor_id"] for asignacion in asignaciones}),
            14
        )

    def test_cobertura_incompleta_detalla_contexto_y_faltantes(self):

        datos = self._datos_base(necesarios=4)
        datos["repartidores"] = [
            self._repartidor(1, restaurante=1, ciudad=1),
            self._repartidor(2, restaurante=1, ciudad=1)
        ]

        resultado = self._generar(datos)
        incidencia = resultado["incidencias"][0]

        self.assertEqual(incidencia["ciudad"], "Ciudad A")
        self.assertEqual(incidencia["restaurante"], "Local A")
        self.assertEqual(incidencia["fecha"], "2026-07-13")
        self.assertEqual(incidencia["turno"], "Comida A")
        self.assertEqual(incidencia["necesarios"], 4)
        self.assertEqual(incidencia["asignados"], 2)
        self.assertEqual(incidencia["faltan"], 2)
        self.assertIn("Regla incumplida", incidencia["motivo"])

    def test_no_asigna_restaurante_no_autorizado(self):

        datos = self._datos_base()
        datos["repartidores"] = [
            self._repartidor(1, restaurante=2, ciudad=1)
        ]

        resultado = self._generar(datos)

        self.assertEqual(
            resultado["horario"]["lunes"]["restaurante_1_turno_10"],
            []
        )
        self.assertIn(
            "restaurante no autorizado",
            resultado["incidencias"][0]["motivo"]
        )

    def test_apoyo_flexible_puede_cubrir_fuera_de_autorizaciones(self):

        datos = self._datos_base()
        datos["repartidores"] = [
            self._repartidor(
                1,
                restaurante=2,
                ciudad=2,
                apoyo_flexible=1
            )
        ]

        resultado = self._generar(datos)

        self.assertEqual(
            resultado["horario"]["lunes"]["restaurante_1_turno_10"][0][
                "repartidor_id"
            ],
            1
        )

    def test_prioriza_restaurante_principal(self):

        datos = self._datos_base()
        datos["repartidores"] = [
            self._repartidor(1, restaurante=2, ciudad=1, autorizados=[1]),
            self._repartidor(2, restaurante=1, ciudad=1)
        ]

        resultado = self._generar(datos)

        self.assertEqual(
            resultado["horario"]["lunes"]["restaurante_1_turno_10"][0][
                "repartidor_id"
            ],
            2
        )

    def test_prioriza_ciudad_principal(self):

        datos = self._datos_base()
        datos["repartidores"] = [
            self._repartidor(
                1,
                restaurante=1,
                ciudad=2,
                ciudades_autorizadas=[1]
            ),
            self._repartidor(2, restaurante=1, ciudad=1)
        ]

        resultado = self._generar(datos)

        self.assertEqual(
            resultado["horario"]["lunes"]["restaurante_1_turno_10"][0][
                "repartidor_id"
            ],
            2
        )

    def test_evita_solapamiento_parcial_entre_restaurantes(self):

        datos = self._datos_base()
        datos["restaurantes"].append({
            "id": 2,
            "nombre": "Local B",
            "zona": "Norte",
            "ciudad_id": 1,
            "ciudad": "Ciudad A"
        })
        datos["turnos"].append({
            "id": 20,
            "restaurante_id": 2,
            "nombre": "Media tarde",
            "hora_inicio": "14:00",
            "hora_fin": "18:00",
            "duracion": 4,
            "activo": 1
        })
        datos["demandas"].append({
            "restaurante_id": 2,
            "turno_restaurante_id": 20,
            "dia_semana": "lunes",
            "repartidores_necesarios": 1,
            "activo": 1
        })
        datos["repartidores"] = [
            self._repartidor(1, restaurante=1, ciudad=1, autorizados=[1, 2])
        ]

        resultado = self._generar(datos)

        cubiertas = sum(
            len(asignaciones)
            for asignaciones in resultado["horario"]["lunes"].values()
        )
        self.assertEqual(cubiertas, 1)
        self.assertIn(
            "solapamiento horario",
            resultado["incidencias"][0]["motivo"]
        )

    def test_evita_solapamiento_con_turno_que_cruza_medianoche(self):

        datos = self._datos_base()
        datos["turnos"][0].update({
            "nombre": "Cierre",
            "hora_inicio": "22:00",
            "hora_fin": "02:00",
            "cruza_medianoche": 1
        })
        datos["turnos"].append({
            "id": 20,
            "restaurante_id": 1,
            "nombre": "Madrugada",
            "hora_inicio": "01:00",
            "hora_fin": "04:00",
            "duracion": 3,
            "activo": 1
        })
        datos["demandas"].append({
            "restaurante_id": 1,
            "turno_restaurante_id": 20,
            "dia_semana": "martes",
            "repartidores_necesarios": 1,
            "activo": 1
        })
        datos["repartidores"] = [
            self._repartidor(1, restaurante=1, ciudad=1)
        ]

        resultado = self._generar(datos)

        self.assertEqual(
            len(resultado["horario"]["lunes"]["restaurante_1_turno_10"]),
            1
        )
        self.assertEqual(
            resultado["horario"]["martes"]["restaurante_1_turno_20"],
            []
        )

    def test_respeta_maximo_horas_diarias_con_turnos_propios(self):

        datos = self._datos_base(necesarios=1)
        datos["turnos"].append({
            "id": 20,
            "restaurante_id": 1,
            "nombre": "Cena",
            "hora_inicio": "20:00",
            "hora_fin": "23:00",
            "duracion": 3,
            "activo": 1
        })
        datos["demandas"].append({
            "restaurante_id": 1,
            "turno_restaurante_id": 20,
            "dia_semana": "lunes",
            "repartidores_necesarios": 1,
            "activo": 1
        })
        datos["repartidores"] = [
            self._repartidor(1, restaurante=1, ciudad=1, max_horas_diarias=4)
        ]

        resultado = self._generar(datos)

        self.assertIn(
            "maximo de horas diarias",
            resultado["incidencias"][0]["motivo"]
        )

    def test_respeta_maximo_dias_consecutivos(self):

        datos = self._datos_base(necesarios=1)
        datos["demandas"][0]["dia_semana"] = "lunes"
        datos["demandas"].append({
            "restaurante_id": 1,
            "turno_restaurante_id": 10,
            "dia_semana": "martes",
            "repartidores_necesarios": 1,
            "activo": 1
        })
        datos["repartidores"] = [
            self._repartidor(
                1,
                restaurante=1,
                ciudad=1,
                max_dias_consecutivos=1
            )
        ]

        resultado = self._generar(datos)

        self.assertIn(
            "maximo de dias consecutivos",
            resultado["incidencias"][0]["motivo"]
        )

    def test_vista_global_por_ciudad_incluye_restaurante(self):

        datos = self._datos_base()

        resultado = self._generar(datos)

        ciudad = resultado["ciudades"][1]
        self.assertEqual(ciudad["nombre"], "Ciudad A")
        self.assertIn(1, ciudad["restaurantes"])

    def test_escenario_realista_tres_ciudades_siete_restaurantes(self):

        ciudades = [
            {"id": 1, "nombre": "Ciudad A", "activo": 1},
            {"id": 2, "nombre": "Ciudad B", "activo": 1},
            {"id": 3, "nombre": "Ciudad C", "activo": 1}
        ]
        restaurantes = []
        turnos = []
        demandas = []
        repartidores = []
        restaurante_id = 1
        turno_id = 100

        for ciudad in ciudades:

            for _ in range(3 if ciudad["id"] == 1 else 2):

                restaurantes.append({
                    "id": restaurante_id,
                    "nombre": f"Local {restaurante_id}",
                    "zona": f"Zona {ciudad['id']}",
                    "ciudad_id": ciudad["id"],
                    "ciudad": ciudad["nombre"]
                })
                turnos.append({
                    "id": turno_id,
                    "restaurante_id": restaurante_id,
                    "nombre": "Comida",
                    "hora_inicio": "12:00",
                    "hora_fin": "16:00",
                    "duracion": 4,
                    "activo": 1
                })
                demandas.append({
                    "restaurante_id": restaurante_id,
                    "turno_restaurante_id": turno_id,
                    "dia_semana": "lunes",
                    "repartidores_necesarios": 1,
                    "activo": 1
                })
                repartidores.append(
                    self._repartidor(
                        restaurante_id,
                        restaurante=restaurante_id,
                        ciudad=ciudad["id"]
                    )
                )
                restaurante_id += 1
                turno_id += 1

        resultado = PlanningEngine().generar_multiciudad(
            repartidores,
            ciudades,
            restaurantes,
            turnos,
            demandas,
            fecha_inicio="2026-07-13"
        )

        self.assertEqual(
            sum(
                len(asignaciones)
                for asignaciones in resultado["horario"]["lunes"].values()
            ),
            7
        )

    def test_rendimiento_aproximado(self):

        ciudades = [{"id": i, "nombre": f"Ciudad {i}", "activo": 1}
                    for i in range(1, 4)]
        restaurantes = []
        turnos = []
        demandas = []

        for indice in range(1, 21):

            ciudad_id = ((indice - 1) % 3) + 1
            restaurantes.append({
                "id": indice,
                "nombre": f"Local {indice}",
                "zona": f"Zona {ciudad_id}",
                "ciudad_id": ciudad_id,
                "ciudad": f"Ciudad {ciudad_id}"
            })
            turnos.append({
                "id": indice,
                "restaurante_id": indice,
                "nombre": "Comida",
                "hora_inicio": "12:00",
                "hora_fin": "16:00",
                "duracion": 4,
                "activo": 1
            })

            for dia in database.DIAS_SEMANA:

                demandas.append({
                    "restaurante_id": indice,
                    "turno_restaurante_id": indice,
                    "dia_semana": dia,
                    "repartidores_necesarios": 1,
                    "activo": 1
                })

        repartidores = [
            self._repartidor(
                indice,
                restaurante=((indice - 1) % 20) + 1,
                ciudad=((indice - 1) % 3) + 1,
                apoyo_flexible=1,
                max_dias_consecutivos=7
            )
            for indice in range(1, 51)
        ]

        inicio = time.perf_counter()
        resultado = PlanningEngine().generar_multiciudad(
            repartidores,
            ciudades,
            restaurantes,
            turnos,
            demandas,
            fecha_inicio="2026-07-13"
        )
        duracion = time.perf_counter() - inicio

        self.assertLess(duracion, 2)
        self.assertIn("horario", resultado)

    def _generar(self, datos):

        return PlanningEngine().generar_multiciudad(
            datos["repartidores"],
            datos["ciudades"],
            datos["restaurantes"],
            datos["turnos"],
            datos["demandas"],
            fecha_inicio="2026-07-13"
        )

    def _datos_base(self, necesarios=1):

        return {
            "ciudades": [{
                "id": 1,
                "nombre": "Ciudad A",
                "activo": 1
            }],
            "restaurantes": [{
                "id": 1,
                "nombre": "Local A",
                "zona": "Centro",
                "ciudad_id": 1,
                "ciudad": "Ciudad A"
            }],
            "turnos": [{
                "id": 10,
                "restaurante_id": 1,
                "nombre": "Comida A",
                "hora_inicio": "12:00",
                "hora_fin": "16:00",
                "duracion": 4,
                "activo": 1
            }],
            "demandas": [{
                "restaurante_id": 1,
                "turno_restaurante_id": 10,
                "dia_semana": "lunes",
                "repartidores_necesarios": necesarios,
                "activo": 1
            }],
            "repartidores": [
                self._repartidor(1, restaurante=1, ciudad=1),
                self._repartidor(2, restaurante=1, ciudad=1)
            ]
        }

    def _repartidor(
        self,
        identificador,
        restaurante,
        ciudad,
        apoyo_flexible=0,
        autorizados=None,
        ciudades_autorizadas=None,
        max_horas_diarias=10,
        max_dias_consecutivos=5
    ):

        return {
            "id": identificador,
            "nombre": f"Rep {identificador}",
            "horas": 40,
            "zona": "Centro",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "descanso": ["jueves", "viernes"],
            "disponibilidad": {
                "lunes": ["comida", "noche", "Comida A", "Media tarde",
                          "Cierre"],
                "martes": ["comida", "noche", "Madrugada"],
                "miercoles": ["comida", "noche"],
                "jueves": ["comida", "noche"],
                "viernes": ["comida", "noche"]
            },
            "ciudad_principal_id": ciudad,
            "restaurante_principal_id": restaurante,
            "apoyo_flexible": apoyo_flexible,
            "ciudades_autorizadas": ciudades_autorizadas or [ciudad],
            "restaurantes_autorizados": autorizados or [restaurante],
            "max_horas_diarias": max_horas_diarias,
            "max_dias_consecutivos": max_dias_consecutivos
        }


class TestGeneradorMulticiudadBaseDatos(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()
        self.information_original = cuadrantes_view.QMessageBox.information
        cuadrantes_view.QMessageBox.information = lambda *args, **kwargs: None

    def tearDown(self):

        cuadrantes_view.QMessageBox.information = self.information_original
        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_validacion_de_demanda_permite_cero(self):

        ciudad, restaurante, turno = self._crear_modelo()

        guardar_demanda_restaurante(restaurante, [{
            "turno_restaurante_id": turno,
            "dia_semana": "lunes",
            "repartidores_necesarios": 0
        }])

        self.assertEqual(obtener_demanda_restaurante(restaurante)[0][5], 0)

    def test_turno_de_calendario_para_restaurante_es_idempotente(self):

        _, _, turno = self._crear_modelo()

        primero = obtener_o_crear_turno_calendario_restaurante(turno)
        segundo = obtener_o_crear_turno_calendario_restaurante(turno)

        self.assertEqual(primero, segundo)

    def test_preview_no_guarda_y_confirmacion_guarda_en_calendario(self):

        ciudad, restaurante, turno = self._crear_modelo()
        insertar_repartidor(
            "Ana",
            40,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="jueves",
            descanso_fin="viernes",
            disponibilidad={
                "lunes": "Comidas",
                "martes": "Ambos",
                "miercoles": "Ambos",
                "jueves": "Ambos",
                "viernes": "Ambos",
                "sabado": "No disponible",
                "domingo": "No disponible"
            },
            ciudad_principal_id=ciudad,
            restaurante_principal_id=restaurante,
            ciudades_autorizadas=[ciudad],
            restaurantes_autorizados=[restaurante]
        )
        guardar_demanda_restaurante(restaurante, [{
            "turno_restaurante_id": turno,
            "dia_semana": "lunes",
            "repartidores_necesarios": 1
        }])

        vista = VistaCuadrantes()
        vista.selector_semana.setDate(QDate(2026, 7, 13))
        generacion = CuadrantesService().generar_cuadrante(
            vista.contexto_cuadrante(),
            vista.fecha_inicio_semana()
        )
        resultado = generacion["resultado"]
        asignaciones = generacion["asignaciones"]

        self.assertIn("horario", resultado)
        self.assertTrue(asignaciones)
        self.assertEqual(obtener_calendario_semanal("2026-07-13"), [])

        vista.mostrar_resumen_generacion = lambda resultado: True
        vista.confirmar_sobrescritura = lambda: True
        vista.generar_cuadrante()

        self.assertEqual(len(obtener_calendario_semanal("2026-07-13")), 1)

    def _crear_modelo(self):

        ciudad = insertar_ciudad("Ciudad A")
        restaurante = insertar_restaurante(
            "Local A",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad
        )
        guardar_restaurante_turnos(restaurante, [{
            "nombre": "Comida A",
            "hora_inicio": "12:00",
            "hora_fin": "16:00",
            "duracion": 4,
            "activo": 1
        }])
        turno = obtener_restaurante_turnos(restaurante)[0][0]

        return ciudad, restaurante, turno


if __name__ == "__main__":

    unittest.main()
