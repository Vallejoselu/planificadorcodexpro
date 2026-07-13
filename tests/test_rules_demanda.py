import unittest

from services.rules.demanda import (
    NIVEL_CIUDAD,
    NIVEL_DEFECTO,
    NIVEL_RESTAURANTE,
    NIVEL_ZONA,
    PRIORIDAD_NIVELES_DEMANDA,
    PRIORIDAD_PERIODOS_DEMANDA,
    nivel_demanda,
    seleccionar_demanda_prioritaria
)
from services.scheduler import demanda_aplicable


class TestRulesDemanda(unittest.TestCase):

    def test_prioridad_documentada_por_alcance_y_periodo(self):

        self.assertEqual(
            PRIORIDAD_NIVELES_DEMANDA,
            (
                NIVEL_RESTAURANTE,
                NIVEL_ZONA,
                NIVEL_CIUDAD,
                NIVEL_DEFECTO
            )
        )
        self.assertEqual(
            PRIORIDAD_PERIODOS_DEMANDA,
            ("fecha", "dia_semana")
        )

    def test_restaurante_gana_a_zona_ciudad_y_defecto(self):

        demandas = [
            self.demanda("defecto", dia_semana="lunes", necesarios=1),
            self.demanda("ciudad", dia_semana="lunes", necesarios=8),
            self.demanda("zona", dia_semana="lunes", necesarios=5),
            self.demanda("restaurante", dia_semana="lunes", necesarios=3)
        ]

        seleccion = seleccionar_demanda_prioritaria(
            demandas,
            "lunes",
            "2026-07-20"
        )

        self.assertEqual(seleccion["nivel"], "restaurante")
        self.assertEqual(seleccion["repartidores_necesarios"], 3)

    def test_alcance_gana_antes_que_periodo(self):

        demandas = [
            self.demanda("zona", fecha="2026-07-20", necesarios=7),
            self.demanda("restaurante", dia_semana="lunes", necesarios=2)
        ]

        seleccion = seleccionar_demanda_prioritaria(
            demandas,
            "lunes",
            "2026-07-20"
        )

        self.assertEqual(seleccion["nivel"], "restaurante")
        self.assertEqual(seleccion["repartidores_necesarios"], 2)

    def test_fecha_gana_a_dia_en_el_mismo_alcance(self):

        demandas = [
            self.demanda("zona", dia_semana="lunes", necesarios=4),
            self.demanda("zona", fecha="2026-07-20", necesarios=6)
        ]

        seleccion = seleccionar_demanda_prioritaria(
            demandas,
            "lunes",
            "2026-07-20"
        )

        self.assertEqual(seleccion["fecha"], "2026-07-20")
        self.assertEqual(seleccion["repartidores_necesarios"], 6)

    def test_demanda_cero_puede_sustituir_a_demanda_general(self):

        demandas = [
            self.demanda("ciudad", dia_semana="lunes", necesarios=4),
            self.demanda("zona", dia_semana="lunes", necesarios=0)
        ]

        seleccion = seleccionar_demanda_prioritaria(
            demandas,
            "lunes",
            "2026-07-20"
        )

        self.assertEqual(seleccion["nivel"], "zona")
        self.assertEqual(seleccion["repartidores_necesarios"], 0)

    def test_demandas_inactivas_no_aplican(self):

        demandas = [
            self.demanda("restaurante", dia_semana="lunes", necesarios=3, activo=0),
            self.demanda("zona", dia_semana="lunes", necesarios=5)
        ]

        seleccion = seleccionar_demanda_prioritaria(
            demandas,
            "lunes",
            "2026-07-20"
        )

        self.assertEqual(seleccion["nivel"], "zona")

    def test_nivel_se_deduce_desde_campos_existentes(self):

        self.assertEqual(nivel_demanda({"restaurante_id": 1}), "restaurante")
        self.assertEqual(nivel_demanda({"zona": "Centro"}), "zona")
        self.assertEqual(nivel_demanda({"ciudad_id": 1}), "ciudad")
        self.assertEqual(nivel_demanda({}), "defecto")

    def test_selector_legacy_de_restaurante_conserva_fecha_sobre_dia(self):

        demandas = [
            {
                "restaurante_id": 1,
                "turno_restaurante_id": 10,
                "dia_semana": "lunes",
                "repartidores_necesarios": 2,
                "activo": 1
            },
            {
                "restaurante_id": 1,
                "turno_restaurante_id": 10,
                "fecha": "2026-07-20",
                "repartidores_necesarios": 6,
                "activo": 1
            }
        ]

        seleccion = demanda_aplicable(
            demandas,
            restaurante_id=1,
            turno_id=10,
            dia="lunes",
            fecha_iso="2026-07-20"
        )

        self.assertEqual(seleccion["repartidores_necesarios"], 6)

    def demanda(self, nivel, necesarios, fecha=None, dia_semana=None, activo=1):

        demanda = {
            "nivel": nivel,
            "repartidores_necesarios": necesarios,
            "activo": activo
        }

        if fecha:

            demanda["fecha"] = fecha

        if dia_semana:

            demanda["dia_semana"] = dia_semana

        return demanda


if __name__ == "__main__":

    unittest.main()
