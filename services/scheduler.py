from datetime import timedelta

from services.constraints import (
    DIAS,
    HORAS_CONTRATO,
    MAX_HORAS_SEMANALES,
    TURNOS
)
from services.rule_engine import (
    asegurar_descanso_consecutivo,
    categoria_turno,
    coste_desplazamiento,
    descanso_es_consecutivo,
    dias_no_disponibles,
    intervalo_turno,
    motivo_no_puede_trabajar,
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
    bajas=None,
    ciudades=None,
    restaurante_turnos=None,
    demandas=None
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
        "fechas": fechas,
        "ciudades": normalizar_ciudades(ciudades),
        "restaurante_turnos": normalizar_restaurante_turnos(
            restaurante_turnos
        ),
        "demandas": normalizar_demandas(demandas)
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

                minimo = minimo_repartidores(restaurante, turno)
                cubiertos = 0

                while cubiertos < minimo:

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
                        cubiertos += 1

                    else:

                        incidencias.append(
                            crear_incidencia_cobertura(
                                repartidores,
                                restaurante,
                                dia,
                                turno,
                                fecha,
                                minimo,
                                cubiertos
                            )
                        )
                        break

    incidencias.extend(
        incidencias_horas_pendientes(repartidores)
    )

    return {
        "horario": horario,
        "resumen": crear_resumen(repartidores),
        "incidencias": incidencias
    }


def construir_planificacion_multiciudad(datos):

    repartidores = datos["repartidores"]
    restaurantes = datos["restaurantes"]
    turnos = datos["restaurante_turnos"]
    demandas = datos["demandas"]
    fechas = datos["fechas"]
    ciudades = datos["ciudades"]
    horario = crear_horario_demanda(restaurantes, turnos, demandas, fechas)
    incidencias = incidencias_descansos_invalidos(repartidores)
    hay_demanda_requerida = False

    for dia in DIAS:

        fecha = fechas.get(dia)
        slots = slots_demanda(restaurantes, turnos, demandas, dia, fecha)
        hay_demanda_requerida = hay_demanda_requerida or bool(slots)

        for slot in slots:

            cubiertos = 0

            while cubiertos < slot["necesarios"]:

                repartidor = buscar_repartidor(
                    repartidores,
                    slot["restaurante"],
                    dia,
                    slot["turno"],
                    fecha
                )

                if not repartidor:

                    incidencias.append(
                        crear_incidencia_demanda(
                            repartidores,
                            slot,
                            dia,
                            fecha,
                            cubiertos
                        )
                    )
                    break

                asignacion = crear_asignacion(
                    repartidor,
                    slot["restaurante"],
                    slot["turno"]
                )
                asignacion["ciudad_id"] = slot["restaurante"].get(
                    "ciudad_id"
                )
                asignacion["ciudad"] = slot["restaurante"].get("ciudad")
                asignacion["turno_restaurante_id"] = slot["turno"].get("id")
                asignacion["hora_inicio"] = slot["turno"].get("hora_inicio")
                asignacion["hora_fin"] = slot["turno"].get("hora_fin")
                asignacion["cruza_medianoche"] = slot["turno"].get(
                    "cruza_medianoche",
                    0
                )

                horario[dia][slot["turno"]["clave"]].append(asignacion)
                registrar_asignacion(
                    repartidor,
                    slot["restaurante"],
                    slot["turno"],
                    dia
                )
                cubiertos += 1

    if hay_demanda_requerida:

        incidencias.extend(
            incidencias_horas_pendientes(repartidores)
        )

    return {
        "horario": horario,
        "ciudades": crear_vista_ciudades(
            ciudades,
            restaurantes,
            horario
        ),
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
    repartidor["_horas_por_dia"] = {}
    repartidor["_restaurante_por_dia"] = {}
    repartidor["_zona_por_dia"] = {}
    repartidor["_intervalos_asignados"] = []


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
    repartidor["_horas_por_dia"][dia] = (
        repartidor["_horas_por_dia"].get(dia, 0)
        + turno["horas"]
    )
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
    intervalo = intervalo_turno(dia, turno)

    if intervalo:

        repartidor["_intervalos_asignados"].append(intervalo)


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

        if len(repartidor) > 15:

            datos["ciudad_principal_id"] = repartidor[15]
            datos["restaurante_principal_id"] = repartidor[16]
            datos["apoyo_flexible"] = repartidor[17]
            datos["horas_complementarias"] = repartidor[18]
            datos["max_horas_diarias"] = repartidor[19]
            datos["max_dias_consecutivos"] = repartidor[20]
            datos["ciudades_autorizadas"] = repartidor[21]
            datos["restaurantes_autorizados"] = repartidor[22]

    horas = int(datos.get("horas", 0) or 0)
    horas_complementarias = int(datos.get("horas_complementarias", 0) or 0)

    if horas not in HORAS_CONTRATO:

        horas = min(horas, MAX_HORAS_SEMANALES)

    datos["horas_contratadas"] = horas
    datos["maximo_horas"] = min(
        MAX_HORAS_SEMANALES,
        horas + horas_complementarias
    )
    datos["max_horas_diarias"] = float(
        datos.get("max_horas_diarias", 10) or 0
    )
    datos["max_dias_consecutivos"] = int(
        datos.get("max_dias_consecutivos", 5) or 0
    )

    datos.setdefault("disponibilidad", {})
    datos.setdefault("restaurante_fijo", None)
    datos.setdefault("preferencias", [])
    datos.setdefault("ciudades_autorizadas", [])
    datos.setdefault("restaurantes_autorizados", [])
    datos.setdefault("apoyo_flexible", 0)
    datos.setdefault("ciudad_principal_id", None)
    datos.setdefault("restaurante_principal_id", None)
    datos["vacaciones"] = [
        normalizar_rango(rango)
        for rango in datos.get("vacaciones", [])
    ]
    datos["bajas"] = [
        normalizar_rango(rango)
        for rango in datos.get("bajas", [])
    ]

    return datos


def minimo_repartidores(restaurante, turno):

    for clave in (
        "min_repartidores",
        "minimo_repartidores",
        "minimo"
    ):

        if turno.get(clave):

            return max(1, int(turno[clave]))

    cobertura = restaurante.get("minimos_por_turno", {})

    if turno["nombre"] in cobertura:

        return max(1, int(cobertura[turno["nombre"]]))

    for clave in (
        "min_repartidores",
        "minimo_repartidores",
        "minimo"
    ):

        if restaurante.get(clave):

            return max(1, int(restaurante[clave]))

    return 1


def slots_demanda(restaurantes, turnos, demandas, dia, fecha):

    slots = []
    restaurantes_por_id = {
        restaurante["id"]: restaurante
        for restaurante in restaurantes
    }
    fecha_iso = fecha.isoformat() if fecha else None

    for turno in turnos:

        restaurante = restaurantes_por_id.get(turno["restaurante_id"])

        if not restaurante:

            continue

        demanda = demanda_aplicable(
            demandas,
            restaurante["id"],
            turno["id"],
            dia,
            fecha_iso
        )

        if demanda is None:

            continue

        necesarios = int(demanda.get("repartidores_necesarios", 0) or 0)

        if necesarios <= 0:

            continue

        slots.append({
            "restaurante": restaurante,
            "turno": turno,
            "necesarios": necesarios,
            "demanda": demanda
        })

    return sorted(
        slots,
        key=lambda slot: contar_candidatos(
            [],
            slot["restaurante"],
            dia,
            slot["turno"],
            fecha
        )
    )


def demanda_aplicable(demandas, restaurante_id, turno_id, dia, fecha_iso):

    por_fecha = None
    por_dia = None

    for demanda in demandas:

        if demanda["restaurante_id"] != restaurante_id:

            continue

        if demanda["turno_restaurante_id"] != turno_id:

            continue

        if not demanda.get("activo", 1):

            continue

        if fecha_iso and demanda.get("fecha") == fecha_iso:

            por_fecha = demanda

        elif demanda.get("dia_semana") == dia:

            por_dia = demanda

    return por_fecha if por_fecha is not None else por_dia


def crear_horario_demanda(restaurantes, turnos, demandas, fechas):

    horario = {}

    for dia in DIAS:

        fecha = fechas.get(dia)
        horario[dia] = {}

        for slot in slots_demanda(restaurantes, turnos, demandas, dia, fecha):

            horario[dia].setdefault(slot["turno"]["clave"], [])

    return horario


def crear_incidencia_demanda(repartidores, slot, dia, fecha, cubiertos):

    faltan = slot["necesarios"] - cubiertos
    restaurante = slot["restaurante"]
    turno = slot["turno"]
    motivo = regla_incumplida_principal(
        repartidores,
        restaurante,
        dia,
        turno,
        fecha
    )

    return {
        "ciudad_id": restaurante.get("ciudad_id"),
        "ciudad": restaurante.get("ciudad"),
        "dia": dia,
        "fecha": fecha.isoformat() if fecha else None,
        "turno": turno["nombre"],
        "turno_restaurante_id": turno.get("id"),
        "horario": (
            f"{turno.get('hora_inicio', '')}-{turno.get('hora_fin', '')}"
        ),
        "restaurante_id": restaurante.get("id"),
        "restaurante": restaurante["nombre"],
        "necesarios": slot["necesarios"],
        "asignados": cubiertos,
        "faltan": faltan,
        "motivo": (
            f"Faltan {faltan} repartidores. "
            f"Regla incumplida: {motivo}."
        ),
        "advertencia": True,
        "regla": "cobertura requerida por demanda"
    }


def crear_incidencia_cobertura(
    repartidores,
    restaurante,
    dia,
    turno,
    fecha,
    minimo,
    cubiertos
):

    return {
        "dia": dia,
        "turno": turno["nombre"],
        "restaurante": restaurante["nombre"],
        "motivo": (
            "No se cumple el minimo de repartidores por turno "
            f"({cubiertos}/{minimo}). "
            f"Regla incumplida: {regla_incumplida_principal(repartidores, restaurante, dia, turno, fecha)}."
        ),
        "advertencia": True,
        "regla": "minimo de repartidores por turno"
    }


def regla_incumplida_principal(repartidores, restaurante, dia, turno, fecha):

    motivos = {}

    for repartidor in repartidores:

        motivo = motivo_no_puede_trabajar(
            repartidor,
            restaurante,
            dia,
            turno,
            fecha
        )

        if not motivo:

            continue

        motivos[motivo] = motivos.get(motivo, 0) + 1

    if not motivos:

        return "sin candidatos disponibles"

    return sorted(
        motivos.items(),
        key=lambda item: (-item[1], item[0])
    )[0][0]


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

            if len(restaurante) > 9:

                datos["ciudad_id"] = restaurante[9]
                datos["ciudad"] = restaurante[10]

        resultado.append(datos)

    return resultado


def normalizar_ciudades(ciudades):

    resultado = []

    for ciudad in ciudades or []:

        if isinstance(ciudad, dict):

            resultado.append(dict(ciudad))

        else:

            resultado.append({
                "id": ciudad[0],
                "nombre": ciudad[1],
                "activo": ciudad[2]
            })

    return resultado


def normalizar_restaurante_turnos(turnos):

    resultado = []

    for turno in turnos or []:

        if isinstance(turno, dict):

            datos = dict(turno)

        else:

            datos = {
                "id": turno[0],
                "restaurante_id": turno[1],
                "nombre": turno[2],
                "hora_inicio": turno[3],
                "hora_fin": turno[4],
                "cruza_medianoche": turno[5],
                "duracion": turno[6],
                "activo": turno[7]
            }

        datos["horas"] = float(datos.get("duracion", datos.get("horas", 0)))
        datos["clave"] = clave_turno_restaurante(datos)
        resultado.append(datos)

    return [
        turno
        for turno in resultado
        if turno.get("activo", 1)
    ]


def normalizar_demandas(demandas):

    resultado = []

    for demanda in demandas or []:

        if isinstance(demanda, dict):

            datos = dict(demanda)

        else:

            datos = {
                "id": demanda[0],
                "restaurante_id": demanda[1],
                "turno_restaurante_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            }

        resultado.append(datos)

    return resultado


def clave_turno_restaurante(turno):

    return (
        f"restaurante_{turno['restaurante_id']}_"
        f"turno_{turno['id']}"
    )


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

    horas_pendientes = max(
        0,
        repartidor["horas_contratadas"] - repartidor["horas_asignadas"]
    )

    return (
        prioridad_restaurante_principal(repartidor, restaurante),
        prioridad_restaurante_autorizado(repartidor, restaurante),
        prioridad_ciudad_principal(repartidor, restaurante),
        prioridad_ciudad_autorizada(repartidor, restaurante),
        0 if repartidor.get("apoyo_flexible") else 1,
        -preferencia,
        -horas_pendientes,
        carga_relativa,
        complementarias_despues,
        desplazamiento,
        diferencia_turnos,
        horas_despues
    )


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


def registrar_tipo_turno(repartidor, turno):

    categoria = categoria_turno(turno)

    if categoria == "comida":

        repartidor["turnos_comida"] += 1

    elif categoria == "noche":

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


def crear_vista_ciudades(ciudades, restaurantes, horario):

    ciudades_por_id = {
        ciudad["id"]: {
            "id": ciudad["id"],
            "nombre": ciudad["nombre"],
            "restaurantes": {}
        }
        for ciudad in ciudades
    }

    for restaurante in restaurantes:

        ciudad_id = restaurante.get("ciudad_id")

        if ciudad_id not in ciudades_por_id:

            ciudades_por_id[ciudad_id] = {
                "id": ciudad_id,
                "nombre": restaurante.get("ciudad", ""),
                "restaurantes": {}
            }

        ciudades_por_id[ciudad_id]["restaurantes"][restaurante["id"]] = {
            "id": restaurante["id"],
            "nombre": restaurante["nombre"],
            "dias": {
                dia: {}
                for dia in DIAS
            }
        }

    for dia, turnos_dia in horario.items():

        for nombre_turno, asignaciones in turnos_dia.items():

            for asignacion in asignaciones:

                ciudad = ciudades_por_id.get(asignacion.get("ciudad_id"))

                if not ciudad:

                    continue

                restaurante = ciudad["restaurantes"].get(
                    asignacion["restaurante_id"]
                )

                if not restaurante:

                    continue

                restaurante["dias"][dia].setdefault(
                    nombre_turno,
                    []
                ).append(asignacion)

    return ciudades_por_id
