from copy import deepcopy
from datetime import date

from database.schema import DIAS_SEMANA
from services.asistente_horarios import (
    buscar_candidatos,
    extraer_dia,
    extraer_nombre_repartidor,
    extraer_restaurante,
    extraer_turno,
    formatear_horas,
    horas_por_repartidor,
    horas_pendientes,
    normalizar_texto,
    preparar_contexto,
    repartidores_activos,
    restaurantes_activos,
    turnos_activos
)
from services.rules.candidatos import motivos_rechazo_asistente


def es_pregunta_simulacion(texto):

    texto = normalizar_texto(texto)

    return (
        "que ocurre si" in texto
        or "sustituir" in texto
        or "sustituto" in texto
        or "sin horas complementarias" in texto
        or "adicional" in texto
        or "elimino" in texto
        or "eliminar" in texto
        or "asignar" in texto
        or "cambiar" in texto
        or "cambio" in texto
    )


def responder_simulacion(pregunta, contexto=None, fecha_referencia=None):

    texto = normalizar_texto(pregunta)
    fecha_referencia = fecha_referencia or date.today()
    contexto_original = preparar_contexto(contexto)
    contexto_simulado = deepcopy(contexto_original)

    if "vacaciones" in texto:

        return simular_vacaciones(
            texto,
            contexto_original,
            contexto_simulado,
            fecha_referencia
        )

    if "elimino" in texto or "eliminar" in texto:

        return simular_eliminar_turno(
            texto,
            contexto_original,
            contexto_simulado,
            fecha_referencia
        )

    if "cambiar" in texto or "cambio" in texto:

        return simular_cambio_repartidor(
            texto,
            contexto_original,
            contexto_simulado,
            fecha_referencia
        )

    if "asignar" in texto:

        return simular_asignacion_repartidor(
            texto,
            contexto_original,
            contexto_simulado,
            fecha_referencia
        )

    if "sustituir" in texto or "sustituto" in texto:

        return simular_sustitucion(
            texto,
            contexto_original,
            contexto_simulado,
            fecha_referencia
        )

    if "sin horas complementarias" in texto:

        return simular_cobertura_sin_complementarias(
            texto,
            contexto_original,
            fecha_referencia
        )

    if "adicional" in texto:

        return simular_repartidor_adicional(
            texto,
            contexto_original,
            fecha_referencia
        )

    return (
        "Puedo simular vacaciones, sustituciones, eliminacion de turnos, "
        "cambios de repartidor, asignaciones, cobertura sin horas "
        "complementarias o repartidores adicionales."
    )


def simular_vacaciones(texto, contexto_original, contexto_simulado, fecha_referencia):

    repartidor = extraer_nombre_repartidor(
        texto,
        repartidores_activos(contexto_simulado)
    )
    dia, fecha = extraer_dia(texto, fecha_referencia)

    if not repartidor or not dia:

        return "Indica el repartidor y el dia para simular vacaciones."

    simulado = buscar_repartidor(contexto_simulado, repartidor["id"])
    simulado.setdefault("vacaciones", []).append({
        "dia": dia,
        "fecha_inicio": fecha.isoformat() if fecha else None,
        "fecha_fin": fecha.isoformat() if fecha else None
    })

    descubiertos = turnos_descubiertos_por_repartidor(
        contexto_simulado,
        simulado,
        dia,
        fecha
    )

    return construir_respuesta_simulacion(
        f"Simulacion: {repartidor['nombre']} de vacaciones el {dia}.",
        contexto_original,
        contexto_simulado,
        descubiertos,
        "La base de datos real no se modifica."
    )


