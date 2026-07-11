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

    return motivo_no_puede_trabajar(
        repartidor,
        restaurante,
        dia,
        turno,
        fecha
    ) is None


def motivo_no_puede_trabajar(repartidor, restaurante, dia, turno, fecha):

    if dia in repartidor["descanso"]:

        return "descanso consecutivo"

    if esta_ausente(repartidor, dia, fecha):

        return "ausencia, vacaciones o baja"

    if not esta_disponible(repartidor, dia, turno):

        return "disponibilidad"

    if solapa_con_asignacion(repartidor, dia, turno):

        return "solapamiento horario"

    if (
        not turno_tiene_horario(turno)
        and (dia, turno["nombre"]) in repartidor["_turnos_asignados"]
    ):

        return "solapamiento de turno"

    if not repartidor.get("doble_turno", 1):

        if dia in repartidor["_dias_asignados"]:

            return "no permite doble turno"

    if turno["nombre"] == "noche":

        if not repartidor.get("puede_hasta_la_una", 1):

            return "no puede hacer ese horario"

    if horario_no_permitido(repartidor, dia, turno):

        return "no puede hacer ese horario"

    if not autorizado_para_restaurante(repartidor, restaurante):

        return "restaurante no autorizado"

    if not autorizado_para_ciudad(repartidor, restaurante):

        return "ciudad no autorizada"

    restaurante_fijo = repartidor.get("restaurante_fijo")

    if restaurante_fijo:

        if str(restaurante_fijo) not in (
            str(restaurante.get("id")),
            restaurante.get("nombre", "")
        ):

            return "preferencia obligatoria de local"

    if repartidor["horas_asignadas"] + turno["horas"] > repartidor["maximo_horas"]:

        return "horas contratadas y complementarias"

    if excede_horas_diarias(repartidor, dia, turno):

        return "maximo de horas diarias"

    if excede_dias_consecutivos(repartidor, dia):

        return "maximo de dias consecutivos"

    return None


def autorizado_para_restaurante(repartidor, restaurante):

    restaurante_id = restaurante.get("id")

    if restaurante_id is None:

        return True

    if repartidor.get("apoyo_flexible"):

        return True

    principal = repartidor.get("restaurante_principal_id")

    if principal and str(principal) == str(restaurante_id):

        return True

    autorizados = repartidor.get("restaurantes_autorizados") or []

    if not autorizados and not principal:

        return True

    return str(restaurante_id) in {
        str(autorizado)
        for autorizado in autorizados
    }


def autorizado_para_ciudad(repartidor, restaurante):

    ciudad_id = restaurante.get("ciudad_id")

    if ciudad_id is None:

        return True

    if repartidor.get("apoyo_flexible"):

        return True

    principal = repartidor.get("ciudad_principal_id")

    if principal and str(principal) == str(ciudad_id):

        return True

    autorizadas = repartidor.get("ciudades_autorizadas") or []

    if not autorizadas and not principal:

        return True

    return str(ciudad_id) in {
        str(autorizada)
        for autorizada in autorizadas
    }


def horario_no_permitido(repartidor, dia, turno):

    restricciones = []

    for clave in (
        "no_puede_turnos",
        "turnos_no_permitidos",
        "horarios_no_permitidos",
        "restricciones_horarias"
    ):

        valor = repartidor.get(clave)

        if not valor:

            continue

        if isinstance(valor, (list, tuple, set)):

            restricciones.extend(valor)

        else:

            restricciones.append(valor)

    for restriccion in restricciones:

        if restriccion_aplica(restriccion, dia, turno):

            return True

    return False


def restriccion_aplica(restriccion, dia, turno):

    if isinstance(restriccion, dict):

        dia_restringido = restriccion.get("dia")
        turno_restringido = (
            restriccion.get("turno")
            or restriccion.get("nombre")
        )
        hora_inicio = restriccion.get("hora_inicio")
        hora_fin = restriccion.get("hora_fin")

        if dia_restringido and dia_restringido != dia:

            return False

        if turno_restringido and turno_restringido != turno["nombre"]:

            return False

        if hora_inicio and hora_inicio != turno.get("hora_inicio"):

            return False

        if hora_fin and hora_fin != turno.get("hora_fin"):

            return False

        return True

    texto = str(restriccion).strip().lower()

    if texto in (
        turno["nombre"],
        f"{dia}:{turno['nombre']}",
        f"{dia}-{turno['nombre']}",
        f"{turno.get('hora_inicio', '')}-{turno.get('hora_fin', '')}"
    ):

        return True

    return False


def excede_horas_diarias(repartidor, dia, turno):

    maximo = repartidor.get("max_horas_diarias")

    if not maximo:

        return False

    horas_dia = repartidor["_horas_por_dia"].get(dia, 0)

    return horas_dia + turno["horas"] > maximo


def excede_dias_consecutivos(repartidor, dia):

    maximo = repartidor.get("max_dias_consecutivos")

    if not maximo:

        return False

    dias = set(repartidor["_dias_asignados"])
    dias.add(dia)

    racha = 0

    for dia_semana in DIAS:

        if dia_semana in dias:

            racha += 1

            if racha > maximo:

                return True

        else:

            racha = 0

    return False


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

    nombre_turno = nombre_turno_disponibilidad(turno)
    categoria = categoria_turno(turno)

    if isinstance(valor, str):

        valor_normalizado = valor.strip().lower()

        if valor_normalizado == "no disponible":

            return False

        if turno is None:

            return True

        if valor_normalizado == "ambos":

            return True

        if valor_normalizado == "comidas":

            return categoria == "comida"

        if valor_normalizado == "cenas":

            return categoria in ("noche", "cena")

    if turno is None:

        return bool(valor)

    return (
        nombre_turno in valor
        or categoria in valor
    )


def nombre_turno_disponibilidad(turno):

    if turno is None:

        return None

    if isinstance(turno, dict):

        return turno.get("nombre")

    return turno


def categoria_turno(turno):

    nombre = nombre_turno_disponibilidad(turno)

    if not nombre:

        return None

    texto = str(nombre).strip().lower()

    if "comida" in texto:

        return "comida"

    if "cena" in texto or "noche" in texto:

        return "noche"

    return texto


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


def turno_tiene_horario(turno):

    return bool(turno.get("hora_inicio") and turno.get("hora_fin"))


def solapa_con_asignacion(repartidor, dia, turno):

    intervalo = intervalo_turno(dia, turno)

    if not intervalo:

        return False

    inicio, fin = intervalo

    for inicio_existente, fin_existente in repartidor.get(
        "_intervalos_asignados",
        []
    ):

        if max(inicio, inicio_existente) < min(fin, fin_existente):

            return True

    return False


def intervalo_turno(dia, turno):

    if not turno_tiene_horario(turno):

        return None

    if dia not in DIAS:

        return None

    inicio = minutos_hora(turno.get("hora_inicio"))
    fin = minutos_hora(turno.get("hora_fin"))

    if inicio is None or fin is None:

        return None

    base = DIAS.index(dia) * 24 * 60

    if turno.get("cruza_medianoche") or fin <= inicio:

        fin += 24 * 60

    return base + inicio, base + fin


def minutos_hora(valor):

    try:

        hora, minuto = str(valor).split(":", 1)
        return int(hora) * 60 + int(minuto)

    except (TypeError, ValueError):

        return None


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
