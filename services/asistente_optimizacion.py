from copy import deepcopy

from services.analizador_cuadrante import analizar_cuadrante
from services.asistente_horarios import (
    buscar_candidatos,
    formatear_horas,
    horas_por_repartidor,
    preparar_contexto,
    repartidores_activos
)


def es_pregunta_optimizacion(texto):

    return (
        "optimiza" in texto
        or "optimizar" in texto
        or "mejora el cuadrante" in texto
        or "mejorar el cuadrante" in texto
        or "que cambios" in texto
        or "cambios recomiendas" in texto
        or "recomienda cambios" in texto
    )


def responder_optimizacion(texto, contexto=None, fecha_referencia=None):

    contexto = preparar_contexto(contexto)
    analisis = analizar_cuadrante(contexto)
    propuestas = []

    propuestas.extend(proponer_cobertura_pendiente(contexto))
    propuestas.extend(proponer_reduccion_horas_extra(contexto))
    propuestas.extend(proponer_balance_horas(contexto))

    if not propuestas:

        return (
            "Optimizacion del cuadrante: no veo cambios claros que aplicar. "
            f"{resumen_estado(analisis)} Puedes revisarlo visualmente antes "
            "de publicar."
        )

    lineas = [
        "Optimizacion sugerida del cuadrante:",
        resumen_estado(analisis),
        "",
        "Cambios recomendados:"
    ]
    lineas.extend(
        f"- {propuesta}"
        for propuesta in propuestas[:8]
    )
    lineas.append("")
    lineas.append(
        "No he guardado ningun cambio. Aplica solo las propuestas que te "
        "encajen desde la pantalla de Cuadrantes."
    )

    return "\n".join(lineas)


def proponer_cobertura_pendiente(contexto):

    propuestas = []

    for plaza in plazas_sin_repartidor(contexto)[:5]:

        turno = turno_por_id(contexto, plaza.get("turno_id"))
        restaurante = restaurante_por_id(contexto, plaza.get("restaurante_id"))

        if not turno:

            continue

        candidatos, rechazos = buscar_candidatos(
            contexto,
            plaza.get("dia"),
            turno,
            restaurante,
            None
        )

        if candidatos:

            candidato = candidatos[0]
            repartidor = candidato["repartidor"]
            propuestas.append(
                "Cubrir "
                f"{descripcion_plaza(plaza, turno, restaurante)} con "
                f"{repartidor['nombre']}: esta disponible, no solapa y tiene "
                f"{formatear_horas(candidato['pendientes'])} h pendientes."
            )

        else:

            propuestas.append(
                "Revisar "
                f"{descripcion_plaza(plaza, turno, restaurante)}: no hay "
                f"candidato valido ({resumir_rechazos(rechazos)})."
            )

    return propuestas


def proponer_reduccion_horas_extra(contexto):

    propuestas = []
    horas = horas_por_repartidor(contexto)
    repartidores = {
        repartidor["id"]: repartidor
        for repartidor in repartidores_activos(contexto)
    }

    for asignacion in contexto.get("asignaciones_repartidor", []):

        repartidor = repartidores.get(asignacion.get("repartidor_id"))

        if not repartidor:

            continue

        exceso = horas.get(repartidor["id"], 0) - repartidor["horas"]

        if exceso <= 0:

            continue

        turno = turno_por_id(contexto, asignacion.get("turno_id"))
        restaurante = restaurante_por_id(
            contexto,
            asignacion.get("restaurante_id")
        )

        if not turno:

            continue

        contexto_sin_asignacion = quitar_asignacion(contexto, asignacion)
        candidatos, _ = buscar_candidatos(
            contexto_sin_asignacion,
            asignacion.get("dia"),
            turno,
            restaurante,
            None
        )
        candidatos = [
            candidato
            for candidato in candidatos
            if candidato["repartidor"]["id"] != repartidor["id"]
        ]

        if not candidatos:

            continue

        candidato = candidatos[0]
        propuestas.append(
            f"Cambiar {descripcion_plaza(asignacion, turno, restaurante)} de "
            f"{repartidor['nombre']} a {candidato['repartidor']['nombre']} "
            f"para reducir {formatear_horas(exceso)} h extra."
        )

        if len(propuestas) >= 3:

            break

    return propuestas


def proponer_balance_horas(contexto):

    horas = horas_por_repartidor(contexto)
    pendientes = [
        (
            repartidor,
            repartidor["horas"] - horas.get(repartidor["id"], 0)
        )
        for repartidor in repartidores_activos(contexto)
        if repartidor["horas"] - horas.get(repartidor["id"], 0) > 0
    ]

    if not pendientes:

        return []

    pendientes.sort(key=lambda item: (-item[1], item[0]["nombre"]))
    repartidor, horas_pendientes = pendientes[0]

    return [(
        f"Priorizar a {repartidor['nombre']} en proximas plazas compatibles: "
        f"tiene {formatear_horas(horas_pendientes)} h pendientes."
    )]


def resumen_estado(analisis):

    return (
        f"Estado: {analisis['sin_repartidor']} plazas sin repartidor, "
        f"{analisis['pendientes']} repartidores con horas pendientes y "
        f"{analisis['extra']} con horas extra."
    )


def plazas_sin_repartidor(contexto):

    return [
        asignacion
        for asignacion in contexto.get("calendario", [])
        if not asignacion.get("repartidor_id")
    ]


def quitar_asignacion(contexto, asignacion_objetivo):

    copia = deepcopy(contexto)
    copia["asignaciones_repartidor"] = [
        asignacion
        for asignacion in copia.get("asignaciones_repartidor", [])
        if not misma_asignacion(asignacion, asignacion_objetivo)
    ]

    return copia


def misma_asignacion(a, b):

    return (
        a.get("repartidor_id") == b.get("repartidor_id")
        and a.get("dia") == b.get("dia")
        and a.get("turno_id") == b.get("turno_id")
        and a.get("restaurante_id") == b.get("restaurante_id")
    )


def turno_por_id(contexto, turno_id):

    for turno in contexto.get("turnos", []):

        if turno.get("id") == turno_id:

            return turno

    return None


def restaurante_por_id(contexto, restaurante_id):

    for restaurante in contexto.get("restaurantes", []):

        if restaurante.get("id") == restaurante_id:

            return restaurante

    return None


def descripcion_plaza(asignacion, turno, restaurante):

    destino = restaurante["nombre"] if restaurante else "sin restaurante"

    return (
        f"{asignacion.get('dia')} {turno.get('nombre', 'turno')} "
        f"en {destino}"
    )


def resumir_rechazos(rechazos):

    if not rechazos:

        return "sin detalle de rechazo"

    motivo, cantidad = sorted(
        rechazos.items(),
        key=lambda item: (-item[1], item[0])
    )[0]

    return f"{cantidad} {motivo}"
