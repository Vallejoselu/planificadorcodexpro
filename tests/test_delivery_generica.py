import unittest

from models.integracion import ConfiguracionIntegracion
from services.delivery_payload import crear_payload_delivery, crear_webhook_simulado
from services.integraciones.generica import IntegracionGenerica


DATOS_DELIVERY = {
    "fecha_inicio_semana": "2026-07-13",
    "horarios": [[
        "miercoles",
        "Comida",
        "Comida",
        "BK Centro",
        "Centro",
        "Ana",
        "13:00",
        "16:00",
        3
    ]],
    "totales": [
        ["Total horarios", 1],
        ["Total horas planificadas", 3]
    ]
}


class TestDeliveryGenerica(unittest.TestCase):

    def test_payload_delivery_usa_esquema_estable(self):

        payload = crear_payload_delivery(DATOS_DELIVERY)

        self.assertEqual(payload["schema"], "planificador.delivery.v1")
        self.assertEqual(payload["fecha_inicio_semana"], "2026-07-13")
        self.assertEqual(payload["turnos"][0]["hora_inicio"], "13:00")
        self.assertEqual(payload["totales"]["Total horarios"], 1)

    def test_webhook_simulado_prepara_solicitud_sin_enviar(self):

        solicitud = crear_webhook_simulado(
            "https://example.test/webhook",
            DATOS_DELIVERY
        )

        self.assertTrue(solicitud["simulado"])
        self.assertEqual(solicitud["metodo"], "POST")
        self.assertEqual(solicitud["url"], "https://example.test/webhook")
        self.assertEqual(
            solicitud["payload"]["turnos"][0]["restaurante"],
            "BK Centro"
        )

    def test_webhook_simulado_requiere_url(self):

        with self.assertRaises(ValueError):

            crear_webhook_simulado("", DATOS_DELIVERY)

    def test_integracion_generica_exporta_payload_json(self):

        integracion = IntegracionGenerica()

        resultado = integracion.exportar_horarios(DATOS_DELIVERY)

        self.assertTrue(resultado.correcto)
        self.assertEqual(resultado.accion, "exportar_horarios")
        self.assertEqual(
            resultado.datos["payload"]["schema"],
            "planificador.delivery.v1"
        )

    def test_integracion_generica_prepara_webhook_desde_configuracion(self):

        integracion = IntegracionGenerica(
            ConfiguracionIntegracion(
                proveedor="api_generica",
                nombre="API generica",
                base_url="https://example.test/webhook"
            )
        )

        resultado = integracion.preparar_webhook(DATOS_DELIVERY)

        self.assertTrue(resultado.correcto)
        self.assertEqual(resultado.accion, "webhook_simulado")
        self.assertTrue(resultado.datos["simulado"])
        self.assertEqual(resultado.datos["url"], "https://example.test/webhook")


if __name__ == "__main__":

    unittest.main()
