from database.schema import DIAS_SEMANA
from services.rules.descansos import descanso_valido
from services.rules.disponibilidad import (
    esta_disponible,
    intervalos_solapados
)
from services.rules.horas import (
    calcular_horas_pendientes,
    horas_por_repartidor,
    repartidores_activos
)


def texto_analisis_cuadrante(contexto):

    analisis = analizar_cuadrante(contexto)
    partes = [
        (
            "Analisis del cuadrante: "
            f"{analisis['asignaciones']} asignaciones con repartidor, "
            f"{describir_total_plazas(analisis['sin_repartidor'])}, "
            f"{analisis['pendientes']} repartidores con horas pendientes "
            f"y {analisis['extra']} con horas extra."
        )
    ]

    if analisis["problemas"]:

        partes.append(
            "Problemas detectados: "
            + "; ".join(analisis["problemas"][:8])
            + "."
        )

    else:

        partes.append("No se han detectado problemas criticos.")

    if analisis["recomendaciones"]:

        partes.append(
            "Recomendaciones: "
            + "; ".join(analisis["recomendaciones"][:6])
            + "."
        )

    else:

        partes.append("El cuadrante parece listo para revisar visualmente.")

    return " ".join(partes)


def analizar_cuadrante(contexto):

    repartidores = repartidores_activos(contexto)
    horas = horas_por_repartidor(contexto)
    calendario = contexto.get("calendario", [])
    asignaciones = contexto.get("asignaciones_repartidor", [])

    plazas_sin_repartidor = [
        asignacion
        for asignacion in calendario
        if not asignacion.get("repartidor_id")
    ]
    pendientes = [
        repartidor
        for repartidor in repartidores
        if calcular_horas_pendientes(repartidor, horas) > 0
    ]
    extra = [
        repartidor
        for repartidor in repartidores
        if horas.get(repartidor["id"], 0) > repartidor["horas"]
    ]
    problemas = []
    recomendaciones = []

    problemas.extend(describir_plazas_sin_repartidor(plazas_sin_repartidor))
    problemas.extend(describir_horas_pendientes(pendientes, horas))
    problemas.extend(describir_horas_extra(extra, horas))
    problemas.extend(describir_conflictos_de_reglas(contexto, asignaciones))
    problemas.extend(describir_solapamientos(contexto, asignaciones))

    if plazas_sin_repartidor:

        recomendaciones.append(
            "cubre las plazas sin repartidor o baja la demanda si no hacen falta"
        )

    if pendientes:

        recomendaciones.append(
            "prioriza repartidores con horas pendientes antes de usar horas extra"
        )

    if extra:

        recomendaciones.append(
            "revisa los repartidores por encima de contrato y sus complementarias"
        )

    if any("descanso" in problema for problema in problemas):

        recomendaciones.append(
            "corrige las asignaciones en dias de libranza antes de publicar"
        )

    if any("disponibilidad" in problema for problema in problemas):

        recomendaciones.append(
            "ajusta disponibilidad o cambia el repartidor asignado"
        )

    if any("solapados" in problema for problema in problemas):

        recomendaciones.append(
            "elimina dobles asignaciones que se pisan en horario"
        )

    return {
        "asignaciones": len(asignaciones),
        "sin_repartidor": len(plazas_sin_repartidor),
        "pendientes": len(pendientes),
        "extra": len(extra),
        "problemas": problemas,
        "recomendaciones": recomendaciones
    }


def describir_plazas_sin_repartidor(plazas):

    if not plazas:

        return []

    muestras = [
        describir_asignacion(plaza)
        for plaza in plazas[:4]
    ]
    problemas = [
        f"{describir_total_plazas(len(plazas))}: " + ", ".join(muestras)
    ]

    if len(plazas) > len(muestras):

        problemas.append(
            f"{len(plazas) - len(muestras)} plazas pendientes adicionales"
        )

    return problemas


def describir_horas_pendientes(repartidores, horas):

    return [
        (
            f"{repartidor['nombre']} tiene "
            f"{formatear_horas(calcular_horas_pendientes(repartidor, horas))} "
            "h pendientes"
        )
        for repartidor in repartidores[:4]
    ]


def describir_horas_extra(repartidores, horas):

    return [
        (
            f"{repartidor['nombre']} supera contrato en "
            f"{formatear_horas(horas.get(repartidor['id'], 0) - repartidor['horas'])} "
            "h"
        )
        for repartidor in repartidores[:4]
    ]


def describir_conflictos_de_reglas(contexto, asignaciones):

    repartidores = mapa_por_id(repartidores_activos(contexto))
    turnos = mapa_por_id(contexto.get("turnos", []))
    problemas = []

    for asignacion in asignaciones:

        repartidor = repartidores.get(asignacion.get("repartidor_id"))
        dia = asignacion.get("dia")

        if not repartidor or dia not in DIAS_SEMANA:

            continue

        turno = turnos.get(asignacion.get("turno_id"))
        descanso = repartidor.get("descanso", [])

        if descanso_valido(descanso) and dia in descanso:

            problemas.append(
                f"{repartidor['nombre']} aparece asignado en descanso el {dia}"
            )
            continue

        if turno and not esta_disponible(repartidor, dia, turno):

            problemas.append(
                f"{repartidor['nombre']} no tiene disponibilidad para "
                f"{turno.get('nombre', 'turno')} el {dia}"
            )

    return problemas[:8]


def describir_solapamientos(contexto, asignaciones):

    turnos = mapa_por_id(contexto.get("turnos", []))
    repartidores = mapa_por_id(repartidores_activos(contexto))
    por_repartidor_dia = {}
    problemas = []

    for asignacion in asignaciones:

        repartidor_id = asignacion.get("repartidor_id")
        dia = asignacion.get("dia")

        if not repartidor_id or dia not in DIAS_SEMANA:

            continue

        turno = turnos.get(asignacion.get("turno_id"), {})
        inicio = asignacion.get("hora_inicio") or turno.get("hora_inicio")
        fin = asignacion.get("hora_fin") or turno.get("hora_fin")

        if not inicio or not fin:

            continue

        clave = (repartidor_id, dia)
        por_repartidor_dia.setdefault(clave, []).append((inicio, fin))

    for (repartidor_id, dia), intervalos in por_repartidor_dia.items():

        if len(intervalos) < 2:

            continue

        for indice, actual in enumerate(intervalos):

            for otro in intervalos[indice + 1:]:

                if intervalos_solapados(actual[0], actual[1], otro[0], otro[1]):

                    repartidor = repartidores.get(repartidor_id, {})
                    problemas.append(
                        f"{repartidor.get('nombre', 'Un repartidor')} "
                        f"tiene turnos solapados el {dia}"
                    )
                    break

            if problemas and problemas[-1].endswith(f"el {dia}"):

                break

    return problemas[:8]


def describir_asignacion(asignacion):

    partes = [
        asignacion.get("dia"),
        asignacion.get("turno") or asignacion.get("tipo"),
        asignacion.get("restaurante")
    ]

    texto = " ".join(str(parte) for parte in partes if parte)

    return texto or "plaza sin detalle"


def describir_total_plazas(total):

    if total == 1:

        return "1 plaza sin repartidor"

    return f"{total} plazas sin repartidor"


def mapa_por_id(elementos):

    return {
        elemento.get("id"): elemento
        for elemento in elementos
        if elemento.get("id") is not None
    }


def formatear_horas(valor):

    valor = float(valor or 0)

    if valor.is_integer():

        return str(int(valor))

    return str(round(valor, 2))
