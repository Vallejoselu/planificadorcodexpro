import re
import unicodedata
from datetime import date, timedelta

from database.database import (
    DIAS_SEMANA,
    obtener_calendario_semanal,
    obtener_repartidores,
    obtener_repartidores_fijos,
    obtener_restaurantes,
    obtener_turnos
)
from services.rules.candidatos import (
    buscar_candidatos,
    solapa_turno
)
from services.rules.descansos import (
    descanso_valido,
    dias_no_disponibles,
    tiene_dias_consecutivos
)
from services.rules.disponibilidad import (
    esta_disponible,
    esta_disponible_dia
)
from services.rules.horas import (
    calcular_horas_pendientes as horas_pendientes,
    horas_por_repartidor,
    repartidores_activos,
    restaurantes_activos,
    turnos_activos
)


def responder(pregunta, contexto=None, fecha_referencia=None):

    texto = normalizar_texto(pregunta)

    if not texto:

        return "Escribe una pregunta para poder ayudarte."

    contexto = preparar_contexto(contexto)
    fecha_referencia = fecha_referencia or date.today()

    from services.asistente_simulacion import (
        es_pregunta_simulacion,
        responder_simulacion
    )

    if es_pregunta_simulacion(texto):

        return responder_simulacion(
            texto,
            contexto,
            fecha_referencia
        )

    intencion = detectar_intencion(texto)

    if intencion == "menos_horas":

        return responder_horas_extremo(contexto, menor=True)

    if intencion == "mas_horas":

        return responder_horas_extremo(contexto, menor=False)

    if intencion == "horas_pendientes":

        return responder_horas_pendientes(texto, contexto)

    if intencion == "descansos":

        return responder_descansos(texto, contexto, fecha_referencia)

    if intencion == "disponibilidad":

        return responder_disponibilidad(texto, contexto, fecha_referencia)

    if intencion == "contrato":

        return responder_contrato(texto, contexto)

    if intencion == "turnos_sin_cubrir":

        return responder_turnos_sin_cubrir(contexto)

    if intencion == "candidatos":

        if "sin superar" in texto and not extraer_dia(texto, fecha_referencia)[0]:

            return responder_pueden_sin_superar(contexto)

        return responder_candidatos(texto, contexto, fecha_referencia)

    return (
        "No he reconocido la pregunta. Puedes probar con: "
        "'Quien descansa el lunes?', 'Quien tiene contrato de 20 horas?' "
        "o 'Quien puede cubrir la cena del viernes?'."
    )


def normalizar_texto(texto):

    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    texto = texto.replace("¿", "").replace("?", "")
    texto = re.sub(r"\s+", " ", texto)

    return texto


def detectar_intencion(texto):

    texto = normalizar_texto(texto)

    if "sin cubrir" in texto:

        return "turnos_sin_cubrir"

    if "puede cubrir" in texto or "puede trabajar" in texto or "sin superar" in texto:

        return "candidatos"

    if "contrato" in texto:

        return "contrato"

    if "descansa" in texto or "descansan" in texto:

        return "descansos"

    if "disponible" in texto or "disponibles" in texto:

        return "disponibilidad"

    if "pendiente" in texto or "faltan" in texto or "falta" in texto:

        return "horas_pendientes"

    if "menos horas" in texto:

        return "menos_horas"

    if "mas horas" in texto:

        return "mas_horas"

    return "desconocida"


def preparar_contexto(contexto=None):

    if contexto is None:

        return cargar_contexto()

    turnos = [
        normalizar_turno(turno)
        for turno in contexto.get("turnos", [])
    ]
    calendario = [
        normalizar_calendario(asignacion)
        for asignacion in contexto.get("calendario", [])
    ]
    asignaciones = [
        normalizar_asignacion_repartidor(asignacion)
        for asignacion in contexto.get("asignaciones_repartidor", [])
    ]
    asignaciones.extend(
        asignaciones_desde_calendario(calendario, turnos)
    )

    return {
        "repartidores": [
            normalizar_repartidor(repartidor)
            for repartidor in contexto.get("repartidores", [])
        ],
        "turnos": turnos,
        "restaurantes": [
            normalizar_restaurante(restaurante)
            for restaurante in contexto.get("restaurantes", [])
        ],
        "calendario": calendario,
        "asignaciones_repartidor": asignaciones
    }


