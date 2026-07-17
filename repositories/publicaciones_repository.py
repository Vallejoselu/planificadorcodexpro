import database.database as db


class PublicacionesRepository:

    def obtener(self, fecha_inicio_semana):

        return db.obtener_publicacion_cuadrante(fecha_inicio_semana)

    def guardar(self, fecha_inicio_semana, estado, resumen=""):

        return db.guardar_publicacion_cuadrante(
            fecha_inicio_semana,
            estado,
            resumen
        )

    def listar(self, limite=100):

        return db.listar_publicaciones_cuadrante(limite)
