import database.database as db


class AusenciasRepository:

    def insertar_descanso(self, repartidor_id, dia_inicio, dia_fin):

        return db.insertar_descanso(repartidor_id, dia_inicio, dia_fin)

    def desactivar_descanso(self, repartidor_id):

        return db.desactivar_descanso(repartidor_id)

    def obtener_descansos_invalidos(self):

        return db.obtener_descansos_invalidos()

    def insertar_disponibilidad(self, repartidor_id, disponibilidad):

        return db.insertar_disponibilidad(repartidor_id, disponibilidad)

    def insertar_vacacion(
        self,
        repartidor_id,
        fecha_inicio,
        fecha_fin,
        observaciones="",
        activo=1
    ):

        return db.insertar_vacacion(
            repartidor_id,
            fecha_inicio,
            fecha_fin,
            observaciones,
            activo
        )

    def insertar_baja(
        self,
        repartidor_id,
        fecha_inicio,
        fecha_fin=None,
        observaciones="",
        activa=1
    ):

        return db.insertar_baja(
            repartidor_id,
            fecha_inicio,
            fecha_fin,
            observaciones,
            activa
        )
