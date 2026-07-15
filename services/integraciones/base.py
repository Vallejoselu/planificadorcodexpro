from models.integracion import ConfiguracionIntegracion, ResultadoIntegracion
from services.credenciales import GestorCredencialesIntegracion


class IntegracionBase:

    proveedor = ""
    nombre = ""

    def __init__(self, configuracion=None, gestor_credenciales=None):

        self.configuracion = configuracion or ConfiguracionIntegracion(
            proveedor=self.proveedor,
            nombre=self.nombre
        )
        self.gestor_credenciales = (
            gestor_credenciales or GestorCredencialesIntegracion()
        )

    def credenciales_disponibles(self):

        return self.gestor_credenciales.existe(
            self.configuracion.credenciales_referencia
        )

    def obtener_credenciales(self):

        return self.gestor_credenciales.obtener(
            self.configuracion.credenciales_referencia
        )

    def estado_credenciales(self):

        return self.gestor_credenciales.estado(
            self.configuracion.credenciales_referencia
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
