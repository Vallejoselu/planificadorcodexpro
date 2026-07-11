import database.database as db


class RepartidoresRepository:

    def listar_activos(self):

        return db.obtener_repartidores()

    def listar_modelos(self):

        return db.obtener_repartidores_modelo()

    def obtener_por_id(self, repartidor_id):

        return db.obtener_repartidor(repartidor_id)

    def crear(self, *args, **kwargs):

        return db.insertar_repartidor(*args, **kwargs)

    def actualizar(self, *args, **kwargs):

        return db.actualizar_repartidor(*args, **kwargs)

    def desactivar(self, repartidor_id):

        return db.eliminar_repartidor(repartidor_id)

    def guardar_ciudades_autorizadas(self, repartidor_id, ciudades):

        return db.guardar_repartidor_ciudades(repartidor_id, ciudades)

    def obtener_ciudades_autorizadas(self, repartidor_id):

        return db.obtener_repartidor_ciudades(repartidor_id)

    def guardar_restaurantes_autorizados(self, repartidor_id, restaurantes):

        return db.guardar_repartidor_restaurantes_autorizados(
            repartidor_id,
            restaurantes
        )

    def obtener_restaurantes_autorizados(self, repartidor_id):

        return db.obtener_repartidor_restaurantes_autorizados(repartidor_id)
