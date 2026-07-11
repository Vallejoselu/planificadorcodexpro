from services.constraints import DESCANSOS_VALIDOS, DIAS
from services.rules.disponibilidad import esta_disponible


DESCANSO_NO_NECESARIO = []


def asegurar_descanso_consecutivo(repartidor):

    descanso = repartidor.get("descanso")

    if descanso and descanso_es_consecutivo(descanso):

        return list(descanso)

    if disponibilidad_aporta_descanso(repartidor):

        return list(DESCANSO_NO_NECESARIO)

    return calcular_descanso(repartidor)


def descanso_es_consecutivo(descanso):

    if not descanso or len(descanso) != 2:

        return False

    return list(descanso) in DESCANSOS_VALIDOS


def descanso_valido(descanso):

    if not descanso or len(descanso) != 2:

        return False

    return (
        list(descanso) in DESCANSOS_VALIDOS
        or tuple(descanso) in DESCANSOS_VALIDOS
    )


def calcular_descanso(repartidor):

    if disponibilidad_aporta_descanso(repartidor):

        return list(DESCANSO_NO_NECESARIO)

    disponibilidad = repartidor.get("disponibilidad", {})
    mejor_descanso = list(DESCANSOS_VALIDOS[0])
    mejor_puntuacion = -1

    for descanso in DESCANSOS_VALIDOS:

        puntuacion = 0

        for dia_descanso in descanso:

            if not esta_disponible(repartidor, dia_descanso, None):

                puntuacion += 2

            elif disponibilidad:

                puntuacion += 1

        if puntuacion > mejor_puntuacion:

            mejor_puntuacion = puntuacion
            mejor_descanso = list(descanso)

    return mejor_descanso


def disponibilidad_aporta_descanso(repartidor):

    return tiene_dias_consecutivos(
        dias_no_disponibles(repartidor)
    )


def dias_no_disponibles(repartidor):

    disponibilidad = repartidor.get("disponibilidad") or {}

    if not disponibilidad:

        return []

    return [
        dia
        for dia in DIAS
        if not esta_disponible(repartidor, dia, None)
    ]


def tiene_dias_consecutivos(dias):

    dias = set(dias or [])

    for indice, dia in enumerate(DIAS):

        siguiente = DIAS[(indice + 1) % len(DIAS)]

        if dia in dias and siguiente in dias:

            return True

    return False
