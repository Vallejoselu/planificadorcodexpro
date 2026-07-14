from repositories.repartidores_repository import RepartidoresRepository
from services.descansos import descanso_es_valido, siguiente_descanso_valido
from services.importacion_repartidores import ImportadorRepartidores
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

    def importar_desde_archivo(self, ruta):

        return ImportadorRepartidores(
            self.repartidores_repository
        ).importar(ruta)

    def siguiente_descanso_valido(self, dia_inicio):

        return siguiente_descanso_valido(dia_inicio)

    def estado_descanso_disponibilidad(self, disponibilidad):

        no_laborables = dias_no_disponibles({
            "disponibilidad": disponibilidad
        })
        descanso_cubierto = tiene_dias_consecutivos(no_laborables)

        return {
            "dias_no_laborables": no_laborables,
            "texto_dias_no_laborables": (
                ", ".join(no_laborables)
                if no_laborables
                else "Ninguno"
            ),
            "descanso_cubierto": descanso_cubierto,
            "explicacion": (
                "La disponibilidad semanal ya aporta dos dias consecutivos sin trabajo."
                if descanso_cubierto
                else "Hace falta configurar descanso adicional."
            )
        }

    def descanso_cubierto_por_disponibilidad(self, disponibilidad):

        return self.estado_descanso_disponibilidad(
            disponibilidad
        )["descanso_cubierto"]

    def validar_descanso_no_necesario(self, disponibilidad):

        if not self.descanso_cubierto_por_disponibilidad(disponibilidad):

            raise ValueError("Configura un descanso adicional valido.")

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