def simular_eliminar_turno(texto, contexto_original, contexto_simulado, fecha_referencia):

    repartidor = extraer_nombre_repartidor(
        texto,
        repartidores_activos(contexto_simulado)
    )
    dia, fecha = extraer_dia(texto, fecha_referencia)

    if not repartidor or not dia:

        return "Indica el repartidor y el dia del turno que quieres simular."

    eliminadas = []
    restantes = []

    for asignacion in contexto_simulado.get("asignaciones_repartidor", []):

        if asignacion.get("repartidor_id") == repartidor["id"] and asignacion.get("dia") == dia:

            eliminadas.append(asignacion)

        else:

            restantes.append(asignacion)

    contexto_simulado["asignaciones_repartidor"] = restantes

    if not eliminadas:

        return (
            f"No he encontrado turnos asignados a {repartidor['nombre']} "
            f"el {dia}. No se modifica ningun dato real."
        )

    descubiertos = [
        construir_descubierto(contexto_simulado, asignacion, fecha)
        for asignacion in eliminadas
    ]

    return construir_respuesta_simulacion(
        f"Simulacion: eliminar a {repartidor['nombre']} del turno del {dia}.",
        contexto_original,
        contexto_simulado,
        descubiertos,
        "La eliminacion es solo temporal y no se guarda."
    )


def simular_sustitucion(texto, contexto_original, contexto_simulado, fecha_referencia):

    repartidor = extraer_nombre_repartidor(
        texto,
        repartidores_activos(contexto_simulado)
    )
    dia, fecha = extraer_dia(texto, fecha_referencia)

    if not repartidor or not dia:

        return "Indica a quien quieres sustituir y en que dia."

    asignaciones = [
        asignacion
        for asignacion in contexto_simulado.get("asignaciones_repartidor", [])
        if asignacion.get("repartidor_id") == repartidor["id"]
        and asignacion.get("dia") == dia
    ]

    if not asignaciones:

        return (
            f"No he encontrado turnos de {repartidor['nombre']} el {dia}. "
            "No puedo proponer sustitutos sin un turno asignado."
        )

    contexto_sin_repartidor = deepcopy(contexto_simulado)
    contexto_sin_repartidor["asignaciones_repartidor"] = [
        asignacion
        for asignacion in contexto_simulado.get("asignaciones_repartidor", [])
        if asignacion not in asignaciones
    ]

    descubiertos = [
        construir_descubierto(contexto_sin_repartidor, asignacion, fecha)
        for asignacion in asignaciones
    ]

    return construir_respuesta_simulacion(
        f"Simulacion: sustitucion de {repartidor['nombre']} el {dia}.",
        contexto_original,
        contexto_sin_repartidor,
        descubiertos,
        "La propuesta es informativa y no se guarda."
    )


def simular_asignacion_repartidor(texto, contexto_original, contexto_simulado, fecha_referencia):

    repartidor = extraer_nombre_repartidor(
        texto,
        repartidores_activos(contexto_simulado)
    )
    dia, fecha = extraer_dia(texto, fecha_referencia)
    turno = extraer_turno(texto, contexto_simulado)
    restaurante = extraer_restaurante(texto, contexto_simulado)

    if not repartidor or not dia or not turno:

        return (
            "Indica repartidor, dia y turno para simular la asignacion. "
            "Ejemplo: asignar Ana a la cena del viernes."
        )

    motivos = motivos_no_valido_para_asignacion(
        contexto_simulado,
        repartidor,
        dia,
        turno,
        restaurante,
        fecha
    )

    if motivos:

        return construir_respuesta_cambio_no_viable(
            "Simulacion: asignacion no recomendable.",
            repartidor,
            dia,
            turno,
            restaurante,
            motivos
        )

    contexto_simulado["asignaciones_repartidor"].append(
        crear_asignacion_simulada(repartidor, dia, turno, restaurante)
    )

    return construir_respuesta_simulacion(
        (
            f"Simulacion: asignar a {repartidor['nombre']} "
            f"a {descripcion_turno(dia, turno, restaurante)}."
        ),
        contexto_original,
        contexto_simulado,
        [],
        "El cambio parece viable con las reglas actuales."
    )


