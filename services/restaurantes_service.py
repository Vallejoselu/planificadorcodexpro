from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository


class RestaurantesService:

    def __init__(
        self,
        restaurantes_repository=None,
        repartidores_repository=None
    ):

        self.restaurantes_repository = (
            restaurantes_repository or RestaurantesRepository()
        )
        self.repartidores_repository = (
            repartidores_repository or RepartidoresRepository()
        )

    def listar_todos(self):

        return self.restaurantes_repository.listar_todos()

    def listar_tabla(self):

        nombres_repartidores = self.obtener_nombres_repartidores()
        datos = []

        for restaurante in self.restaurantes_repository.listar_todos():

            repartidores_fijos = (
                self.restaurantes_repository.obtener_repartidores_fijos(
                    restaurante[0]
                )
            )
            datos.append({
                "restaurante": restaurante,
                "repartidores_fijos": repartidores_fijos,
                "repartidores_fijos_texto": ", ".join([
                    nombres_repartidores.get(id_repartidor, "")
                    for id_repartidor in repartidores_fijos
                ])
            })

        return datos

    def obtener_nombres_repartidores(self):

        nombres = {}

        for repartidor in self.repartidores_repository.listar_activos():

            nombres[repartidor[0]] = repartidor[1]

        return nombres

    def obtener_por_id(self, restaurante_id):

        return self.restaurantes_repository.obtener_por_id(restaurante_id)

    def obtener_repartidores_fijos(self, restaurante_id):

        return self.restaurantes_repository.obtener_repartidores_fijos(
            restaurante_id
        )

    def desactivar(self, restaurante_id):

        return self.restaurantes_repository.desactivar(restaurante_id)
