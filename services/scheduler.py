from datetime import timedelta

from services.constraints import (
    DIAS,
    HORAS_CONTRATO,
    MAX_HORAS_SEMANALES,
    TURNOS
)
from services.rule_engine import (
    asegurar_descanso_consecutivo,
    coste_desplazamiento,
    descanso_es_consecutivo,
    dias_no_disponibles,
    parsear_fecha,
    puede_trabajar,
    puntuacion_preferencia
)


def preparar_datos(
    repartidores,
    restaurantes=None,
    turnos=None,
    fecha_inicio=None,
    vacaciones=None,
    bajas=None
):

    restaurantes = normalizar_restaurantes(restaurantes)
    turnos = turnos if turnos else TURNOS
    fechas = crear_fechas_semana(fecha_inicio)
    vacaciones = normalizar_ausencias(vacaciones)
    bajas = normalizar_ausencias(bajas)

    repartidores = [
        normalizar_repartidor(repartidor)
        for repartidor in repartidores
    ]

    for repartidor in repartidores:

        id_repartidor = repartidor["id"]

        if id_repartidor in vacaciones:

            repartidor["vacaciones"] = vacaciones[id_repartidor]

        if id_repartidor in bajas:

            repartidor["bajas"] = bajas[id_repartidor]

        preparar_estado_repartidor(repartidor)

    return {
        "repartidores": repartidores,
        "restaurantes": restaurantes,
        "turnos": turnos,
        "fechas": fechas
    }


def construir_planificacion(datos):

    repartidores = datos["repartidores"]
    restaurantes = datos["restaurantes"]
    turnos = datos["turnos"]
    fechas = datos["fechas"]
    horario = crear_horario_base(restaurantes, turnos)
    incidencias = incidencias_descansos_invalidos(repartidores)

    for dia in DIAS:

        fecha = fechas.get(dia)

        for turno in turnos:

            restaurantes_ordenados = sorted(
                restaurantes,
                key=lambda restaurante: contar_candidatos(
                    repartidores,
                    restaurante,
                    dia,
                    turno,
                    fecha
                )
            )

            for restaurante in restaurantes_ordenados:

                repartidor = buscar_repartidor(
                    repartidores,
                    restaurante,
                    dia,
                    turno,
                    fecha
                )

                if repartidor:

                    asignacion = crear_asignacion(
                        repartidor,
                        restaurante,
                        turno
                    )
                    horario[dia][turno["nombre"]].append(asignacion)
                    registrar_asignacion(
                        repartidor,
                        restaurante,
                        turno,
                        dia
                    )

                else:

                    incidencias.append({
                        "dia": dia,
                        "turno": turno["nombre"],
                        "restaurante": restaurante["nombre"],
                        "motivo": "No hay repartidor disponible"
                    })

    incidencias.extend(
        incidencias_horas_pendientes(repartidores)
    )

    return {
        "horario": horario,
        "resumen": crear_resumen(repartidores),
        "incidencias": incidencias
    }


def preparar_estado_repartidor(repartidor):

    descanso_original = repartidor.get("descanso")
    repartidor["descanso"] = asegurar_descanso_consecutivo(
        repartidor
    )
    repartidor["descanso_invalido"] = bool(
        descanso_original
        and not descanso_es_consecutivo(descanso_original)
    )
    repartidor["horas_asignadas"] = 0
    repartidor["horas_complementarias"] = 0
    repartidor["turnos_comida"] = 0
    repartidor["turnos_noche"] = 0
    repartidor["desplazamientos"] = 0
    repartidor["_dias_asignados"] = set()
    repartidor["_turnos_asignados"] = set()
    repartidor["_restaurante_por_dia"] = {}
    repartidor["_zona_por_dia"] = {}


def incidencias_descansos_invalidos(repartidores):

    incidencias = []

    for repartidor in repartidores:

        if repartidor.get("descanso_invalido"):

            incidencias.append({
                "dia": "",
                "turno": "",
                "restaurante": "",
                "motivo": (
                    f"Descanso antiguo no valido para {repartidor['nombre']}. "
                    "Debe corregirse manualmente."
                )
            })

    return incidencias


