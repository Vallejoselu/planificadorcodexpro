import database.database as db


class TurnosRepository:

    def listar_activos(self):

        return [
            turno
            for turno in db.obtener_turnos()
            if turno[7]
        ]

    def listar_todos(self):

        return db.obtener_turnos()

    def listar_modelos(self):

        return db.obtener_turnos_modelo()

    def obtener_por_id(self, turno_id):

        return db.obtener_turno(turno_id)

    def crear(self, *args, **kwargs):

        return db.insertar_turno(*args, **kwargs)

    def actualizar(self, *args, **kwargs):

        return db.actualizar_turno(*args, **kwargs)

    def desactivar(self, turno_id):

        return db.eliminar_turno(turno_id)

    def obtener_o_crear_para_restaurante(self, turno_restaurante_id):

        return db.obtener_o_crear_turno_calendario_restaurante(
            turno_restaurante_id
        )
