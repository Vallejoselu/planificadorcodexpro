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


if __name__ == "__main__":

    unittest.main()