def incidencias_horas_pendientes(repartidores):

    incidencias = []

    for repartidor in repartidores:

        if repartidor["horas_asignadas"] >= repartidor["horas_contratadas"]:

            continue

        if not dias_no_disponibles(repartidor):

            continue

        pendientes = (
            repartidor["horas_contratadas"]
            - repartidor["horas_asignadas"]
        )
        incidencias.append({
            "dia": "",
            "turno": "",
            "restaurante": "",
            "motivo": (
                f"{repartidor['nombre']} tiene {pendientes:g} horas "
                "pendientes por falta de disponibilidad."
            )
        })

    return incidencias


def crear_asignacion(repartidor, restaurante, turno):

    return {
        "repartidor_id": repartidor["id"],
        "repartidor": repartidor["nombre"],
        "restaurante_id": restaurante["id"],
        "restaurante": restaurante["nombre"],
        "turno": turno["nombre"],
        "horas": turno["horas"]
    }


def registrar_asignacion(repartidor, restaurante, turno, dia):

    repartidor["horas_asignadas"] += turno["horas"]
    repartidor["horas_complementarias"] = max(
        0,
        repartidor["horas_asignadas"]
        - repartidor["horas_contratadas"]
    )
    registrar_tipo_turno(repartidor, turno)
    registrar_restaurante_dia(
        repartidor,
        restaurante,
        dia
    )
    repartidor["_dias_asignados"].add(dia)
    repartidor["_turnos_asignados"].add(
        (dia, turno["nombre"])
    )


def crear_resumen(repartidores):

    resumen = []

    for repartidor in repartidores:

        resumen.append({
            "id": repartidor["id"],
            "nombre": repartidor["nombre"],
            "horas": repartidor["horas_asignadas"],
            "maximo": repartidor["maximo_horas"],
            "descanso": repartidor["descanso"],
            "horas_complementarias": repartidor["horas_complementarias"],
            "comidas": repartidor["turnos_comida"],
            "cenas": repartidor["turnos_noche"],
            "desplazamientos": repartidor["desplazamientos"]
        })

    return resumen


def crear_horario_base(restaurantes, turnos):

    horario = {}

    for dia in DIAS:

        horario[dia] = {}

        for turno in turnos:

            horario[dia][turno["nombre"]] = []

    return horario


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
            "prioridad_grela": repartidor[8]
        }

        if len(repartidor) > 10 and repartidor[9] and repartidor[10]:

            datos["descanso"] = [
                repartidor[9],
                repartidor[10]
            ]

        if len(repartidor) > 11 and repartidor[11]:

            datos["disponibilidad"] = repartidor[11]

        if len(repartidor) > 12 and repartidor[12]:

            datos["vacaciones"] = repartidor[12]

        if len(repartidor) > 13 and repartidor[13]:

            datos["bajas"] = repartidor[13]

        if len(repartidor) > 14 and repartidor[14]:

            datos["preferencias"] = repartidor[14]

    horas = int(datos.get("horas", 0) or 0)
    horas_complementarias = int(datos.get("horas_complementarias", 0) or 0)

    if horas not in HORAS_CONTRATO:

        horas = min(horas, MAX_HORAS_SEMANALES)

    datos["horas_contratadas"] = horas
    datos["maximo_horas"] = min(
        MAX_HORAS_SEMANALES,
        horas + horas_complementarias
    )

    datos.setdefault("disponibilidad", {})
    datos.setdefault("restaurante_fijo", None)
    datos.setdefault("preferencias", [])
    datos["vacaciones"] = [
        normalizar_rango(rango)
        for rango in datos.get("vacaciones", [])
    ]
    datos["bajas"] = [
        normalizar_rango(rango)
        for rango in datos.get("bajas", [])
    ]

    return datos


def normalizar_restaurantes(restaurantes):

    if not restaurantes:

        return [
            {
                "id": 0,
                "nombre": "Restaurante",
                "zona": ""
            }
        ]

    resultado = []

    for restaurante in restaurantes:

        if isinstance(restaurante, dict):

            datos = dict(restaurante)

        else:

            datos = {
                "id": restaurante[0],
                "nombre": restaurante[1],
                "direccion": restaurante[2],
                "zona": restaurante[3],
                "telefono": restaurante[4],
                "prioridad": restaurante[5]
            }

        resultado.append(datos)

    return resultado