def simular_cambio_repartidor(texto, contexto_original, contexto_simulado, fecha_referencia):

    repartidores = extraer_repartidores_mencionados(
        texto,
        repartidores_activos(contexto_simulado)
    )
    dia, fecha = extraer_dia(texto, fecha_referencia)
    turno = extraer_turno(texto, contexto_simulado)
    restaurante = extraer_restaurante(texto, contexto_simulado)

    if len(repartidores) < 2 or not dia:

        return (
            "Indica repartidor origen, repartidor destino y dia para simular "
            "el cambio. Ejemplo: cambiar Luis por Ana el viernes cena."
        )

    origen, destino = repartidores[0], repartidores[1]
    asignaciones = asignaciones_de_repartidor(
        contexto_simulado,
        origen,
        dia,
        turno,
        restaurante
    )

    if not asignaciones:

        return (
            f"No he encontrado un turno de {origen['nombre']} el {dia} "
            "con esos filtros. No se modifica ningun dato real."
        )

    if len(asignaciones) > 1 and not turno:

        return (
            f"{origen['nombre']} tiene varios turnos el {dia}. Indica si "
            "quieres simular comida, cena o el nombre exacto del turno."
        )

    asignacion = asignaciones[0]
    turno_objetivo = buscar_turno(
        contexto_simulado,
        asignacion.get("turno_id")
    )
    restaurante_objetivo = buscar_restaurante(
        contexto_simulado,
        asignacion.get("restaurante_id")
    )
    contexto_sin_origen = deepcopy(contexto_simulado)
    contexto_sin_origen["asignaciones_repartidor"] = [
        actual
        for actual in contexto_simulado.get("asignaciones_repartidor", [])
        if not misma_asignacion(actual, asignacion)
    ]

    motivos = motivos_no_valido_para_asignacion(
        contexto_sin_origen,
        destino,
        dia,
        turno_objetivo,
        restaurante_objetivo,
        fecha
    )

    if motivos:

        return construir_respuesta_cambio_no_viable(
            (
                f"Simulacion: cambiar {origen['nombre']} por "
                f"{destino['nombre']} no es recomendable."
            ),
            destino,
            dia,
            turno_objetivo,
            restaurante_objetivo,
            motivos
        )

    nueva = dict(asignacion)
    nueva["repartidor_id"] = destino["id"]
    contexto_sin_origen["asignaciones_repartidor"].append(nueva)

    return construir_respuesta_simulacion(
        (
            f"Simulacion: cambiar {descripcion_turno(dia, turno_objetivo, restaurante_objetivo)} "
            f"de {origen['nombre']} a {destino['nombre']}."
        ),
        contexto_original,
        contexto_sin_origen,
        [],
        "El cambio parece viable con las reglas actuales."
    )


def simular_cobertura_sin_complementarias(texto, contexto_original, fecha_referencia):

    dia, fecha = extraer_dia(texto, fecha_referencia)

    if not dia:

        return "Indica el dia para simular cobertura sin horas complementarias."

    descubiertos = []

    for restaurante in restaurantes_activos(contexto_original):

        for turno in turnos_activos(contexto_original):

            candidatos, rechazos = buscar_candidatos(
                contexto_original,
                dia,
                turno,
                restaurante,
                fecha
            )

            if not candidatos:

                descubiertos.append({
                    "dia": dia,
                    "turno": turno,
                    "restaurante": restaurante,
                    "candidatos": [],
                    "rechazos": rechazos
                })

    if not descubiertos:

        return (
            f"Si, el {dia} se puede cubrir sin horas complementarias "
            "con las restricciones actuales."
        )

    return construir_respuesta_simulacion(
        f"Simulacion: cubrir el {dia} sin horas complementarias.",
        contexto_original,
        contexto_original,
        descubiertos,
        "Los turnos listados no tienen candidato valido sin superar contrato."
    )


def simular_repartidor_adicional(texto, contexto_original, fecha_referencia):

    dia, fecha = extraer_dia(texto, fecha_referencia)
    turno = extraer_turno(texto, contexto_original)
    restaurante = extraer_restaurante(texto, contexto_original)

    if not dia:

        dia = DIAS_SEMANA[0]

    if not turno:

        turnos = turnos_activos(contexto_original)
        turno = turnos[0] if turnos else None

    if not restaurante:

        restaurantes = restaurantes_activos(contexto_original)
        restaurante = restaurantes[0] if restaurantes else None

    if not turno or not restaurante:

        return "No hay turnos o restaurantes activos para simular un repartidor adicional."

    candidatos, rechazos = buscar_candidatos(
        contexto_original,
        dia,
        turno,
        restaurante,
        fecha
    )
    descubierto = {
        "dia": dia,
        "turno": turno,
        "restaurante": restaurante,
        "candidatos": candidatos,
        "rechazos": rechazos
    }

    return construir_respuesta_simulacion(
        f"Simulacion: {restaurante['nombre']} necesita un repartidor adicional.",
        contexto_original,
        contexto_original,
        [descubierto],
        "Se muestran candidatos para cubrir esa necesidad extra."
    )


