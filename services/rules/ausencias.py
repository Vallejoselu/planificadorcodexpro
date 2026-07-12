from services.constraints import DIAS
from services.rules.disponibilidad import parsear_fecha


def esta_ausente(repartidor, dia, fecha):

    return (
        esta_ausente_por_tipo(repartidor, "vacaciones", fecha, dia)
        or esta_ausente_por_tipo(repartidor, "bajas", fecha, dia)
    )


def esta_ausente_por_tipo(repartidor, tipo, fecha, dia=None):

    if not fecha and not dia:

        return False

    for rango in repartidor.get(tipo, []):

        if rango_contiene(rango, dia, fecha):

            return True

    return False


def rango_contiene(rango, dia, fecha):

    if dia and rango.get("dia") == dia:

        return True

    inicio = (
        rango.get("fecha_inicio")
        or rango.get("inicio")
    )
    fin = (
        rango.get("fecha_fin")
        or rango.get("fin")
        or inicio
    )

    if inicio in DIAS or fin in DIAS:

        return dia_en_rango(dia, inicio, fin)

    inicio_fecha = parsear_fecha(inicio)
    fin_fecha = parsear_fecha(fin) or inicio_fecha

    if not fecha or not inicio_fecha or not fin_fecha:

        return False

    return inicio_fecha <= fecha <= fin_fecha


def dia_en_rango(dia, inicio, fin):

    if not dia or inicio not in DIAS:

        return False

    if fin not in DIAS:

        fin = inicio

    posicion = DIAS.index(inicio)

    while True:

        dia_actual = DIAS[posicion]

        if dia_actual == dia:

            return True

        if dia_actual == fin:

            return False

        posicion = (posicion + 1) % len(DIAS)
