from repositories.turnos_repository import TurnosRepository


class TurnosService:

    def __init__(self, turnos_repository=None):

        self.turnos_repository = turnos_repository or TurnosRepository()

    def listar_todos(self):

        return self.turnos_repository.listar_todos()

    def obtener_por_id(self, turno_id):

        return self.turnos_repository.obtener_por_id(turno_id)

    def desactivar(self, turno_id):

        return self.turnos_repository.desactivar(turno_id)