def cargar_contexto():

    restaurantes = [
        normalizar_restaurante(restaurante)
        for restaurante in obtener_restaurantes()
    ]
    fijos_por_repartidor = {}

    for restaurante in restaurantes:

        for repartidor_id in obtener_repartidores_fijos(restaurante["id"]):

            fijos_por_repartidor.setdefault(repartidor_id, []).append(
                restaurante["id"]
            )

    repartidores = []

    for repartidor in obtener_repartidores():

        datos = normalizar_repartidor(repartidor)
        datos["restaurantes_fijos"] = fijos_por_repartidor.get(
            datos["id"],
            []
        )
        repartidores.append(datos)

    turnos = [
        normalizar_turno(turno)
        for turno in obtener_turnos()
    ]
    calendario = [
        normalizar_calendario(asignacion)
        for asignacion in obtener_calendario_semanal()
    ]

    return {
        "repartidores": repartidores,
        "turnos": turnos,
        "restaurantes": restaurantes,
        "calendario": calendario,
        "asignaciones_repartidor": asignaciones_desde_calendario(
            calendario,
            turnos
        )
    }


def normalizar_repartidor(repartidor):

    if isinstance(repartidor, dict):

        datos = dict(repartidor)

    else:

        datos = {
            "id": repartidor[0],
            "nombre": repartidor[1],
            "horas": repartidor[2],
            "zona": repartidor[3],
            "doble_turno": repartidor[4],
            "puede_hasta_la_una": repartidor[5],
            "prioridad_comida": repartidor[6],
            "prioridad_noche": repartidor[7],
            "prioridad_grela": repartidor[8],
            "descanso": [
                dia
                for dia in (repartidor[9], repartidor[10])
                if dia
            ],
            "disponibilidad": repartidor[11] if len(repartidor) > 11 else {},
            "vacaciones": repartidor[12] if len(repartidor) > 12 else [],
            "bajas": repartidor[13] if len(repartidor) > 13 else [],
            "preferencias": repartidor[14] if len(repartidor) > 14 else []
        }

    datos.setdefault("descanso", [])
    datos.setdefault("disponibilidad", {})
    datos.setdefault("vacaciones", [])
    datos.setdefault("bajas", [])
    datos.setdefault("preferencias", [])
    datos.setdefault("restaurantes_fijos", [])
    datos.setdefault("activo", 1)
    datos["descanso_invalido"] = bool(
        datos.get("descanso")
        and not descanso_valido(datos.get("descanso"))
    )
    datos["horas"] = int(datos.get("horas", 0) or 0)

    return datos


def normalizar_turno(turno):

    if isinstance(turno, dict):

        datos = dict(turno)

    else:

        datos = {
            "id": turno[0],
            "tipo": turno[1],
            "nombre": turno[2],
            "hora_inicio": turno[3],
            "hora_fin": turno[4],
            "color": turno[5],
            "duracion": turno[6],
            "activo": turno[7]
        }

    datos.setdefault("activo", 1)
    datos["duracion"] = float(datos.get("duracion", 0) or 0)

    return datos


def normalizar_restaurante(restaurante):

    if isinstance(restaurante, dict):

        datos = dict(restaurante)

    else:

        datos = {
            "id": restaurante[0],
            "nombre": restaurante[1],
            "direccion": restaurante[2],
            "zona": restaurante[3],
            "telefono": restaurante[4],
            "prioridad": restaurante[5],
            "activo": restaurante[6],
            "horario_comida": restaurante[7],
            "horario_cena": restaurante[8]
        }

    datos.setdefault("activo", 1)

    return datos


def normalizar_calendario(asignacion):

    if isinstance(asignacion, dict):

        return dict(asignacion)

    return {
        "id": asignacion[0],
        "dia": asignacion[1],
        "turno_id": asignacion[2],
        "turno": asignacion[3],
        "tipo": asignacion[4],
        "color": asignacion[5],
        "restaurante_id": asignacion[6],
        "restaurante": asignacion[7],
        "zona": asignacion[8],
        "repartidor_id": asignacion[9] if len(asignacion) > 9 else None,
        "repartidor": asignacion[10] if len(asignacion) > 10 else None
    }


