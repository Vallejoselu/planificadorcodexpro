from services.planning_models import PuntuacionConfig, PuntuacionCandidato
from services.rules.candidatos import coste_desplazamiento, puntuacion_preferencia


def puntuacion_solucion(
    repartidor,
    restaurante,
    dia,
    turno,
    config=None,
    devolver_detalle=False
):

    config = config or PuntuacionConfig()
    horas_turno = turno["horas"]
    horas_despues = repartidor["horas_asignadas"] + horas_turno
    maximo = max(1, repartidor["maximo_horas"])
    carga_relativa = horas_despues / maximo

    complementarias_despues = max(
        0,
        horas_despues - repartidor["horas_contratadas"]
    )
    diferencia_turnos = calcular_diferencia_turnos(repartidor, turno)
    preferencia = puntuacion_preferencia(
        repartidor,
        restaurante,
        turno
    )
    desplazamiento = coste_desplazamiento(
        repartidor,
        restaurante,
        dia
    )
    horas_pendientes = max(
        0,
        repartidor["horas_contratadas"] - repartidor["horas_asignadas"]
    )
    detalle = {
        "restaurante_principal": prioridad_restaurante_principal(
            repartidor,
            restaurante
        ),
        "restaurante_autorizado": prioridad_restaurante_autorizado(
            repartidor,
            restaurante
        ),
        "ciudad_principal": prioridad_ciudad_principal(
            repartidor,
            restaurante
        ),
        "ciudad_autorizada": prioridad_ciudad_autorizada(
            repartidor,
            restaurante
        ),
        "apoyo_flexible": 0 if repartidor.get("apoyo_flexible") else 1,
        "preferencia": -preferencia,
        "horas_pendientes": -horas_pendientes,
        "carga_relativa": carga_relativa,
        "horas_complementarias": complementarias_despues,
        "desplazamiento": desplazamiento,
        "diferencia_turnos": diferencia_turnos,
        "horas_despues": horas_despues
    }
    valores = (
        detalle["restaurante_principal"] * config.peso_restaurante_principal,
        detalle["restaurante_autorizado"] * config.peso_restaurante_autorizado,
        detalle["ciudad_principal"] * config.peso_ciudad_principal,
        detalle["ciudad_autorizada"] * config.peso_ciudad_autorizada,
        detalle["apoyo_flexible"] * config.peso_apoyo_flexible,
        detalle["preferencia"] * config.peso_preferencia,
        detalle["horas_pendientes"] * config.peso_horas_pendientes,
        detalle["carga_relativa"] * config.peso_carga_relativa,
        detalle["horas_complementarias"] * config.peso_horas_complementarias,
        detalle["desplazamiento"] * config.peso_desplazamiento,
        detalle["diferencia_turnos"] * config.peso_diferencia_turnos,
        detalle["horas_despues"] * config.peso_horas_despues
    )

    if devolver_detalle:

        return PuntuacionCandidato(valores, detalle)

    return valores


def calcular_diferencia_turnos(repartidor, turno):

    comidas = repartidor["turnos_comida"]
    cenas = repartidor["turnos_noche"]

    if turno["nombre"] == "comida":

        comidas += 1

    elif turno["nombre"] == "noche":

        cenas += 1

    return abs(comidas - cenas)


def prioridad_restaurante_principal(repartidor, restaurante):

    principal = repartidor.get("restaurante_principal_id")

    if principal and str(principal) == str(restaurante.get("id")):

        return 0

    return 1


def prioridad_restaurante_autorizado(repartidor, restaurante):

    if prioridad_restaurante_principal(repartidor, restaurante) == 0:

        return 0

    if str(restaurante.get("id")) in {
        str(restaurante_id)
        for restaurante_id in repartidor.get("restaurantes_autorizados", [])
    }:

        return 0

    return 1


def prioridad_ciudad_principal(repartidor, restaurante):

    principal = repartidor.get("ciudad_principal_id")

    if principal and str(principal) == str(restaurante.get("ciudad_id")):

        return 0

    return 1


def prioridad_ciudad_autorizada(repartidor, restaurante):

    if prioridad_ciudad_principal(repartidor, restaurante) == 0:

        return 0

    if str(restaurante.get("ciudad_id")) in {
        str(ciudad_id)
        for ciudad_id in repartidor.get("ciudades_autorizadas", [])
    }:

        return 0

    return 1
