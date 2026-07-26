import unittest

from services.asistente_creacion_guiada import AsistenteCreacionGuiadaService


class ConfiguracionFalsa:

    def __init__(self, pasos, listo=False):

        self.pasos = pasos
        self.listo = listo

    def diagnosticar(self):

        return {
            "pasos": self.pasos,
            "resumen": {
                "estado": "Configuracion incompleta",
                "correctos": 1,
                "avisos": 0,
                "pendientes": 1,
                "total": len(self.pasos)
            },
            "listo": self.listo
        }


class TestAsistenteCreacionGuiadaService(unittest.TestCase):

    def test_obtener_flujo_numera_pasos_y_recomienda_primer_pendiente(self):

        servicio = AsistenteCreacionGuiadaService(ConfiguracionFalsa([
            {
                "codigo": "ciudades",
                "titulo": "Ciudades",
                "estado": "ok",
                "detalle": "Correcto",
                "pagina": "ciudades"
            },
            {
                "codigo": "restaurantes",
                "titulo": "Restaurantes",
                "estado": "pendiente",
                "detalle": "Falta crear restaurantes",
                "pagina": "restaurantes"
            }
        ]))

        flujo = servicio.obtener_flujo()

        self.assertEqual(flujo["indice_recomendado"], 1)
        self.assertEqual(flujo["pasos"][0]["numero"], 1)
        self.assertEqual(flujo["pasos"][0]["total"], 2)
        self.assertEqual(
            flujo["pasos"][1]["accion"],
            "Crear o revisar restaurantes"
        )

    def test_si_todo_esta_correcto_recomienda_generacion(self):

        servicio = AsistenteCreacionGuiadaService(ConfiguracionFalsa([
            {
                "codigo": "ciudades",
                "titulo": "Ciudades",
                "estado": "ok",
                "detalle": "Correcto",
                "pagina": "ciudades"
            },
            {
                "codigo": "generacion",
                "titulo": "Generacion",
                "estado": "ok",
                "detalle": "Listo",
                "pagina": "cuadrantes"
            }
        ], listo=True))

        flujo = servicio.obtener_flujo()

        self.assertEqual(flujo["indice_recomendado"], 1)
        self.assertTrue(flujo["listo"])
        self.assertEqual(flujo["pasos"][1]["accion"], "Ir a cuadrantes")


if __name__ == "__main__":

    unittest.main()
