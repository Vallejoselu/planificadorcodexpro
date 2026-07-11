from services.scheduler import construir_planificacion, preparar_datos


class PlanningEngine:

    def generar(
        self,
        repartidores,
        restaurantes=None,
        turnos=None,
        fecha_inicio=None,
        vacaciones=None,
        bajas=None
    ):

        datos = preparar_datos(
            repartidores,
            restaurantes,
            turnos,
            fecha_inicio,
            vacaciones,
            bajas
        )

        return construir_planificacion(datos)


def generar_horarios(
    repartidores,
    restaurantes=None,
    turnos=None,
    fecha_inicio=None,
    vacaciones=None,
    bajas=None
):

    return PlanningEngine().generar(
        repartidores,
        restaurantes,
        turnos,
        fecha_inicio,
        vacaciones,
        bajas
    )
