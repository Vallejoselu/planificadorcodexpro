from services.scheduler import (
    construir_planificacion,
    construir_planificacion_multiciudad,
    preparar_datos
)


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

    def generar_multiciudad(
        self,
        repartidores,
        ciudades,
        restaurantes,
        restaurante_turnos,
        demandas,
        fecha_inicio=None,
        vacaciones=None,
        bajas=None
    ):

        datos = preparar_datos(
            repartidores,
            restaurantes,
            fecha_inicio=fecha_inicio,
            vacaciones=vacaciones,
            bajas=bajas,
            ciudades=ciudades,
            restaurante_turnos=restaurante_turnos,
            demandas=demandas
        )

        return construir_planificacion_multiciudad(datos)


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