def asignaciones_desde_calendario(calendario, turnos):

    turnos_por_id = {
        turno["id"]: turno
        for turno in turnos
    }
    asignaciones = []

    for asignacion in calendario:

        repartidor_id = asignacion.get("repartidor_id")

        if not repartidor_id:

            continue

        turno = turnos_por_id.get(asignacion.get("turno_id"), {})

        asignaciones.append({
            "repartidor_id": repartidor_id,
            "dia": asignacion.get("dia"),
            "turno_id": asignacion.get("turno_id"),
            "restaurante_id": asignacion.get("restaurante_id"),
            "duracion": turno.get("duracion", 0),
            "hora_inicio": turno.get("hora_inicio"),
            "hora_fin": turno.get("hora_fin")
        })

    return asignaciones


def normalizar_asignacion_repartidor(asignacion):

    datos = dict(asignacion)
    datos["duracion"] = float(datos.get("duracion", 0) or 0)

    return datos


def responder_horas_extremo(contexto, menor=True):

    repartidores = repartidores_activos(contexto)

    if not repartidores:

        return "No hay repartidores activos registrados."

    horas = horas_por_repartidor(contexto)
    valor = min(horas.values()) if menor else max(horas.values())
    nombres = [
        repartidor["nombre"]
        for repartidor in repartidores
        if horas.get(repartidor["id"], 0) == valor
    ]
    tipo = "menos" if menor else "mas"
    aviso = aviso_sin_asignaciones(contexto)

    return (
        f"{', '.join(nombres)} lleva {tipo} horas esta semana: "
        f"{formatear_horas(valor)} horas registradas.{aviso}"
    )


def responder_horas_pendientes(texto, contexto):

    repartidores = repartidores_activos(contexto)

    if not repartidores:

        return "No hay repartidores activos registrados."

    horas = horas_por_repartidor(contexto)
    nombre = extraer_nombre_repartidor(texto, repartidores)

    if nombre:

        repartidor = nombre
        pendientes = horas_pendientes(repartidor, horas)

        return (
            f"A {repartidor['nombre']} le faltan "
            f"{formatear_horas(pendientes)} horas para completar "
            f"su contrato de {repartidor['horas']} horas."
            f"{aviso_sin_asignaciones(contexto)}"
        )

    pendientes = [
        (
            repartidor,
            horas_pendientes(repartidor, horas)
        )
        for repartidor in repartidores
        if horas_pendientes(repartidor, horas) > 0
    ]

    if not pendientes:

        return "No hay repartidores con horas pendientes."

    pendientes.sort(key=lambda item: (-item[1], item[0]["nombre"]))
    detalle = ", ".join(
        f"{repartidor['nombre']} ({formatear_horas(valor)} h)"
        for repartidor, valor in pendientes
    )

    return f"Tienen horas pendientes: {detalle}.{aviso_sin_asignaciones(contexto)}"


def responder_descansos(texto, contexto, fecha_referencia):

    dia, _ = extraer_dia(texto, fecha_referencia)

    if not dia:

        return "Indica el dia para consultar descansos."

    repartidores = [
        repartidor["nombre"]
        for repartidor in repartidores_activos(contexto)
        if descanso_valido(repartidor.get("descanso", []))
        and dia in repartidor.get("descanso", [])
    ]
    invalidos = descansos_invalidos(contexto)

    if not repartidores:

        respuesta = f"No hay repartidores con descanso valido el {dia}."

        if invalidos:

            respuesta += " " + mensaje_descansos_invalidos(invalidos)

        return respuesta

    respuesta = f"Descansan el {dia}: {', '.join(repartidores)}."

    if invalidos:

        respuesta += " " + mensaje_descansos_invalidos(invalidos)

    return respuesta


