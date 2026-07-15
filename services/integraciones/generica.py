from services.integraciones.base import IntegracionBase
from models.integracion import ResultadoIntegracion
from services.delivery_payload import crear_payload_delivery, crear_webhook_simulado


class IntegracionGenerica(IntegracionBase):

    proveedor = "api_generica"
    nombre = "API generica"

    def exportar_horarios(self, datos):

        payload = crear_payload_delivery(datos or {})

        return ResultadoIntegracion(
            correcto=True,
            proveedor=self.configuracion.proveedor,
            accion="exportar_horarios",
            mensaje="Payload JSON generico preparado.",
            datos={
                "payload": payload
            }
        )

    def preparar_webhook(self, datos):

        url = (
            self.configuracion.opciones.get("webhook_url")
            or self.configuracion.base_url
        )
        solicitud = crear_webhook_simulado(url, datos or {})

        return ResultadoIntegracion(
            correcto=True,
            proveedor=self.configuracion.proveedor,
            accion="webhook_simulado",
            mensaje="Webhook simulado preparado. No se ha enviado nada.",
            datos=solicitud
        )
