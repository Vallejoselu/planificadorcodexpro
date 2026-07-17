import unittest

from services.planning_incidents import explicar_regla_incumplida
from services.planning_engine import PlanningEngine
from services.planning_models import PuntuacionConfig
from services.planning_preparation import preparar_datos_planificacion
from services.planning_scoring import puntuacion_solucion
from services.planning_validation import validar_planificacion
from services.rules.candidatos import puntuacion_preferencia
from services.scheduler import construir_planificacion


class TestMotorPlanificacionMejorado(unittest.TestCase):

    def repartidor(self, identificador, nombre="Ana"):

        return {
            "id": identificador,
            "nombre": nombre,
            "horas_asignadas": 0,
            "horas_contratadas": 30,
            "maximo_horas": 40,
            "turnos_comida": 0,
            "turnos_noche": 0,
            "restaurante_principal_id": 1,
            "restaurantes_autorizados": [1],
            "ciudad_principal_id": 1,
            "ciudades_autorizadas": [1],
            "apoyo_flexible": 0,
            "preferencias": [{
                "restaurante_id": 1,
                "turno": "comida",
                "prioridad": 80
            }],
            "_restaurante_por_dia": {},
            "_zona_por_dia": {}
        }

    def restaurante(self):

        return {
            "id": 1,
            "nombre": "Local A",
            "zona": "Centro",
            "ciudad_id": 1
        }

    def turno(self):

        return {
            "nombre": "comida",
            "horas": 4,
            "hora_inicio": "13:00",
            "hora_fin": "17:00"
        }

    def test_preparacion_de_datos_expone_contexto_normalizado(self):

        datos = preparar_datos_planificacion(
            [{
                "id": 1,
                "nombre": "Ana",
                "horas": 30,
                "zona": "Centro",
                "descanso": ["lunes", "martes"]
            }],
            restaurantes=[self.restaurante()],
            turnos=[self.turno()],
            fecha_inicio="2026-07-13"
        )

        self.assertEqual(datos["repartidores"][0]["horas_contratadas"], 30)
        self.assertIn("lunes", datos["fechas"])
        self.assertEqual(datos["restaurantes"][0]["nombre"], "Local A")

    def test_puntuacion_devuelve_detalle_y_permite_pesos(self):

        repartidor = self.repartidor(1)
        restaurante = self.restaurante()
        turno = self.turno()

        con_preferencia = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            devolver_detalle=True
        )
        sin_preferencia = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            config=PuntuacionConfig(peso_preferencia=0),
            devolver_detalle=True
        )

        self.assertLess(con_preferencia.valores[5], sin_preferencia.valores[5])
        self.assertIn("preferencia", con_preferencia.detalle)

    def test_puntuacion_aplica_penalizacion_desplazamiento_configurada(self):

        repartidor = self.repartidor(1)
        repartidor["_restaurante_por_dia"]["lunes"] = 1
        repartidor["_zona_por_dia"]["lunes"] = "Centro"
        restaurante = {
            "id": 2,
            "nombre": "Local B",
            "zona": "Sur",
            "ciudad_id": 1
        }
        turno = self.turno()

        repartidor["penalizacion_desplazamiento"] = 1
        baja = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            devolver_detalle=True
        )
        repartidor["penalizacion_desplazamiento"] = 5
        alta = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            devolver_detalle=True
        )

        self.assertEqual(baja.detalle["desplazamiento"], 3)
        self.assertEqual(alta.detalle["desplazamiento"], 3)
        self.assertGreater(alta.valores[9], baja.valores[9])

    def test_puntuacion_aplica_peso_prioridad_zona_configurado(self):

        repartidor = self.repartidor(1)
        repartidor["zona"] = "Centro"
        repartidor["preferencias"] = []
        repartidor["restaurante_fijo"] = None
        repartidor["peso_prioridad_zona"] = 30
        restaurante = self.restaurante()

        self.assertEqual(
            puntuacion_preferencia(repartidor, restaurante, self.turno()),
            80
        )

    def test_puntuacion_aplica_peso_restaurante_fijo_configurado(self):

        repartidor = self.repartidor(1)
        repartidor["zona"] = "Norte"
        repartidor["preferencias"] = []
        repartidor["restaurante_fijo"] = 1
        repartidor["peso_restaurante_fijo"] = 40
        restaurante = self.restaurante()

        self.assertEqual(
            puntuacion_preferencia(repartidor, restaurante, self.turno()),
            90
        )

    def test_puntuacion_aplica_peso_balance_comidas_cenas_configurado(self):

        repartidor = self.repartidor(1)
        restaurante = self.restaurante()
        turno = self.turno()
        repartidor["turnos_comida"] = 3
        repartidor["turnos_noche"] = 0

        repartidor["peso_balance_comidas_cenas"] = 1
        bajo = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            devolver_detalle=True
        )
        repartidor["peso_balance_comidas_cenas"] = 5
        alto = puntuacion_solucion(
            repartidor,
            restaurante,
            "lunes",
            turno,
            devolver_detalle=True
        )

        self.assertEqual(bajo.detalle["diferencia_turnos"], 4)
        self.assertGreater(alto.valores[10], bajo.valores[10])

    def test_incidencia_explica_motivos_agregados(self):

        repartidor = self.repartidor(1)
        repartidor["descanso"] = ["lunes"]
        repartidor["disponibilidad"] = {"lunes": []}
        repartidor["_turnos_asignados"] = set()
        repartidor["_dias_asignados"] = set()
        repartidor["_horas_por_dia"] = {}
        repartidor["_intervalos_asignados"] = []
        explicacion = explicar_regla_incumplida(
            [repartidor],
            self.restaurante(),
            "lunes",
            self.turno(),
            None
        )

        self.assertEqual(explicacion["principal"], "descanso consecutivo")
        self.assertEqual(
            explicacion["detalle"],
            [{"motivo": "descanso consecutivo", "cantidad": 1}]
        )

    def test_validacion_final_detecta_horas_y_duplicados(self):

        resultado = {
            "resumen": [{
                "nombre": "Ana",
                "horas": 42,
                "maximo": 40
            }],
            "horario": {
                "lunes": {
                    "comida": [
                        {"repartidor_id": 1, "restaurante": "Local A"},
                        {"repartidor_id": 1, "restaurante": "Local A"}
                    ]
                }
            }
        }

        reglas = {
            incidencia["regla"]
            for incidencia in validar_planificacion(resultado)
        }

        self.assertIn("validacion final de horas", reglas)
        self.assertIn("validacion final de duplicados", reglas)

    def test_planificacion_incluye_detalle_de_reglas_en_incidencias(self):

        datos = preparar_datos_planificacion(
            [{
                "id": 1,
                "nombre": "Ana",
                "horas": 10,
                "zona": "Centro",
                "descanso": ["lunes", "martes"],
                "disponibilidad": {"lunes": []}
            }],
            restaurantes=[self.restaurante()],
            turnos=[self.turno()],
            fecha_inicio="2026-07-13"
        )

        resultado = construir_planificacion(datos)
        incidencia = next(
            incidencia
            for incidencia in resultado["incidencias"]
            if incidencia.get("detalle_reglas")
        )

        self.assertIn("detalle_reglas", incidencia)
        self.assertIn("resumen_reglas", incidencia)
        self.assertIn("Detalle:", incidencia["motivo"])
        self.assertEqual(
            incidencia["detalle_reglas"][0]["motivo"],
            "descanso consecutivo"
        )

    def test_multiciudad_prioriza_turno_con_menos_candidatos(self):

        ciudades = [{
            "id": 1,
            "nombre": "Ciudad A",
            "activo": 1
        }]
        restaurantes = [
            {
                "id": 1,
                "nombre": "Local facil",
                "zona": "Centro",
                "ciudad_id": 1,
                "ciudad": "Ciudad A"
            },
            {
                "id": 2,
                "nombre": "Local dificil",
                "zona": "Centro",
                "ciudad_id": 1,
                "ciudad": "Ciudad A"
            }
        ]
        turnos = [
            {
                "id": 10,
                "restaurante_id": 1,
                "nombre": "Comida facil",
                "hora_inicio": "12:00",
                "hora_fin": "16:00",
                "duracion": 4,
                "activo": 1
            },
            {
                "id": 20,
                "restaurante_id": 2,
                "nombre": "Comida dificil",
                "hora_inicio": "12:00",
                "hora_fin": "16:00",
                "duracion": 4,
                "activo": 1
            }
        ]
        demandas = [
            {
                "restaurante_id": 1,
                "turno_restaurante_id": 10,
                "dia_semana": "lunes",
                "repartidores_necesarios": 1,
                "activo": 1
            },
            {
                "restaurante_id": 2,
                "turno_restaurante_id": 20,
                "dia_semana": "lunes",
                "repartidores_necesarios": 1,
                "activo": 1
            }
        ]
        repartidores = [
            self.repartidor_multiciudad(1, [1, 2]),
            self.repartidor_multiciudad(2, [1])
        ]

        resultado = PlanningEngine().generar_multiciudad(
            repartidores,
            ciudades,
            restaurantes,
            turnos,
            demandas,
            fecha_inicio="2026-07-13"
        )
        facil = resultado["horario"]["lunes"]["restaurante_1_turno_10"]
        dificil = resultado["horario"]["lunes"]["restaurante_2_turno_20"]

        self.assertEqual(dificil[0]["repartidor_id"], 1)
        self.assertEqual(facil[0]["repartidor_id"], 2)
        self.assertFalse([
            incidencia
            for incidencia in resultado["incidencias"]
            if incidencia.get("regla") == "cobertura requerida por demanda"
        ])

    def repartidor_multiciudad(self, identificador, autorizados):

        return {
            "id": identificador,
            "nombre": f"Rep {identificador}",
            "horas": 40,
            "zona": "Centro",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "descanso": ["jueves", "viernes"],
            "disponibilidad": {
                "lunes": ["comida", "noche"]
            },
            "ciudad_principal_id": 1,
            "restaurante_principal_id": 1,
            "ciudades_autorizadas": [1],
            "restaurantes_autorizados": autorizados,
            "max_horas_diarias": 10,
            "max_dias_consecutivos": 5
        }


if __name__ == "__main__":

    unittest.main()
