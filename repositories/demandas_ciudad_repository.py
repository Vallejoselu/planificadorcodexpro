import database.database as db


class DemandasCiudadRepository:

    def listar(self):

        return db.obtener_demanda_ciudad()

    def guardar(self, demandas):

        return db.guardar_demanda_ciudad(demandas)