def motivos_no_valido_para_asignacion(
    contexto,
    repartidor,
    dia,
    turno,
    restaurante,
    fecha
):

    if not turno:

        return ["no hay turno valido para simular"]

    return motivos_rechazo_asistente(
        contexto,
        repartidor,
        dia,
        turno,
        restaurante,
        fecha,
        horas_por_repartidor(contexto)
    )


def crear_asignacion_simulada(repartidor, dia, turno, restaurante):

    return {
        "repartidor_id": repartidor["id"],
        "dia": dia,
        "turno_id": turno.get("id"),
        "restaurante_id": restaurante.get("id") if restaurante else None,
        "duracion": turno.get("duracion", 0),
        "hora_inicio": turno.get("hora_inicio"),
        "hora_fin": turno.get("hora_fin")
    }


def asignaciones_de_repartidor(contexto, repartidor, dia, turno, restaurante):

    asignaciones = []

    for asignacion in contexto.get("asignaciones_repartidor", []):

        if asignacion.get("repartidor_id") != repartidor["id"]:

            continue

        if asignacion.get("dia") != dia:

            continue

        if turno and asignacion.get("turno_id") != turno.get("id"):

            continue

        if restaurante and asignacion.get("restaurante_id") != restaurante.get("id"):

            continue

        asignaciones.append(asignacion)

    return asignaciones


def extraer_repartidores_mencionados(texto, repartidores):

    texto_normalizado = normalizar_texto(texto)
    encontrados = []

    for repartidor in repartidores:

        nombre = normalizar_texto(repartidor.get("nombre"))
        posicion = texto_normalizado.find(nombre)

        if posicion >= 0:

            encontrados.append((posicion, repartidor))

    encontrados.sort(key=lambda item: item[0])

    return [
        repartidor
        for _, repartidor in encontrados
    ]


def construir_respuesta_cambio_no_viable(
    titulo,
    repartidor,
    dia,
    turno,
    restaurante,
    motivos
):

    return (
        f"{titulo}\n"
        f"{repartidor['nombre']} no deberia cubrir "
        f"{descripcion_turno(dia, turno, restaurante)}.\n"
        "Motivos: "
        + ", ".join(motivos)
        + ".\n\nNo se ha guardado ningun cambio."
    )


def descripcion_turno(dia, turno, restaurante):

    restaurante_nombre = (
        restaurante.get("nombre")
        if restaurante
        else "sin restaurante"
    )
    turno_nombre = turno.get("nombre", "turno") if turno else "turno"

    return f"{dia} {turno_nombre} en {restaurante_nombre}"


def misma_asignacion(primera, segunda):

    return (
        primera.get("repartidor_id") == segunda.get("repartidor_id")
        and primera.get("dia") == segunda.get("dia")
        and primera.get("turno_id") == segunda.get("turno_id")
        and primera.get("restaurante_id") == segunda.get("restaurante_id")
    )


def turnos_descubiertos_por_repartidor(contexto, repartidor, dia, fecha):

    descubiertos = []

    for asignacion in contexto.get("asignaciones_repartidor", []):

        if asignacion.get("repartidor_id") != repartidor["id"]:

            continue

        if asignacion.get("dia") != dia:

            continue

        descubiertos.append(
            construir_descubierto(contexto, asignacion, fecha)
        )

    return descubiertos


def construir_descubierto(contexto, asignacion, fecha):

    turno = buscar_turno(contexto, asignacion.get("turno_id"))
    restaurante = buscar_restaurante(contexto, asignacion.get("restaurante_id"))
    candidatos, rechazos = buscar_candidatos(
        contexto,
        asignacion.get("dia"),
        turno,
        restaurante,
        fecha
    )

    candidatos = [
        candidato
        for candidato in candidatos
        if candidato["repartidor"]["id"] != asignacion.get("repartidor_id")
    ]

    return {
        "dia": asignacion.get("dia"),
        "turno": turno,
        "restaurante": restaurante,
        "candidatos": candidatos,
        "rechazos": rechazos
    }


