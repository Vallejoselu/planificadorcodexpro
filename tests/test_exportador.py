import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import (
    crear_base_datos,
    guardar_turno_calendario,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno
)
from services.exportador import exportar_excel


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


if __name__ == "__main__":

    unittest.main()
