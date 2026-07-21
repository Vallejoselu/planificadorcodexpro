import unittest

from services.centro_operativo import CentroOperativoService


class FakeConfiguracionService:

    def __init__(self, pasos):

        self.pasos = pasos

    def diagnosticar(self):

        pendientes = sum(
            1
            for paso in self.pasos
            if paso["estado"] == "pendiente"
        )
        avisos = sum(
            1
            for paso in self.pasos
            if paso["estado"] == "aviso"
        )

        return {
            "pasos": self.pasos,
            "resumen": {
                "pendientes": pendientes,
                "avisos": avisos,
                "correctos": len(self.pasos) - pendientes - avisos,
                "total": len(self.pasos)
            }
        }


class FakeRepository:

    def __init__(self, filas):

        self.filas = filas

    def listar_activos(self):

        return self.filas

    def listar_semana(self):

        return self.filas


class TestCentroOperativoService(unittest.TestCase):

    def crear_servicio(self, pasos, calendario=None):

        return CentroOperativoService(
            configuracion_service=FakeConfiguracionService(pasos),
            calendario_repository=FakeRepository(calendario or []),
            repartidores_repository=FakeRepository([{"id": 1}]),
            restaurantes_repository=FakeRepository([{"id": 1}]),
            turnos_repository=FakeRepository([{"id": 1}])
        )

    def test_estado_ok_recomienda_generar_si_no_hay_cuadrante(self):

        servicio = self.crear_servicio([
            {
                "titulo": "Generacion",
                "estado": "ok",
                "detalle": "Lista.",
                "pagina": "cuadrantes"
            }
        ])

        resumen = servicio.obtener_resumen()

        self.assertEqual(resumen["nivel"], "ok")
        self.assertEqual(resumen["estado"], "Listo para generar cuadrantes")
        self.assertEqual(resumen["accion"]["texto"], "Generar cuadrante")
        self.assertEqual(resumen["accion"]["pagina"], "cuadrantes")

    def test_pendiente_prioriza_resolver_dato_bloqueante(self):

        servicio = self.crear_servicio([
            {
                "titulo": "Demanda",
                "estado": "aviso",
                "detalle": "No hay demanda real.",
                "pagina": "configuracion"
            },
            {
                "titulo": "Restaurantes",
                "estado": "pendiente",
                "detalle": "No hay restaurantes activos.",
                "pagina": "restaurantes"
            }
        ])

        resumen = servicio.obtener_resumen()

        self.assertEqual(resumen["nivel"], "pendiente")
        self.assertEqual(resumen["pendientes"][0]["titulo"], "Restaurantes")
        self.assertEqual(resumen["accion"]["texto"], "Resolver Restaurantes")
        self.assertEqual(resumen["accion"]["pagina"], "restaurantes")

    def test_lista_pendientes_se_limita_para_no_cargar_inicio(self):

        pasos = [
            {
                "titulo": f"Paso {indice}",
                "estado": "aviso",
                "detalle": "Revisar.",
                "pagina": "puesta_marcha"
            }
            for indice in range(8)
        ]
        servicio = self.crear_servicio(pasos)

        resumen = servicio.obtener_resumen()

        self.assertEqual(len(resumen["pendientes"]), 5)
        self.assertEqual(resumen["pendientes"][-1]["titulo"], "Mas puntos")
        self.assertIn("4 punto(s) mas", resumen["pendientes"][-1]["detalle"])

    def test_metrica_cuadrante_muestra_cobertura_real(self):

        servicio = self.crear_servicio(
            [],
            calendario=[
                {"repartidor_id": 1},
                {"repartidor_id": None},
                {"repartidor_id": 2},
                (1, "lunes", 5, "Comida", "comida", "#fff", 2, "Local", "Zona", 3)
            ]
        )

        resumen = servicio.obtener_resumen()
        metrica = {
            item["clave"]: item["valor"]
            for item in resumen["metricas"]
        }

        self.assertEqual(metrica["cuadrante"], "3/4")
        self.assertEqual(resumen["accion"]["texto"], "Abrir cuadrante")


if __name__ == "__main__":

    unittest.main()
