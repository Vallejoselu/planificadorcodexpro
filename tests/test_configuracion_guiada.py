import unittest

from services.configuracion_guiada import ConfiguracionGuiadaService


class FakeCiudadesRepository:

    def __init__(self, ciudades=None):

        self.ciudades = ciudades or []

    def listar_activas(self):

        return self.ciudades


class FakeRepartidoresRepository:

    def __init__(self, repartidores=None):

        self.repartidores = repartidores or []

    def listar_activos(self):

        return self.repartidores


class FakeRestaurantesRepository:

    def __init__(
        self,
        restaurantes=None,
        turnos=None,
        demandas=None
    ):

        self.restaurantes = restaurantes or []
        self.turnos = turnos or {}
        self.demandas = demandas or {}

    def listar_activos(self):

        return self.restaurantes

    def listar_turnos(self, restaurante_id):

        return self.turnos.get(restaurante_id, [])

    def listar_demanda(self, restaurante_id):

        return self.demandas.get(restaurante_id, [])


class FakeTurnosRepository:

    def __init__(self, turnos=None):

        self.turnos = turnos or []

    def listar_activos(self):

        return self.turnos


class FakeDemandasRepository:

    def __init__(self, demandas=None):

        self.demandas = demandas or []

    def listar(self):

        return self.demandas


class TestConfiguracionGuiadaService(unittest.TestCase):

    def test_diagnostico_detecta_configuracion_incompleta(self):

        servicio = self.servicio()

        diagnostico = servicio.diagnosticar()
        estados = {
            paso["codigo"]: paso["estado"]
            for paso in diagnostico["pasos"]
        }

        self.assertFalse(diagnostico["listo"])
        self.assertEqual(estados["restaurantes"], "pendiente")
        self.assertEqual(estados["repartidores"], "pendiente")
        self.assertEqual(estados["generacion"], "pendiente")
        self.assertGreater(diagnostico["resumen"]["pendientes"], 0)

    def test_diagnostico_avisa_si_falta_demanda(self):

        servicio = self.servicio(
            ciudades=[(1, "Santiago", 1)],
            restaurantes=[self.restaurante()],
            repartidores=[self.repartidor(disponibilidad={"lunes": ["comida"]})],
            turnos=[self.turno()]
        )

        diagnostico = servicio.diagnosticar()
        demanda = self.paso(diagnostico, "demanda")
        generacion = self.paso(diagnostico, "generacion")

        self.assertTrue(diagnostico["listo"])
        self.assertEqual(demanda["estado"], "aviso")
        self.assertIn("No hay demanda", demanda["detalle"])
        self.assertEqual(generacion["estado"], "aviso")

    def test_diagnostico_listo_con_datos_completos(self):

        restaurante = self.restaurante()
        servicio = self.servicio(
            ciudades=[(1, "Santiago", 1)],
            restaurantes=[restaurante],
            repartidores=[
                self.repartidor(
                    disponibilidad={"lunes": ["comida"]},
                    ciudad_principal_id=1
                )
            ],
            turnos=[self.turno()],
            demandas_restaurante={
                2: [self.demanda_restaurante()]
            }
        )

        diagnostico = servicio.diagnosticar()

        self.assertTrue(diagnostico["listo"])
        self.assertEqual(
            diagnostico["resumen"]["estado"],
            "Lista para generar cuadrantes"
        )
        self.assertTrue(
            all(paso["estado"] == "ok" for paso in diagnostico["pasos"])
        )

    def servicio(
        self,
        ciudades=None,
        restaurantes=None,
        repartidores=None,
        turnos=None,
        demandas_restaurante=None,
        demandas_zona=None,
        demandas_ciudad=None
    ):

        return ConfiguracionGuiadaService(
            ciudades_repository=FakeCiudadesRepository(ciudades),
            repartidores_repository=FakeRepartidoresRepository(repartidores),
            restaurantes_repository=FakeRestaurantesRepository(
                restaurantes,
                demandas=demandas_restaurante
            ),
            turnos_repository=FakeTurnosRepository(turnos),
            demandas_zona_repository=FakeDemandasRepository(demandas_zona),
            demandas_ciudad_repository=FakeDemandasRepository(demandas_ciudad)
        )

    def paso(self, diagnostico, codigo):

        return next(
            paso
            for paso in diagnostico["pasos"]
            if paso["codigo"] == codigo
        )

    def restaurante(self):

        return (2, "BK Centro", "", "Centro", "", 50, 1, "", "", 1, "Santiago")

    def turno(self):

        return (5, "Comida", "Comida", "13:00", "16:00", "", 3, 1)

    def demanda_restaurante(self):

        return (1, 2, 5, None, "lunes", 1, 1)

    def repartidor(
        self,
        disponibilidad=None,
        ciudad_principal_id=None,
        restaurante_principal_id=None,
        apoyo_flexible=0
    ):

        return (
            1,
            "Ana",
            30,
            "Centro",
            0,
            0,
            50,
            50,
            50,
            "martes",
            "miercoles",
            disponibilidad or {},
            [],
            [],
            [],
            ciudad_principal_id,
            restaurante_principal_id,
            apoyo_flexible,
            0,
            10,
            5,
            [],
            []
        )


if __name__ == "__main__":

    unittest.main()
