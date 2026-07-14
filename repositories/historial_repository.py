import database.database as db


class HistorialRepository:

    def registrar(
        self,
        accion,
        entidad="",
        detalle="",
        fecha_inicio_semana=None
    ):

        return db.registrar_historial_accion(
            accion,
            entidad,
            detalle,
            fecha_inicio_semana
        )

    def listar(self, limite=100, fecha_inicio_semana=None):

        return db.obtener_historial_acciones(limite, fecha_inicio_semana)
