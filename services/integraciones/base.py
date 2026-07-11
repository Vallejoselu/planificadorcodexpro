from models.integracion import ConfiguracionIntegracion, ResultadoIntegracion


class IntegracionBase:

    proveedor = ""
    nombre = ""

    def __init__(self, configuracion=None):

        self.configuracion = configuracion or ConfiguracionIntegracion(
            proveedor=self.proveedor,
            nombre=self.nombre
        )

    # Punto unico para que cada API futura convierta datos externos al modelo interno.
    def normalizar_pedido(self, datos):

        return dict(datos or {})

    def probar_conexion(self):

        return self.no_implementado("probar_conexion")

    def importar_pedidos(self):

        return self.no_implementado("importar_pedidos")

    def exportar_horarios(self, horarios):

        return self.no_implementado("exportar_horarios")

    def sincronizar(self):

        return self.no_implementado("sincronizar")

    def no_implementado(self, accion):

        return ResultadoIntegracion(
            correcto=False,
            proveedor=self.configuracion.proveedor,
            accion=accion,
            mensaje="Integracion preparada, conexion pendiente de implementar."
        )
