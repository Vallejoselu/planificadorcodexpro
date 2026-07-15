import database.database as db


class SincronizacionesRepository:

    def registrar(self, *args, **kwargs):

        return db.registrar_sincronizacion_integracion(*args, **kwargs)

    def actualizar(self, *args, **kwargs):

        return db.actualizar_sincronizacion_integracion(*args, **kwargs)

    def obtener(self, sincronizacion_id):

        return db.obtener_sincronizacion_integracion(sincronizacion_id)

    def listar(self, limite=100, estado=None, proveedor=None):

        return db.obtener_sincronizaciones_integracion(
            limite,
            estado,
            proveedor
        )

    def listar_pendientes(self, ahora, limite=100):

        return db.obtener_sincronizaciones_pendientes(ahora, limite)
