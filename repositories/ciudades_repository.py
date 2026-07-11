import database.database as db


class CiudadesRepository:

    def listar_todas(self):

        return db.obtener_ciudades()

    def listar_activas(self):

        return db.obtener_ciudades(solo_activas=True)

    def obtener_por_id(self, ciudad_id):

        return db.obtener_ciudad(ciudad_id)

    def crear(self, nombre, activo=1):

        return db.insertar_ciudad(nombre, activo)

    def actualizar(self, ciudad_id, nombre, activo=1):

        return db.actualizar_ciudad(ciudad_id, nombre, activo)