def crear_fechas_semana(fecha_inicio):

    if not fecha_inicio:

        return {}

    inicio = parsear_fecha(fecha_inicio)

    if not inicio:

        return {}

    fechas = {}

    for posicion, dia in enumerate(DIAS):

        fechas[dia] = inicio + timedelta(days=posicion)

    return fechas


def normalizar_ausencias(ausencias):

    resultado = {}

    if not ausencias:

        return resultado

    if isinstance(ausencias, dict):

        for id_repartidor, rangos in ausencias.items():

            resultado[int(id_repartidor)] = [
                normalizar_rango(rango)
                for rango in rangos
            ]

        return resultado

    for ausencia in ausencias:

        if isinstance(ausencia, dict):

            if ausencia.get("activa", ausencia.get("activo", 1)) == 0:

                continue

            id_repartidor = ausencia.get("repartidor_id")
            inicio = ausencia.get("fecha_inicio")
            fin = ausencia.get("fecha_fin") or inicio

        else:

            id_repartidor = ausencia[0]
            inicio = ausencia[1]
            fin = ausencia[2] if len(ausencia) > 2 and ausencia[2] else inicio

        resultado.setdefault(int(id_repartidor), []).append(
            normalizar_rango((inicio, fin))
        )

    return resultado


def normalizar_rango(rango):

    if isinstance(rango, dict):

        inicio = rango.get("fecha_inicio") or rango.get("inicio")
        fin = rango.get("fecha_fin") or rango.get("fin") or inicio

    elif isinstance(rango, (list, tuple)):

        inicio = rango[0]
        fin = rango[1] if len(rango) > 1 and rango[1] else inicio

    else:

        inicio = rango
        fin = rango

    return {
        "inicio": inicio,
        "fin": fin
    }


def contar_candidatos(repartidores, restaurante, dia, turno, fecha):

    return len([
        repartidor
        for repartidor in repartidores
        if puede_trabajar(repartidor, restaurante, dia, turno, fecha)
    ])


def buscar_repartidor(repartidores, restaurante, dia, turno, fecha):

    candidatos = []

    for repartidor in repartidores:

        if not puede_trabajar(repartidor, restaurante, dia, turno, fecha):

            continue

        candidatos.append((
            puntuacion_solucion(
                repartidor,
                restaurante,
                dia,
                turno
            ),
            repartidor["nombre"],
            repartidor
        ))

    if not candidatos:

        return None

    candidatos.sort(key=lambda candidato: (
        candidato[0],
        candidato[1]
    ))

    return candidatos[0][2]


def puntuacion_solucion(repartidor, restaurante, dia, turno):

    horas_turno = turno["horas"]
    horas_despues = repartidor["horas_asignadas"] + horas_turno
    maximo = max(1, repartidor["maximo_horas"])
    carga_relativa = horas_despues / maximo

    complementarias_despues = max(
        0,
        horas_despues - repartidor["horas_contratadas"]
    )

    comidas = repartidor["turnos_comida"]
    cenas = repartidor["turnos_noche"]

    if turno["nombre"] == "comida":

        comidas += 1

    elif turno["nombre"] == "noche":

        cenas += 1

    diferencia_turnos = abs(comidas - cenas)
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

    return (
        carga_relativa,
        -preferencia,
        complementarias_despues,
        desplazamiento,
        diferencia_turnos,
        horas_despues
    )


def registrar_tipo_turno(repartidor, turno):

    if turno["nombre"] == "comida":

        repartidor["turnos_comida"] += 1

    elif turno["nombre"] == "noche":

        repartidor["turnos_noche"] += 1


def registrar_restaurante_dia(repartidor, restaurante, dia):

    coste = coste_desplazamiento(
        repartidor,
        restaurante,
        dia
    )

    repartidor["desplazamientos"] += coste
    repartidor["_restaurante_por_dia"][dia] = restaurante.get("id")
    repartidor["_zona_por_dia"][dia] = restaurante.get("zona")
