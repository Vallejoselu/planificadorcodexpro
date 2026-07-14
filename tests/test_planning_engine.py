import unittest

from services.rules.candidatos import buscar_candidatos
from services.planning_engine import PlanningEngine, generar_horarios
from services.planificador import generar_horarios as generar_horarios_legacy
from services.validators import validar_horario


class TestPlanningEngine(unittest.TestCase):

    def repartidores(self):

        return [
            {
                "id": 1,
                "nombre": "Ana",
                "horas": 20,
                "zona": "Ronda",
                "doble_turno": 1,
                "puede_hasta_la_una": 1,
                "descanso": ["lunes", "martes"],
                "disponibilidad": {
                    "miercoles": ["comida", "noche"],
                    "jueves": ["comida", "noche"],
                    "viernes": ["comida", "noche"]
                }
            },
            {
                "id": 2,
                "nombre": "Luis",
                "horas": 20,
                "zona": "Ronda",
                "doble_turno": 1,
                "puede_hasta_la_una": 1,
                "descanso": ["martes", "miercoles"],
                "disponibilidad": {
                    "lunes": ["comida", "noche"],
                    "jueves": ["comida", "noche"],
                    "viernes": ["comida", "noche"]
                }
            }
        ]

    def restaurantes(self):

        return [
            {
                "id": 1,
                "nombre": "R1",
                "zona": "Ronda"
            }
        ]

    def test_planning_engine_es_punto_de_entrada(self):

        resultado = PlanningEngine().generar(
            self.repartidores(),
            self.restaurantes()
        )

        self.assertIn("horario", resultado)
        self.assertIn("resumen", resultado)
        self.assertIn("incidencias", resultado)
        self.assertEqual(validar_horario(resultado), [])

    def test_funcion_publica_del_motor_mantiene_salida(self):

        resultado = generar_horarios(
            self.repartidores(),
            self.restaurantes()
        )

        self.assertEqual(validar_horario(resultado), [])

    def test_wrapper_legacy_de_planificador_conserva_comportamiento(self):

        nuevo = generar_horarios(
            self.repartidores(),
            self.restaurantes()
        )
        legacy = generar_horarios_legacy(
            self.repartidores(),
            self.restaurantes()
        )

        self.assertEqual(nuevo, legacy)

    def test_validador_detecta_descanso_y_duplicado(self):

        resultado = {
            "horario": {
                "lunes": {
                    "comida": [
                        {
                            "repartidor_id": 1
                        },
                        {
                            "repartidor_id": 1
                        }
                    ]
                }
            },
            "resumen": [
                {
                    "id": 1,
                    "nombre": "Ana",
                    "horas": 8,
                    "maximo": 10,
                    "descanso": ["lunes", "martes"]
                }
            ]
        }

        errores = validar_horario(resultado)

        self.assertTrue(
            any("duplicado" in error for error in errores)
        )
        self.assertTrue(
            any("descanso" in error for error in errores)
        )

    def test_generador_cubre_minimo_de_repartidores_por_turno(self):

        resultado = generar_horarios(
            [
                self.repartidor_base(1, "Ana"),
                self.repartidor_base(2, "Luis")
            ],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4,
                "min_repartidores": 2
            }]
        )

        self.assertEqual(
            len(resultado["horario"]["miercoles"]["comida"]),
            2
        )

    def test_generador_advierte_si_no_cumple_minimo(self):

        resultado = generar_horarios(
            [self.repartidor_base(1, "Ana")],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4,
                "min_repartidores": 2
            }]
        )

        self.assertTrue(
            any(
                incidencia.get("regla") == "minimo de repartidores por turno"
                for incidencia in resultado["incidencias"]
            )
        )

    def test_generador_respeta_maximo_de_horas_diarias(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["max_horas_diarias"] = 4

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[
                {
                    "nombre": "comida",
                    "horas": 4
                },
                {
                    "nombre": "noche",
                    "horas": 4
                }
            ]
        )

        self.assertTrue(
            any(
                "maximo de horas diarias" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )
        self.assertLessEqual(
            resultado["resumen"][0]["horas"],
            resultado["resumen"][0]["maximo"]
        )

    def test_generador_respeta_maximo_de_dias_consecutivos(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["max_dias_consecutivos"] = 1

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }]
        )

        self.assertTrue(
            any(
                "maximo de dias consecutivos" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_generador_respeta_horarios_no_permitidos(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["no_puede_turnos"] = ["noche"]

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "noche",
                "horas": 4
            }]
        )

        self.assertEqual(
            resultado["horario"]["miercoles"]["noche"],
            []
        )
        self.assertTrue(
            any(
                "no puede hacer ese horario" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_no_asigna_repartidor_en_descanso(self):

        resultado = generar_horarios(
            [self.repartidor_base(1, "Ana")],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }]
        )

        self.assertEqual(resultado["horario"]["lunes"]["comida"], [])
        self.assertTrue(
            any(
                "descanso" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_no_supera_horas_contratadas(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["horas"] = 4

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }]
        )

        self.assertEqual(resultado["resumen"][0]["horas"], 4)
        self.assertLessEqual(
            resultado["resumen"][0]["horas"],
            resultado["resumen"][0]["maximo"]
        )

    def test_no_asigna_dos_veces_mismo_repartidor_en_mismo_turno(self):

        resultado = generar_horarios(
            [self.repartidor_base(1, "Ana")],
            [
                {"id": 1, "nombre": "R1", "zona": "Ronda"},
                {"id": 2, "nombre": "R2", "zona": "Ronda"}
            ],
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }]
        )

        for dia, turnos_dia in resultado["horario"].items():

            for asignaciones in turnos_dia.values():

                ids = [
                    asignacion["repartidor_id"]
                    for asignacion in asignaciones
                    if asignacion.get("repartidor_id")
                ]
                self.assertEqual(
                    len(ids),
                    len(set(ids)),
                    f"Duplicado en {dia}: {ids}"
                )

    def test_respeta_vacaciones_y_bajas(self):

        repartidor = self.repartidor_base(1, "Ana")

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }],
            fecha_inicio="2026-07-13",
            vacaciones=[{
                "repartidor_id": 1,
                "fecha_inicio": "2026-07-15",
                "fecha_fin": "2026-07-15"
            }],
            bajas=[{
                "repartidor_id": 1,
                "fecha_inicio": "2026-07-16",
                "fecha_fin": "2026-07-16"
            }]
        )

        self.assertEqual(resultado["horario"]["miercoles"]["comida"], [])
        self.assertEqual(resultado["horario"]["jueves"]["comida"], [])
        self.assertTrue(
            any(
                "ausencia" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_asistente_y_planificador_rechazan_descanso_con_misma_regla(self):

        repartidor = self.repartidor_base(1, "Ana")
        turno_planificador = {
            "nombre": "comida",
            "horas": 4
        }
        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[turno_planificador]
        )
        contexto_asistente = {
            "repartidores": [{
                **repartidor,
                "activo": 1,
                "vacaciones": [],
                "bajas": [],
                "preferencias": []
            }],
            "turnos": [{
                "id": 1,
                "tipo": "Comida",
                "nombre": "Comida",
                "duracion": 4,
                "activo": 1
            }],
            "restaurantes": self.restaurantes(),
            "asignaciones_repartidor": []
        }

        candidatos, rechazos = buscar_candidatos(
            contexto_asistente,
            "lunes",
            contexto_asistente["turnos"][0],
            self.restaurantes()[0]
        )

        self.assertEqual(resultado["horario"]["lunes"]["comida"], [])
        self.assertEqual(candidatos, [])
        self.assertIn("estan descansando", rechazos)

    def test_generador_usa_horas_complementarias_permitidas(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["horas"] = 10
        repartidor["horas_complementarias"] = 2

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 6
            }]
        )

        self.assertEqual(resultado["resumen"][0]["maximo"], 12)
        self.assertEqual(resultado["resumen"][0]["horas"], 12)
        self.assertEqual(
            resultado["resumen"][0]["limite_horas_complementarias"],
            2
        )
        self.assertEqual(resultado["resumen"][0]["horas_complementarias"], 2)
        self.assertEqual(
            resultado["horas_complementarias"][0],
            {
                "repartidor_id": 1,
                "nombre": "Ana",
                "permitidas": True,
                "limite": 2,
                "usadas": 2,
                "disponibles": 0
            }
        )
        self.assertTrue(
            any(
                incidencia.get("regla") == "horas complementarias usadas"
                for incidencia in resultado["incidencias"]
            )
        )

    def test_generador_no_usa_horas_complementarias_si_no_estan_permitidas(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["horas"] = 10

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 6
            }]
        )

        self.assertEqual(resultado["resumen"][0]["maximo"], 10)
        self.assertEqual(resultado["resumen"][0]["horas"], 6)
        self.assertFalse(
            resultado["resumen"][0]["horas_complementarias_permitidas"]
        )
        self.assertEqual(resultado["resumen"][0]["horas_complementarias"], 0)
        self.assertTrue(
            any(
                "horas complementarias no permitidas"
                in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_generador_respeta_limite_de_horas_complementarias(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["horas"] = 8
        repartidor["horas_complementarias"] = 2

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 5
            }]
        )

        self.assertEqual(resultado["resumen"][0]["maximo"], 10)
        self.assertEqual(resultado["resumen"][0]["horas"], 10)
        self.assertEqual(resultado["resumen"][0]["horas_complementarias"], 2)
        self.assertTrue(
            any(
                "limite de horas complementarias" in incidencia["motivo"]
                for incidencia in resultado["incidencias"]
            )
        )

    def test_generador_permiso_explicito_bloquea_limite_configurado(self):

        repartidor = self.repartidor_base(1, "Ana")
        repartidor["horas"] = 10
        repartidor["horas_complementarias"] = 4
        repartidor["permite_horas_complementarias"] = False

        resultado = generar_horarios(
            [repartidor],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 6
            }]
        )

        self.assertEqual(resultado["resumen"][0]["maximo"], 10)
        self.assertEqual(
            resultado["resumen"][0]["limite_horas_complementarias"],
            0
        )
        self.assertEqual(resultado["resumen"][0]["horas_complementarias"], 0)

    def test_generador_prioriza_preferencias_de_local_y_turno(self):

        ana = self.repartidor_base(1, "Ana")
        luis = self.repartidor_base(2, "Luis")
        luis["preferencias"] = [{
            "restaurante_id": 1,
            "turno": "comida",
            "prioridad": 100
        }]

        resultado = generar_horarios(
            [ana, luis],
            self.restaurantes(),
            turnos=[{
                "nombre": "comida",
                "horas": 4
            }]
        )

        self.assertEqual(
            resultado["horario"]["miercoles"]["comida"][0]["repartidor"],
            "Luis"
        )

    def repartidor_base(self, identificador, nombre):

        return {
            "id": identificador,
            "nombre": nombre,
            "horas": 20,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "descanso": ["lunes", "martes"],
            "disponibilidad": {
                "miercoles": ["comida", "noche"],
                "jueves": ["comida", "noche"],
                "viernes": ["comida", "noche"],
                "sabado": ["comida", "noche"],
                "domingo": ["comida", "noche"]
            }
        }


if __name__ == "__main__":

    unittest.main()
