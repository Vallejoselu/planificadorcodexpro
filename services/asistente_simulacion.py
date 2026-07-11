from copy import deepcopy
from datetime import date

from database.database import DIAS_SEMANA
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
        "cobertura sin horas complementarias o repartidores adicionales."
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
        "No se ha guardado ningun cambio. Aplicar propuesta no esta disponible "
        "hasta que los horarios por repartidor se persistan de forma segura."
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

        for candidato in candidatos[:5]:

            repartidor = candidato["repartidor"]
            pendientes = formatear_horas(candidato["pendientes"])
            partes.append(
                f"{repartidor['nombre']} valido: disponible, sin descanso, "
                f"sin solapamiento y con {pendientes} h pendientes"
            )

        lineas.append("  Sustitutos posibles: " + "; ".join(partes) + ".")

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
