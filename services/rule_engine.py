from datetime import date, datetime

from services.constraints import DESCANSOS_VALIDOS, DIAS


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


def puede_trabajar(repartidor, restaurante, dia, turno, fecha):

    if dia in repartidor["descanso"]:

        return False

    if esta_ausente(repartidor, dia, fecha):

        return False

    if not esta_disponible(repartidor, dia, turno["nombre"]):

        return False

    if (dia, turno["nombre"]) in repartidor["_turnos_asignados"]:

        return False

    if not repartidor.get("doble_turno", 1):

        if dia in repartidor["_dias_asignados"]:

            return False

    if turno["nombre"] == "noche":

        if not repartidor.get("puede_hasta_la_una", 1):

            return False

    restaurante_fijo = repartidor.get("restaurante_fijo")

    if restaurante_fijo:

        if str(restaurante_fijo) not in (
            str(restaurante.get("id")),
            restaurante.get("nombre", "")
        ):

            return False

    if repartidor["horas_asignadas"] + turno["horas"] > repartidor["maximo_horas"]:

        return False

    return True


def esta_ausente(repartidor, dia, fecha):

    for rango in repartidor.get("vacaciones", []):

        if rango_contiene(rango, dia, fecha):

            return True

    for rango in repartidor.get("bajas", []):

        if rango_contiene(rango, dia, fecha):

            return True

    return False


def rango_contiene(rango, dia, fecha):

    inicio = rango.get("inicio")
    fin = rango.get("fin")

    if inicio in DIAS or fin in DIAS:

        return dia_en_rango(dia, inicio, fin)

    inicio_fecha = parsear_fecha(inicio)
    fin_fecha = parsear_fecha(fin) or inicio_fecha

    if not fecha or not inicio_fecha or not fin_fecha:

        return False

    return inicio_fecha <= fecha <= fin_fecha


def dia_en_rango(dia, inicio, fin):

    if inicio not in DIAS:

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


def esta_disponible(repartidor, dia, turno):

    disponibilidad = repartidor.get("disponibilidad") or {}

    if not disponibilidad:

        return True

    if isinstance(disponibilidad, (list, tuple, set)):

        return dia in disponibilidad

    valor = disponibilidad.get(dia)

    if valor is None:

        return False

    if isinstance(valor, bool):

        return valor

    if isinstance(valor, str):

        valor_normalizado = valor.strip().lower()

        if valor_normalizado == "no disponible":

            return False

        if turno is None:

            return True

        if valor_normalizado == "ambos":

            return True

        if valor_normalizado == "comidas":

            return turno == "comida"

        if valor_normalizado == "cenas":

            return turno in ("noche", "cena")

    if turno is None:

        return bool(valor)

    return turno in valor


def prioridad_repartidor(repartidor, restaurante, turno):

    if turno["nombre"] == "comida":

        prioridad = repartidor.get("prioridad_comida", 50)

    elif restaurante.get("zona") == "Grela":

        prioridad = repartidor.get("prioridad_grela", 50)

    else:

        prioridad = repartidor.get("prioridad_noche", 50)

    if repartidor.get("zona") == restaurante.get("zona"):

        prioridad += 10

    if repartidor.get("restaurante_fijo"):

        prioridad += 20

    return prioridad


def puntuacion_preferencia(repartidor, restaurante, turno):

    puntuacion = prioridad_repartidor(
        repartidor,
        restaurante,
        turno
    )

    for preferencia in repartidor.get("preferencias", []):

        if not preferencia_aplica(preferencia, restaurante, turno):

            continue

        if isinstance(preferencia, dict):

            puntuacion += int(preferencia.get("prioridad", 50))

        else:

            puntuacion += 50

    return puntuacion


def preferencia_aplica(preferencia, restaurante, turno):

    if isinstance(preferencia, dict):

        restaurante_id = preferencia.get("restaurante_id")
        restaurante_nombre = preferencia.get("restaurante")
        zona = preferencia.get("zona")
        turno_preferido = preferencia.get("turno")

        if restaurante_id and str(restaurante_id) != str(restaurante.get("id")):

            return False

        if restaurante_nombre and restaurante_nombre != restaurante.get("nombre"):

            return False

        if zona and zona != restaurante.get("zona"):

            return False

        if turno_preferido and turno_preferido != turno["nombre"]:

            return False

        return True

    if isinstance(preferencia, (list, tuple, set)):

        return (
            restaurante.get("id") in preferencia
            or restaurante.get("nombre") in preferencia
            or restaurante.get("zona") in preferencia
        )

    return str(preferencia) in (
        str(restaurante.get("id")),
        restaurante.get("nombre", ""),
        restaurante.get("zona", "")
    )


def coste_desplazamiento(repartidor, restaurante, dia):

    restaurante_anterior = repartidor["_restaurante_por_dia"].get(dia)
    zona_anterior = repartidor["_zona_por_dia"].get(dia)

    if restaurante_anterior is None:

        return 0

    if str(restaurante_anterior) == str(restaurante.get("id")):

        return 0

    if zona_anterior and zona_anterior == restaurante.get("zona"):

        return 1

    return 3


def parsear_fecha(valor):

    if isinstance(valor, date):

        return valor

    if isinstance(valor, datetime):

        return valor.date()

    if not valor:

        return None

    try:

        return datetime.strptime(str(valor), "%Y-%m-%d").date()

    except ValueError:

        return None
