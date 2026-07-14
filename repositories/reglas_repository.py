import database.database as db


class ReglasRepository:

    def listar_configuracion(self):

        return db.obtener_reglas_configuracion()

    def guardar(self, clave, valor, activo=1):

        return db.guardar_regla_configuracion(clave, valor, activo)

    def eliminar(self, claves=None):

        return db.eliminar_reglas_configuracion(claves)
