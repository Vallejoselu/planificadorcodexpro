from database.schema import DESCANSOS_VALIDOS


def descanso_es_valido(dia_inicio, dia_fin):

    return (dia_inicio, dia_fin) in DESCANSOS_VALIDOS


def siguiente_descanso_valido(dia_inicio):

    for inicio, fin in DESCANSOS_VALIDOS:

        if inicio == dia_inicio:

            return fin

    return DESCANSOS_VALIDOS[0][1]
