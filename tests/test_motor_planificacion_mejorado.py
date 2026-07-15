import unittest

from services.planning_incidents import explicar_regla_incumplida
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
        self.assertEqual(
            incidencia["detalle_reglas"][0]["motivo"],
            "descanso consecutivo"
        )


if __name__ == "__main__":

    unittest.main()
