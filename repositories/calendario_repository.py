import database.database as db


class CalendarioRepository:

    def listar_semana(self, fecha_inicio_semana=None):

        return db.obtener_calendario_semanal(fecha_inicio_semana)

    def listar_semana_modelos(self, fecha_inicio_semana=None):

        return db.obtener_calendario_semanal_modelo(fecha_inicio_semana)

    def guardar_turno(
        self,
        dia,
        turno_id,
        restaurante_id,
        repartidor_id=None,
        fecha_inicio_semana=None
    ):

        return db.guardar_turno_calendario(
            dia,
            turno_id,
            restaurante_id,
            repartidor_id,
            fecha_inicio_semana
        )

    def eliminar_turno(
        self,
        dia,
        turno_id,
        restaurante_id=None,
        fecha_inicio_semana=None
    ):

        return db.eliminar_turno_calendario(
            dia,
            turno_id,
            restaurante_id,
            fecha_inicio_semana
        )

    def eliminar_semana(self, fecha_inicio_semana):

        return db.eliminar_calendario_semana(fecha_inicio_semana)

    def semana_tiene_datos(self, fecha_inicio_semana):

        return db.semana_tiene_calendario(fecha_inicio_semana)

    def listar_semanas(self):

        return db.listar_semanas_calendario()

    def reemplazar_semana(self, fecha_inicio_semana, asignaciones):

        return db.reemplazar_calendario_semana(
            fecha_inicio_semana,
            asignaciones
        )
