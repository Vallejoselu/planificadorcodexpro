import tempfile
import unittest
from pathlib import Path

import database.database as database
from database.database import (
    crear_base_datos,
    guardar_turno_calendario,
    insertar_ciudad,
    insertar_repartidor,
    insertar_restaurante,
    insertar_turno,
    obtener_calendario_semanal,
    obtener_calendario_semanal_modelo,
    obtener_repartidores,
    obtener_repartidores_modelo,
    obtener_restaurantes,
    obtener_restaurantes_modelo,
    obtener_turnos_modelo,
    obtener_turnos
)
from models import (
    AsignacionCalendario,
    Ausencia,
    Disponibilidad,
    Repartidor,
    Restaurante,
    Turno
)


class TestModelosDominio(unittest.TestCase):

    def setUp(self):

        self.ruta_original = database.RUTA_BD
        self.temporal = tempfile.TemporaryDirectory()
        database.RUTA_BD = Path(self.temporal.name) / "delivery.db"
        crear_base_datos()

    def tearDown(self):

        database.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_repartidor_desde_fila_actual(self):

        ciudad = insertar_ciudad("Ciudad A")
        restaurante = insertar_restaurante(
            "Local A",
            "",
            "Centro",
            "",
            50,
            ciudad_id=ciudad
        )
        insertar_repartidor(
            "Ana",
            30,
            "Centro",
            1,
            1,
            70,
            40,
            20,
            ciudad_principal_id=ciudad,
            restaurante_principal_id=restaurante,
            apoyo_flexible=1,
            ciudades_autorizadas=[ciudad],
            restaurantes_autorizados=[restaurante]
        )

        modelo = Repartidor.from_row(obtener_repartidores()[0])

        self.assertEqual(modelo.nombre, "Ana")
        self.assertEqual(modelo.horas, 30)
        self.assertTrue(modelo.doble_turno)
        self.assertTrue(modelo.apoyo_flexible)
        self.assertEqual(modelo.ciudad_principal_id, ciudad)
        self.assertEqual(modelo.restaurantes_autorizados, [restaurante])
        self.assertEqual(obtener_repartidores_modelo()[0].nombre, "Ana")

    def test_restaurante_y_turno_desde_filas_actuales(self):

        ciudad = insertar_ciudad("Ciudad A")
        restaurante_id = insertar_restaurante(
            "Local A",
            "Calle 1",
            "Centro",
            "600000000",
            80,
            ciudad_id=ciudad
        )
        turno_id = insertar_turno(
            "Comida",
            "Comida",
            "12:00",
            "16:00",
            "#2563EB",
            4
        )

        restaurante = Restaurante.from_row(obtener_restaurantes()[0])
        turno = Turno.from_row(obtener_turnos()[0])

        self.assertEqual(restaurante.id, restaurante_id)
        self.assertEqual(restaurante.nombre, "Local A")
        self.assertEqual(restaurante.ciudad_id, ciudad)
        self.assertEqual(turno.id, turno_id)
        self.assertEqual(turno.nombre, "Comida")
        self.assertEqual(turno.duracion, 4)
        self.assertEqual(obtener_restaurantes_modelo()[0].nombre, "Local A")
        self.assertEqual(obtener_turnos_modelo()[0].nombre, "Comida")

    def test_asignacion_calendario_desde_fila_actual(self):

        restaurante_id = insertar_restaurante(
            "Local A",
            "",
            "Centro",
            "",
            50
        )
        insertar_turno(
            "Comida",
            "Comida",
            "12:00",
            "16:00",
            "#2563EB",
            4
        )
        turno_id = obtener_turnos()[0][0]
        guardar_turno_calendario(
            "lunes",
            turno_id,
            restaurante_id,
            None,
            "2026-07-13"
        )

        asignacion = AsignacionCalendario.from_row(
            obtener_calendario_semanal("2026-07-13")[0]
        )

        self.assertEqual(asignacion.dia, "lunes")
        self.assertEqual(asignacion.turno, "Comida")
        self.assertEqual(asignacion.restaurante, "Local A")
        self.assertEqual(asignacion.fecha_inicio_semana, "2026-07-13")
        self.assertEqual(
            obtener_calendario_semanal_modelo("2026-07-13")[0].dia,
            "lunes"
        )

    def test_disponibilidad_y_ausencia_desde_filas_simples(self):

        disponibilidad = Disponibilidad.from_row(
            (1, "lunes", "comida", 1, "Disponible")
        )
        ausencia = Ausencia.from_row(
            (2, 1, "2026-07-13", "2026-07-20", 1, "Vacaciones"),
            tipo="vacaciones"
        )

        self.assertTrue(disponibilidad.disponible)
        self.assertEqual(disponibilidad.turno, "comida")
        self.assertEqual(ausencia.tipo, "vacaciones")
        self.assertEqual(ausencia.fecha_fin, "2026-07-20")
        self.assertEqual(ausencia.to_dict()["observaciones"], "Vacaciones")


if __name__ == "__main__":

    unittest.main()
