def repartidores_activos(contexto):

    return [
        repartidor
        for repartidor in contexto["repartidores"]
        if repartidor.get("activo", 1)
    ]


def restaurantes_activos(contexto):

    return [
        restaurante
        for restaurante in contexto["restaurantes"]
        if restaurante.get("activo", 1)
    ]


def turnos_activos(contexto):

    return [
        turno
        for turno in contexto["turnos"]
        if turno.get("activo", 1)
    ]


def horas_por_repartidor(contexto):

    horas = {
        repartidor["id"]: 0
        for repartidor in repartidores_activos(contexto)
    }

    for asignacion in contexto.get("asignaciones_repartidor", []):

        repartidor_id = asignacion.get("repartidor_id")

        if repartidor_id in horas:

            horas[repartidor_id] += float(asignacion.get("duracion", 0) or 0)

    return horas


def calcular_horas_pendientes(repartidor, horas):

    return max(0, repartidor["horas"] - horas.get(repartidor["id"], 0))