def responder_disponibilidad(texto, contexto, fecha_referencia):

    dia, _ = extraer_dia(texto, fecha_referencia)
    turno = extraer_turno(texto, contexto)
    nombre = extraer_nombre_repartidor(
        texto,
        repartidores_activos(contexto)
    )

    if not dia:

        if nombre:

            return responder_disponibilidad_repartidor(nombre)

        return "Indica el dia para consultar disponibilidad."

    disponibles = []

    for repartidor in repartidores_activos(contexto):

        if descanso_valido(repartidor.get("descanso", [])) and dia in repartidor.get("descanso", []):

            continue

        if turno and not esta_disponible(repartidor, dia, turno):

            continue

        if not turno and not esta_disponible_dia(repartidor, dia):

            continue

        disponibles.append(repartidor["nombre"])

    if not disponibles:

        return f"No hay repartidores disponibles el {dia}."

    etiqueta_turno = f" para {turno['nombre']}" if turno else ""

    return f"Disponibles el {dia}{etiqueta_turno}: {', '.join(disponibles)}."


def responder_disponibilidad_repartidor(repartidor):

    disponibles = [
        dia
        for dia in DIAS_SEMANA
        if esta_disponible_dia(repartidor, dia)
    ]
    no_laborables = dias_no_disponibles(repartidor)

    if tiene_dias_consecutivos(no_laborables):

        descanso = (
            "no necesita descanso adicional porque ya tiene "
            f"{', '.join(no_laborables)} sin trabajo"
        )

    elif descanso_valido(repartidor.get("descanso", [])):

        descanso = (
            "tiene descanso adicional "
            + "-".join(repartidor.get("descanso", []))
        )

    else:

        descanso = "necesita configurar descanso adicional"

    return (
        f"{repartidor['nombre']} puede trabajar de "
        f"{', '.join(disponibles) if disponibles else 'ningun dia'} "
        f"y {descanso}."
    )


def responder_contrato(texto, contexto):

    horas = extraer_horas(texto)

    if horas is None:

        return "Indica las horas del contrato que quieres consultar."

    repartidores = [
        repartidor["nombre"]
        for repartidor in repartidores_activos(contexto)
        if repartidor["horas"] == horas
    ]

    if not repartidores:

        return f"No hay repartidores activos con contrato de {horas} horas."

    return (
        f"Repartidores con contrato de {horas} horas: "
        f"{', '.join(repartidores)}."
    )


def responder_turnos_sin_cubrir(contexto):

    restaurantes = restaurantes_activos(contexto)
    turnos = turnos_activos(contexto)

    if not restaurantes or not turnos:

        return "No hay restaurantes o turnos activos suficientes para calcular turnos sin cubrir."

    cubiertos = {
        (
            asignacion.get("dia"),
            asignacion.get("turno_id"),
            asignacion.get("restaurante_id")
        )
        for asignacion in contexto["calendario"]
    }
    sin_cubrir = []

    for dia in DIAS_SEMANA:

        for turno in turnos:

            for restaurante in restaurantes:

                clave = (dia, turno["id"], restaurante["id"])

                if clave not in cubiertos:

                    sin_cubrir.append(
                        f"{dia} {turno['nombre']} en {restaurante['nombre']}"
                    )

    if not sin_cubrir:

        return "No hay turnos sin cubrir en el calendario semanal."

    primeros = sin_cubrir[:10]
    extra = ""

    if len(sin_cubrir) > len(primeros):

        extra = f" Hay {len(sin_cubrir) - len(primeros)} mas."

    return "Turnos sin cubrir: " + "; ".join(primeros) + "." + extra


def responder_candidatos(texto, contexto, fecha_referencia):

    dia, fecha = extraer_dia(texto, fecha_referencia)
    turno = extraer_turno(texto, contexto)
    restaurante = extraer_restaurante(texto, contexto)

    if not dia:

        return "Indica el dia del turno que quieres cubrir."

    if not turno:

        return "Indica el turno que quieres cubrir."

    candidatos, rechazos = buscar_candidatos(
        contexto,
        dia,
        turno,
        restaurante,
        fecha
    )

    if not candidatos:

        return "No hay repartidores disponibles. " + resumir_rechazos(rechazos)

    partes = []

    for candidato in candidatos[:5]:

        repartidor = candidato["repartidor"]
        pendientes = candidato["pendientes"]
        motivo = (
            f"{repartidor['nombre']} puede cubrir el turno porque esta disponible, "
            f"no descansa ese dia y todavia tiene "
            f"{formatear_horas(pendientes)} horas pendientes"
        )

        if restaurante:

            motivo += f" para la zona/restaurante {restaurante['nombre']}"

        partes.append(motivo + ".")

    return " ".join(partes)


