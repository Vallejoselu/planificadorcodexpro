import database.database as db


class DemandasZonaRepository:

    def listar_zonas(self):

        return db.obtener_zonas_restaurantes()

    def listar(self):

        return db.obtener_demanda_zona()

    def guardar(self, demandas):

        return db.guardar_demanda_zona(demandas)
