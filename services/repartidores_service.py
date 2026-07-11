from repositories.repartidores_repository import RepartidoresRepository
from services.descansos import descanso_es_valido
from services.rules.descansos import dias_no_disponibles, tiene_dias_consecutivos


class RepartidoresService:

    def __init__(self, repartidores_repository=None):

        self.repartidores_repository = (
            repartidores_repository or RepartidoresRepository()
        )

    def listar_activos(self):

        return self.repartidores_repository.listar_activos()

    def obtener_por_id(self, repartidor_id):

        return self.repartidores_repository.obtener_por_id(repartidor_id)

    def desactivar(self, repartidor_id):

        return self.repartidores_repository.desactivar(repartidor_id)

    def formatear_descanso(self, repartidor):

        if not repartidor[9] or not repartidor[10]:

            no_laborables = dias_no_disponibles({
                "disponibilidad": repartidor[11] if len(repartidor) > 11 else {}
            })

            if tiene_dias_consecutivos(no_laborables):

                return "No necesario por disponibilidad semanal"

            return "Pendiente de configurar"

        descanso = f"{repartidor[9]} - {repartidor[10]}"

        if not descanso_es_valido(repartidor[9], repartidor[10]):

            return descanso + " (no valido: corregir manualmente)"

        return descanso

    def formatear_disponibilidad(self, disponibilidad):

        if not disponibilidad:

            return ""

        etiquetas = []

        for dia, turnos in disponibilidad.items():

            if "comida" in turnos and "noche" in turnos:

                valor = "ambos"

            elif "comida" in turnos:

                valor = "comidas"

            elif "noche" in turnos:

                valor = "cenas"

            else:

                valor = "no"

            etiquetas.append(f"{dia}: {valor}")

        return " | ".join(etiquetas)
