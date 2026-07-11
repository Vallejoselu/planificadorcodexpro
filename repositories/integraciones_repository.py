import database.database as db


class IntegracionesRepository:

    def listar_configuraciones(self):

        return db.obtener_integraciones_api()

    def obtener_configuracion(self, proveedor):

        return db.obtener_integracion_api(proveedor)

    def guardar_configuracion(self, *args, **kwargs):

        return db.guardar_integracion_api(*args, **kwargs)

    def registrar_evento(self, *args, **kwargs):

        return db.registrar_evento_integracion(*args, **kwargs)

    def listar_eventos(self, limite=100):

        return db.obtener_eventos_integracion(limite)
