import database.database as db


class RestaurantesRepository:

    def listar_activos(self):

        return [
            restaurante
            for restaurante in db.obtener_restaurantes()
            if restaurante[6]
        ]

    def listar_todos(self):

        return db.obtener_restaurantes()

    def listar_modelos(self):

        return db.obtener_restaurantes_modelo()

    def obtener_por_id(self, restaurante_id):

        return db.obtener_restaurante(restaurante_id)

    def crear(self, *args, **kwargs):

        return db.insertar_restaurante(*args, **kwargs)

    def actualizar(self, *args, **kwargs):

        return db.actualizar_restaurante(*args, **kwargs)

    def desactivar(self, restaurante_id):

        return db.eliminar_restaurante(restaurante_id)

    def obtener_repartidores_fijos(self, restaurante_id):

        return db.obtener_repartidores_fijos(restaurante_id)

    def guardar_repartidores_fijos(self, restaurante_id, repartidores):

        return db.guardar_repartidores_fijos(restaurante_id, repartidores)

    def listar_turnos(self, restaurante_id):

        return db.obtener_restaurante_turnos(restaurante_id)

    def guardar_turnos(self, restaurante_id, turnos):

        return db.guardar_restaurante_turnos(restaurante_id, turnos)

    def listar_demanda(self, restaurante_id):

        return db.obtener_demanda_restaurante(restaurante_id)

    def guardar_demanda(self, restaurante_id, demandas):

        return db.guardar_demanda_restaurante(restaurante_id, demandas)
