from database.schema import DIAS_SEMANA
from services.asistente_horarios import (
    formatear_horas,
    horas_por_repartidor,
    preparar_contexto,
    repartidores_activos
)
from services.rules.descansos import descanso_valido
from services.rules.disponibilidad import (
    esta_disponible,
    intervalos_solapados
)
from services.rules.horas import calcular_horas_pendientes


def es_pregunta_prioridad(texto):

    return (
        "que hago primero" in texto
        or "que arreglo primero" in texto
        or "por donde empiezo" in texto
        or "prioridad del cuadrante" in texto
        or "acciones prioritarias" in texto
        or "orden de acciones" in texto
        or "que soluciono primero" in texto
    )


def responder_prioridad(texto, contexto=None, fecha_referencia=None):

    contexto = preparar_contexto(contexto)
    acciones = acciones_prioritarias(contexto)

    if not acciones:

        return (
            "Prioridad del cuadrante: no veo bloqueos importantes. "
            "Revisa visualmente los horarios y publica solo si la cobertura "
            "encaja con la operativa real."
        )

    lineas = [
        "Prioridad de acciones del cuadrante:",
        "Empieza por lo que puede impedir publicar o cubrir servicio.",
        ""
    ]

    for indice, accion in enumerate(acciones[:8], start=1):

        lineas.append(f"{indice}. {accion}")

    lineas.append("")
    lineas.append(
        "No he guardado ningun cambio. Usa esta lista como orden de trabajo "
        "en la pantalla de Cuadrantes."
    )

    return "\n".join(lineas)


def acciones_prioritarias(contexto):

    acciones = []
    acciones.extend(acciones_plazas_sin_repartidor(contexto))
    acciones.extend(acciones_descanso_disponibilidad(contexto))
    acciones.extend(acciones_solapamientos(contexto))
    acciones.extend(acciones_horas_extra(contexto))
    acciones.extend(acciones_horas_pendientes(contexto))

    return acciones


def acciones_plazas_sin_repartidor(contexto):

    plazas = [
        plaza
        for plaza in contexto.get("calendario", [])
        if not plaza.get("repartidor_id")
    ]

    if not plazas:

        return []

    detalle = ", ".join(
        describir_plaza(plaza, contexto)
        for plaza in plazas[:3]
    )

    extra = ""

    if len(plazas) > 3:

        extra = f" y {len(plazas) - 3} mas"

    return [(
        f"Cubrir plazas sin repartidor: hay {len(plazas)} pendiente(s) "
        f"({detalle}{extra}). Sin esto el servicio queda incompleto."
    )]


def acciones_descanso_disponibilidad(contexto):

    repartidores = mapa_por_id(repartidores_activos(contexto))
    turnos = mapa_por_id(contexto.get("turnos", []))
    problemas = []

    for asignacion in contexto.get("asignaciones_repartidor", []):

        repartidor = repartidores.get(asignacion.get("repartidor_id"))
        dia = asignacion.get("dia")
        turno = turnos.get(asignacion.get("turno_id"))

        if not repartidor or dia not in DIAS_SEMANA:

            continue

        if descanso_valido(repartidor.get("descanso", [])) and dia in repartidor.get("descanso", []):

            problemas.append(
                f"{repartidor['nombre']} esta asignado en su dia libre {dia}"
            )
            continue

        if turno and not esta_disponible(repartidor, dia, turno):

            problemas.append(
                f"{repartidor['nombre']} no tiene disponibilidad para "
                f"{turno.get('nombre', 'turno')} el {dia}"
            )

    if not problemas:

        return []

    return [(
        "Corregir descansos o disponibilidad: "
        + "; ".join(problemas[:3])
        + ". Estas asignaciones no deberian mantenerse."
    )]


def acciones_solapamientos(contexto):

    turnos = mapa_por_id(contexto.get("turnos", []))
    repartidores = mapa_por_id(repartidores_activos(contexto))
    por_repartidor_dia = {}
    problemas = []

    for asignacion in contexto.get("asignaciones_repartidor", []):

        repartidor_id = asignacion.get("repartidor_id")
        dia = asignacion.get("dia")
        turno = turnos.get(asignacion.get("turno_id"), {})
        inicio = asignacion.get("hora_inicio") or turno.get("hora_inicio")
        fin = asignacion.get("hora_fin") or turno.get("hora_fin")

        if not repartidor_id or dia not in DIAS_SEMANA or not inicio or not fin:

            continue

        clave = (repartidor_id, dia)
        por_repartidor_dia.setdefault(clave, []).append((inicio, fin))

    for (repartidor_id, dia), intervalos in por_repartidor_dia.items():

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

    if not problemas:

        return []

    return [(
        "Eliminar solapamientos: "
        + "; ".join(problemas[:3])
        + ". Una persona no puede estar en dos sitios a la vez."
    )]


def acciones_horas_extra(contexto):

    horas = horas_por_repartidor(contexto)
    extras = []

    for repartidor in repartidores_activos(contexto):

        exceso = horas.get(repartidor["id"], 0) - repartidor["horas"]

        if exceso > 0:

            extras.append((repartidor, exceso))

    if not extras:

        return []

    extras.sort(key=lambda item: (-item[1], item[0]["nombre"]))
    detalle = ", ".join(
        f"{repartidor['nombre']} +{formatear_horas(exceso)} h"
        for repartidor, exceso in extras[:3]
    )

    return [(
        f"Revisar horas extra: {detalle}. Cambia turnos a personas con "
        "horas pendientes si hay candidatos compatibles."
    )]


def acciones_horas_pendientes(contexto):

    horas = horas_por_repartidor(contexto)
    pendientes = []

    for repartidor in repartidores_activos(contexto):

        pendiente = calcular_horas_pendientes(repartidor, horas)

        if pendiente > 0:

            pendientes.append((repartidor, pendiente))

    if not pendientes:

        return []

    pendientes.sort(key=lambda item: (-item[1], item[0]["nombre"]))
    detalle = ", ".join(
        f"{repartidor['nombre']} {formatear_horas(pendiente)} h"
        for repartidor, pendiente in pendientes[:4]
    )

    return [(
        f"Balancear horas pendientes: {detalle}. Esto va despues de cubrir "
        "plazas, descansos y solapamientos."
    )]


def describir_plaza(plaza, contexto):

    turno = buscar_por_id(contexto.get("turnos", []), plaza.get("turno_id"))
    restaurante = buscar_por_id(
        contexto.get("restaurantes", []),
        plaza.get("restaurante_id")
    )

    partes = [
        plaza.get("dia"),
        plaza.get("turno") or (turno or {}).get("nombre"),
        plaza.get("restaurante") or (restaurante or {}).get("nombre")
    ]

    return " ".join(str(parte) for parte in partes if parte)


def buscar_por_id(elementos, elemento_id):

    for elemento in elementos:

        if elemento.get("id") == elemento_id:

            return elemento

    return None


def mapa_por_id(elementos):

    return {
        elemento.get("id"): elemento
        for elemento in elementos
        if elemento.get("id") is not None
    }