def responder_pueden_sin_superar(contexto):

    horas = horas_por_repartidor(contexto)
    candidatos = []

    for repartidor in repartidores_activos(contexto):

        pendientes = horas_pendientes(repartidor, horas)

        if pendientes > 0:

            candidatos.append((repartidor, pendientes))

    if not candidatos:

        return "No hay repartidores con horas disponibles sin superar su contrato."

    candidatos.sort(key=lambda item: (
        horas.get(item[0]["id"], 0),
        -item[1],
        item[0]["nombre"]
    ))
    detalle = ", ".join(
        f"{repartidor['nombre']} ({formatear_horas(pendientes)} h pendientes)"
        for repartidor, pendientes in candidatos
    )

    return (
        "Pueden trabajar sin superar sus horas contratadas: "
        f"{detalle}.{aviso_sin_asignaciones(contexto)}"
    )


def descansos_invalidos(contexto):

    return [
        repartidor
        for repartidor in repartidores_activos(contexto)
        if repartidor.get("descanso")
        and not descanso_valido(repartidor.get("descanso"))
    ]


def mensaje_descansos_invalidos(repartidores):

    detalle = ", ".join(
        f"{repartidor['nombre']} ({' - '.join(repartidor.get('descanso', []))})"
        for repartidor in repartidores
    )

    return (
        "Configuracion no valida segun las reglas actuales: "
        f"{detalle}. Debe corregirse manualmente."
    )


def aviso_sin_asignaciones(contexto):

    if contexto.get("asignaciones_repartidor"):

        return ""

    return (
        " Aviso: el calendario actual no guarda repartidor asignado, "
        "asi que las horas por repartidor se calculan como 0."
    )


def extraer_dia(texto, fecha_referencia):

    if "manana" in texto:

        fecha = fecha_referencia + timedelta(days=1)

        return dia_desde_fecha(fecha), fecha

    if "hoy" in texto:

        return dia_desde_fecha(fecha_referencia), fecha_referencia

    for dia in DIAS_SEMANA:

        if normalizar_texto(dia) in texto:

            return dia, None

    return None, None


def dia_desde_fecha(fecha):

    return DIAS_SEMANA[fecha.weekday()]


def extraer_turno(texto, contexto):

    turnos = turnos_activos(contexto)

    for turno in turnos:

        nombre = normalizar_texto(turno["nombre"])
        tipo = normalizar_texto(turno.get("tipo", ""))

        if nombre and nombre in texto:

            return turno

        if tipo and tipo in texto:

            return turno

    if "cena" in texto or "noche" in texto:

        return buscar_turno_por_clave(turnos, ("cena", "noche"))

    if "comida" in texto:

        return buscar_turno_por_clave(turnos, ("comida",))

    return None


def buscar_turno_por_clave(turnos, claves):

    for turno in turnos:

        texto = normalizar_texto(
            f"{turno.get('tipo', '')} {turno.get('nombre', '')}"
        )

        if any(clave in texto for clave in claves):

            return turno

    return None


def extraer_restaurante(texto, contexto):

    for restaurante in restaurantes_activos(contexto):

        nombre = normalizar_texto(restaurante["nombre"])

        if nombre and nombre in texto:

            return restaurante

    return None


def extraer_nombre_repartidor(texto, repartidores):

    for repartidor in repartidores:

        if normalizar_texto(repartidor["nombre"]) in texto:

            return repartidor

    return None


def extraer_horas(texto):

    coincidencia = re.search(r"(\d+)\s*horas?", texto)

    if not coincidencia:

        return None

    return int(coincidencia.group(1))


def resumir_rechazos(rechazos):

    if not rechazos:

        return "No hay datos suficientes para encontrar candidatos."

    partes = [
        f"{cantidad} {motivo}"
        for motivo, cantidad in sorted(
            rechazos.items(),
            key=lambda item: (-item[1], item[0])
        )
    ]

    return "Motivos principales: " + ", ".join(partes) + "."


def formatear_horas(valor):

    valor = float(valor or 0)

    if valor.is_integer():

        return str(int(valor))

    return str(round(valor, 2))
