import unittest

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
