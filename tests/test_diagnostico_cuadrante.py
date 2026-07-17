import unittest

from services.cuadrantes_service import CuadrantesService


class TestDiagnosticoCuadrante(unittest.TestCase):

    def setUp(self):

        self.servicio = CuadrantesService()

    def test_diagnostico_semana_sin_cuadrante_explica_estado_pendiente(self):

        diagnostico = self.servicio.diagnosticar_semana(
            "2026-07-13",
            [],
            {},
            {
                "asignaciones": 0,
                "con_repartidor": 0,
                "sin_repartidor": 0
            },
            [],
            [self.turno()],
            [self.restaurante()],
            [self.repartidor()]
        )

        self.assertEqual(diagnostico["estado"], "pendiente")
        self.assertIn("No hay cuadrante guardado", diagnostico["resumen"])
        self.assertIn("Asignaciones: 0", diagnostico["texto"])

    def test_diagnostico_destaca_turnos_sin_cubrir(self):

        asignaciones = {
            ("lunes", 1): [{
                "restaurante_id": 1,
                "repartidor_id": None
            }]
        }
        indicadores = {
            "asignaciones": 1,
            "con_repartidor": 0,
            "sin_repartidor": 1
        }
        alertas = self.servicio.alertas_asignaciones_sin_repartidor(
            asignaciones,
            [self.turno()]
        )

        diagnostico = self.servicio.diagnosticar_semana(
            "2026-07-13",
            [self.fila_calendario(repartidor_id=None)],
            asignaciones,
            indicadores,
            alertas,
            [self.turno()],
            [self.restaurante()],
            [self.repartidor()]
        )

        self.assertEqual(diagnostico["estado"], "critico")
        self.assertEqual(diagnostico["sin_repartidor"], 1)
        self.assertIn("Asigna un repartidor compatible", diagnostico["texto"])

    def test_alertas_reglas_detecta_asignacion_en_dia_no_disponible(self):

        asignaciones = {
            ("martes", 1): [{
                "restaurante_id": 1,
                "repartidor_id": 10
            }]
        }
        repartidor = self.repartidor(
            disponibilidad={
                "lunes": "Ambos",
                "martes": "No disponible"
            },
            descanso=["jueves", "viernes"]
        )

        alertas = self.servicio.alertas_reglas_asignaciones(
            "2026-07-13",
            asignaciones,
            [self.turno()],
            [self.restaurante()],
            [repartidor]
        )

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["tipo"], "Reglas incumplidas")
        self.assertIn("disponibilidad", alertas[0]["detalle"])

    def test_diagnostico_preparar_estado_incluye_reglas_incumplidas(self):

        servicio = CuadrantesService(
            calendario_repository=FakeCalendarioRepository([
                self.fila_calendario(dia="martes", repartidor_id=10)
            ])
        )
        estado = servicio.preparar_estado_semana(
            "2026-07-13",
            [self.turno()],
            [self.restaurante()],
            [
                self.repartidor(
                    disponibilidad={"martes": "No disponible"},
                    descanso=["jueves", "viernes"]
                )
            ]
        )

        self.assertEqual(estado["diagnostico"]["estado"], "critico")
        self.assertTrue(
            any(
                alerta["tipo"] == "Reglas incumplidas"
                for alerta in estado["alertas"]
            )
        )

    def turno(self):

        return {
            "id": 1,
            "tipo": "Comida",
            "nombre": "Comida",
            "hora_inicio": "13:00",
            "hora_fin": "16:00",
            "color": "#2563EB",
            "duracion": 3,
            "activo": 1
        }

    def restaurante(self):

        return {
            "id": 1,
            "nombre": "Local Centro",
            "zona": "Centro",
            "ciudad_id": 1,
            "activo": 1
        }

    def repartidor(self, disponibilidad=None, descanso=None):

        return {
            "id": 10,
            "nombre": "Ana",
            "horas": 30,
            "zona": "Centro",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "prioridad_comida": 50,
            "prioridad_noche": 50,
            "prioridad_grela": 50,
            "descanso": descanso or ["martes", "miercoles"],
            "disponibilidad": disponibilidad or {"lunes": "Ambos"},
            "ciudad_principal_id": 1,
            "restaurante_principal_id": 1,
            "apoyo_flexible": 0,
            "horas_complementarias": 0,
            "max_horas_diarias": 10,
            "max_dias_consecutivos": 5,
            "ciudades_autorizadas": [1],
            "restaurantes_autorizados": [1]
        }

    def fila_calendario(self, dia="lunes", repartidor_id=10):

        return (
            1,
            dia,
            1,
            "Comida",
            "Comida",
            "#2563EB",
            1,
            "Local Centro",
            "Centro",
            repartidor_id,
            "Ana" if repartidor_id else None,
            "2026-07-13"
        )


class FakeCalendarioRepository:

    def __init__(self, filas):

        self.filas = filas

    def listar_semana(self, fecha_inicio_semana=None):

        return self.filas


if __name__ == "__main__":

    unittest.main()
