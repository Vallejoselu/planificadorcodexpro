from services.rules.ausencias import esta_ausente, esta_ausente_por_tipo
from services.rules.disponibilidad import (
    categoria_turno,
    esta_disponible,
    intervalos_solapados,
    intervalo_turno,
    normalizar_texto,
    turno_tiene_horario
)
from services.rules.descansos import descanso_valido
from services.rules.horas import (
    calcular_horas_pendientes,
    horas_por_repartidor,
    repartidores_activos
)


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

    horas_despues = repartidor["horas_asignadas"] + turno["horas"]

    if horas_despues > repartidor["horas_contratadas"]:

        if not repartidor.get("permite_horas_complementarias", False):

            return "horas complementarias no permitidas"

        if horas_despues > repartidor["maximo_horas"]:

            return "limite de horas complementarias"

    if horas_despues > repartidor["maximo_horas"]:

        return "horas contratadas y complementarias"

    if excede_horas_diarias(repartidor, dia, turno):

        return "maximo de horas diarias"

    if excede_dias_consecutivos(repartidor, dia):

        return "maximo de dias consecutivos"

    return None


def buscar_candidatos(contexto, dia, turno, restaurante=None, fecha=None):

    horas = horas_por_repartidor(contexto)
    candidatos = []
    rechazos = {}

    for repartidor in repartidores_activos(contexto):

        motivos = motivos_rechazo_asistente(
            contexto,
            repartidor,
            dia,
            turno,
            restaurante,
            fecha,
            horas
        )

        if motivos:

            for motivo in motivos:

                rechazos[motivo] = rechazos.get(motivo, 0) + 1

            continue

        realizadas = horas.get(repartidor["id"], 0)
        pendientes = calcular_horas_pendientes(repartidor, horas)
        candidatos.append({
            "repartidor": repartidor,
            "realizadas": realizadas,
            "pendientes": pendientes,
            "preferencia": puntuacion_preferencia_asistente(
                repartidor,
                turno,
                restaurante
            ),
            "consecutivos": turnos_consecutivos(contexto, repartidor, dia)
        })

    candidatos.sort(key=lambda candidato: (
        candidato["realizadas"],
        -candidato["pendientes"],
        -candidato["preferencia"],
        candidato["consecutivos"],
        candidato["repartidor"]["nombre"]
    ))

    return candidatos, rechazos


def motivos_rechazo_asistente(
    contexto,
    repartidor,
    dia,
    turno,
    restaurante,
    fecha,
    horas
):

    motivos = []

    if not repartidor.get("activo", 1):

        motivos.append("no estan activos")

    if descanso_valido(repartidor.get("descanso", [])) and dia in repartidor.get("descanso", []):

        motivos.append("estan descansando")

    if esta_ausente_por_tipo(repartidor, "vacaciones", fecha, dia):

        motivos.append("estan de vacaciones")

    if esta_ausente_por_tipo(repartidor, "bajas", fecha, dia):

        motivos.append("estan de baja")

    if not esta_disponible(repartidor, dia, turno):

        motivos.append("no tienen disponibilidad")

    if solapa_turno(contexto, repartidor, dia, turno):

        motivos.append("tienen otro turno solapado")

    if horas.get(repartidor["id"], 0) + turno["duracion"] > repartidor["horas"]:

        motivos.append("superarian sus horas contratadas")

    if not cumple_restaurante_o_zona(repartidor, restaurante):

        motivos.append("no cumplen restaurante o zona")

    if es_turno_noche(turno) and not repartidor.get("puede_hasta_la_una", 1):

        motivos.append("no pueden trabajar hasta la una")

    return motivos


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

    from services.constraints import DIAS

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


def solapa_turno(contexto, repartidor, dia, turno):

    inicio = turno.get("hora_inicio")
    fin = turno.get("hora_fin")

    if not inicio or not fin:

        return False

    for asignacion in contexto.get("asignaciones_repartidor", []):

        if asignacion.get("repartidor_id") != repartidor["id"]:

            continue

        if asignacion.get("dia") != dia:

            continue

        asignado = turno_por_id(contexto, asignacion.get("turno_id"))
        asignado_inicio = asignacion.get("hora_inicio") or asignado.get("hora_inicio")
        asignado_fin = asignacion.get("hora_fin") or asignado.get("hora_fin")

        if intervalos_solapados(inicio, fin, asignado_inicio, asignado_fin):

            return True

    return False


def turno_por_id(contexto, turno_id):

    for turno in contexto["turnos"]:

        if turno["id"] == turno_id:

            return turno

    return {}


def cumple_restaurante_o_zona(repartidor, restaurante):

    if not restaurante:

        return True

    fijos = repartidor.get("restaurantes_fijos") or []

    if fijos:

        return restaurante["id"] in fijos

    zona_repartidor = repartidor.get("zona")
    zona_restaurante = restaurante.get("zona")

    return not zona_repartidor or not zona_restaurante or zona_repartidor == zona_restaurante


def puntuacion_preferencia_asistente(repartidor, turno, restaurante):

    puntuacion = 0

    for preferencia in repartidor.get("preferencias", []):

        if restaurante:

            if preferencia.get("restaurante_id") == restaurante["id"]:

                puntuacion += int(preferencia.get("prioridad", 50))

            if preferencia.get("zona") and preferencia.get("zona") == restaurante.get("zona"):

                puntuacion += int(preferencia.get("prioridad", 50))

        if preferencia.get("turno") and preferencia.get("turno") == turno.get("nombre"):

            puntuacion += int(preferencia.get("prioridad", 50))

    return puntuacion


def turnos_consecutivos(contexto, repartidor, dia):

    return len([
        asignacion
        for asignacion in contexto.get("asignaciones_repartidor", [])
        if asignacion.get("repartidor_id") == repartidor["id"]
        and asignacion.get("dia") == dia
    ])


def es_turno_noche(turno):

    texto = normalizar_texto(
        f"{turno.get('tipo', '')} {turno.get('nombre', '')}"
    )

    return "cena" in texto or "noche" in texto