def construir_respuesta_simulacion(
    titulo,
    contexto_original,
    contexto_simulado,
    descubiertos,
    nota
):

    lineas = [
        titulo,
        nota,
        "",
        "Horas resultantes:",
        resumen_horas(contexto_simulado)
    ]

    if descubiertos:

        lineas.append("")
        lineas.append("Turnos que quedarian descubiertos o requieren cobertura:")

        for descubierto in descubiertos:

            lineas.extend(describir_descubierto(descubierto))

    else:

        lineas.append("")
        lineas.append("No quedarian turnos descubiertos.")

    cambios = comparar_horas(contexto_original, contexto_simulado)

    if cambios:

        lineas.append("")
        lineas.append("Cambios de horas:")
        lineas.append(cambios)

    lineas.append("")
    lineas.append(
        "No se ha guardado ningun cambio. Puedes aplicar la propuesta "
        "editando el cuadrante y asignando el primer sustituto sugerido "
        "en el turno correspondiente."
    )

    return "\n".join(lineas)


def describir_descubierto(descubierto):

    turno = descubierto.get("turno") or {}
    restaurante = descubierto.get("restaurante") or {}
    candidatos = descubierto.get("candidatos", [])
    rechazos = descubierto.get("rechazos", {})
    encabezado = (
        f"- {descubierto.get('dia')} {turno.get('nombre', 'turno')} "
        f"en {restaurante.get('nombre', 'restaurante')}"
    )
    lineas = [encabezado]

    if candidatos:

        partes = []
        primer_candidato = candidatos[0]["repartidor"]

        for candidato in candidatos[:5]:

            repartidor = candidato["repartidor"]
            pendientes = formatear_horas(candidato["pendientes"])
            partes.append(
                f"{repartidor['nombre']} valido: disponible, sin descanso, "
                f"sin solapamiento y con {pendientes} h pendientes"
            )

        lineas.append("  Sustitutos posibles: " + "; ".join(partes) + ".")
        lineas.append(
            f"  Accion sugerida: asignar a {primer_candidato['nombre']} "
            "a este turno en el cuadrante."
        )

    else:

        lineas.append("  Sin sustitutos validos.")

        if rechazos:

            motivos = ", ".join(
                f"{cantidad} {motivo}"
                for motivo, cantidad in sorted(
                    rechazos.items(),
                    key=lambda item: (-item[1], item[0])
                )
            )
            lineas.append("  Motivos: " + motivos + ".")

    return lineas


def resumen_horas(contexto):

    horas = horas_por_repartidor(contexto)
    partes = []

    for repartidor in repartidores_activos(contexto):

        realizadas = horas.get(repartidor["id"], 0)
        pendientes = max(0, repartidor["horas"] - realizadas)
        exceso = max(0, realizadas - repartidor["horas"])
        texto = (
            f"{repartidor['nombre']}: {formatear_horas(realizadas)} h, "
            f"{formatear_horas(pendientes)} h pendientes"
        )

        if exceso:

            texto += f", exceso de {formatear_horas(exceso)} h"

        partes.append(texto)

    return "; ".join(partes) if partes else "No hay repartidores activos."


def comparar_horas(contexto_original, contexto_simulado):

    originales = horas_por_repartidor(contexto_original)
    simuladas = horas_por_repartidor(contexto_simulado)
    cambios = []

    for repartidor in repartidores_activos(contexto_simulado):

        antes = originales.get(repartidor["id"], 0)
        despues = simuladas.get(repartidor["id"], 0)

        if antes != despues:

            cambios.append(
                f"{repartidor['nombre']}: {formatear_horas(antes)} -> "
                f"{formatear_horas(despues)} h"
            )

    return "; ".join(cambios)


def buscar_repartidor(contexto, repartidor_id):

    for repartidor in contexto.get("repartidores", []):

        if repartidor["id"] == repartidor_id:

            return repartidor

    return None


def buscar_turno(contexto, turno_id):

    for turno in contexto.get("turnos", []):

        if turno["id"] == turno_id:

            return turno

    return {}


def buscar_restaurante(contexto, restaurante_id):

    for restaurante in contexto.get("restaurantes", []):

        if restaurante["id"] == restaurante_id:

            return restaurante

    return {}
