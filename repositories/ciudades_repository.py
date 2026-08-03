import database.database as db
from database.schema import CIUDAD_SIN_CIUDAD


class CiudadesRepository:

    def listar_todas(self):

        return self._sin_ciudad_tecnica(db.obtener_ciudades())

    def listar_activas(self):

        return self._sin_ciudad_tecnica(db.obtener_ciudades(solo_activas=True))

    def obtener_por_id(self, ciudad_id):

        return db.obtener_ciudad(ciudad_id)

    def crear(self, nombre, activo=1):

        return db.insertar_ciudad(nombre, activo)

    def actualizar(self, ciudad_id, nombre, activo=1):

        return db.actualizar_ciudad(ciudad_id, nombre, activo)

    def _sin_ciudad_tecnica(self, ciudades):

        return [
            ciudad
            for ciudad in ciudades
            if ciudad[1] != CIUDAD_SIN_CIUDAD
        ]
