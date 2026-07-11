import unittest
from datetime import date

import services.asistente_horarios as asistente
import services.rule_engine as rule_engine
from services.rules.ausencias import esta_ausente, esta_ausente_por_tipo
from services.rules.candidatos import buscar_candidatos, puede_trabajar
from services.rules.disponibilidad import esta_disponible
from services.rules.horas import calcular_horas_pendientes


class TestReglasNegocioComunes(unittest.TestCase):

    def test_asistente_y_planificador_usan_reglas_comunes(self):

        self.assertIs(asistente.buscar_candidatos, buscar_candidatos)
        self.assertIs(rule_engine.puede_trabajar, puede_trabajar)
        self.assertIs(rule_engine.esta_disponible, esta_disponible)

    def test_disponibilidad_acepta_categoria_y_nombre_de_turno(self):

        repartidor = {
            "disponibilidad": {
                "lunes": ["comida", "Cierre"],
                "martes": "Cenas"
            }
        }

        self.assertTrue(
            esta_disponible(
                repartidor,
                "lunes",
                {"nombre": "Comida A"}
            )
        )
        self.assertTrue(
            esta_disponible(
                repartidor,
                "lunes",
                {"nombre": "Cierre"}
            )
        )
        self.assertTrue(
            esta_disponible(
                repartidor,
                "martes",
                {"tipo": "Cena", "nombre": "Cena"}
            )
        )

    def test_ausencias_cubre_planificador_y_asistente(self):

        repartidor = {
            "vacaciones": [{
                "inicio": "2026-07-13",
                "fin": "2026-07-14"
            }],
            "bajas": [{
                "dia": "viernes"
            }]
        }

        self.assertTrue(
            esta_ausente(repartidor, "lunes", date(2026, 7, 13))
        )
        self.assertTrue(
            esta_ausente_por_tipo(repartidor, "bajas", None, "viernes")
        )

    def test_horas_pendientes_es_regla_compartida(self):

        repartidor = {"id": 1, "horas": 20}
        horas = {1: 12.5}

        self.assertEqual(
            calcular_horas_pendientes(repartidor, horas),
            7.5
        )

    def test_buscar_candidatos_rechaza_mismos_motivos_en_asistente(self):

        contexto = {
            "repartidores": [{
                "id": 1,
                "nombre": "Ana",
                "horas": 20,
                "activo": 1,
                "descanso": ["lunes", "martes"],
                "disponibilidad": {"viernes": ["noche"]},
                "vacaciones": [],
                "bajas": [],
                "preferencias": []
            }],
            "turnos": [{
                "id": 1,
                "tipo": "Cena",
                "nombre": "Cena",
                "hora_inicio": "20:00",
                "hora_fin": "23:00",
                "duracion": 3,
                "activo": 1
            }],
            "restaurantes": [],
            "asignaciones_repartidor": []
        }

        candidatos, rechazos = buscar_candidatos(
            contexto,
            "lunes",
            contexto["turnos"][0]
        )

        self.assertEqual(candidatos, [])
        self.assertIn("estan descansando", rechazos)


if __name__ == "__main__":

    unittest.main()
