import tempfile
import unittest
import json
from pathlib import Path

import database.database as database
from database.database import (
    crear_base_datos,
    guardar_turno_calendario,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno
)
from services.exportador import (
    crear_calendario_ics,
    exportar_delivery_json,
    exportar_excel,
    exportar_ics
)


class TestExportador(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_exportar_excel_no_falla_con_calendario_semanal(self):

        repartidor_id = insertar_repartidor(
            "Ana",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={"miercoles": "Ambos"}
        )
        restaurante_id = insertar_restaurante(
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000000",
            50
        )
        turno_id = insertar_turno(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        guardar_turno_calendario(
            "miercoles",
            turno_id,
            restaurante_id,
            repartidor_id,
            "2026-07-13"
        )
        salida = Path(self.temporal.name) / "cuadrante.xlsx"

        exportar_excel(salida, "2026-07-13")

        self.assertTrue(salida.exists())
        self.assertGreater(salida.stat().st_size, 0)

    def test_exportar_ics_crea_evento_de_calendario(self):

        repartidor_id = insertar_repartidor(
            "Ana",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={"miercoles": "Ambos"}
        )
        restaurante_id = insertar_restaurante(
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000000",
            50
        )
        turno_id = insertar_turno(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        guardar_turno_calendario(
            "miercoles",
            turno_id,
            restaurante_id,
            repartidor_id,
            "2026-07-13"
        )
        salida = Path(self.temporal.name) / "cuadrante.ics"

        exportar_ics(salida, "2026-07-13")

        contenido = salida.read_text(encoding="utf-8")
        self.assertIn("BEGIN:VCALENDAR", contenido)
        self.assertIn("BEGIN:VEVENT", contenido)
        self.assertIn("SUMMARY:Comida - BK Centro", contenido)
        self.assertIn("DTSTART:20260715T130000", contenido)
        self.assertIn("DTEND:20260715T160000", contenido)
        self.assertIn("Repartidor: Ana", contenido)

    def test_exportar_delivery_json_crea_payload_generico(self):

        repartidor_id = insertar_repartidor(
            "Ana",
            30,
            "Centro",
            1,
            1,
            50,
            50,
            50,
            descanso_inicio="lunes",
            descanso_fin="martes",
            disponibilidad={"miercoles": "Ambos"}
        )
        restaurante_id = insertar_restaurante(
            "BK Centro",
            "Rua 1",
            "Centro",
            "600000000",
            50
        )
        turno_id = insertar_turno(
            "Comida",
            "Comida",
            "13:00",
            "16:00",
            "#2563EB",
            3
        )
        guardar_turno_calendario(
            "miercoles",
            turno_id,
            restaurante_id,
            repartidor_id,
            "2026-07-13"
        )
        salida = Path(self.temporal.name) / "delivery.json"

        exportar_delivery_json(salida, "2026-07-13")

        payload = json.loads(salida.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema"], "planificador.delivery.v1")
        self.assertEqual(payload["fecha_inicio_semana"], "2026-07-13")
        self.assertEqual(payload["turnos"][0]["restaurante"], "BK Centro")
        self.assertEqual(payload["turnos"][0]["repartidor"], "Ana")

    def test_ics_extiende_turnos_que_cruzan_medianoche(self):

        contenido = crear_calendario_ics({
            "fecha_inicio_semana": "2026-07-13",
            "horarios": [[
                "viernes",
                "Cena",
                "Cena",
                "BK Noche",
                "Centro",
                "Luis",
                "22:00",
                "01:00",
                3
            ]]
        })

        self.assertIn("DTSTART:20260717T220000", contenido)
        self.assertIn("DTEND:20260718T010000", contenido)


if __name__ == "__main__":

    unittest.main()
