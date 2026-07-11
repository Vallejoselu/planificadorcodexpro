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
