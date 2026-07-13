from services.planning_models import IncidenciaValidacion
from services.rules.disponibilidad import intervalos_solapados


def validar_planificacion(resultado):

    incidencias = []
    incidencias.extend(validar_horas_resumen(resultado.get("resumen", [])))
    incidencias.extend(validar_asignaciones(resultado.get("horario", {})))

    return [
        incidencia.to_dict()
        for incidencia in incidencias
    ]


def validar_horas_resumen(resumen):

    incidencias = []

    for item in resumen:

        if item.get("horas", 0) <= item.get("maximo", 0):

            continue

        incidencias.append(
            IncidenciaValidacion(
                regla="validacion final de horas",
                motivo=(
                    f"{item.get('nombre')} supera su maximo "
                    f"({item.get('horas'):g}/{item.get('maximo'):g} h)."
                )
            )
        )

    return incidencias


def validar_asignaciones(horario):

    incidencias = []

    for dia, turnos_dia in horario.items():

        intervalos_por_repartidor = {}

        for nombre_turno, asignaciones in turnos_dia.items():

            vistos = set()

            for asignacion in asignaciones:

                repartidor_id = asignacion.get("repartidor_id")

                if not repartidor_id:

                    continue

                if repartidor_id in vistos:

                    incidencias.append(
                        IncidenciaValidacion(
                            regla="validacion final de duplicados",
                            dia=dia,
                            turno=nombre_turno,
                            restaurante=asignacion.get("restaurante", ""),
                            motivo=(
                                "Un repartidor aparece dos veces en el "
                                "mismo turno generado."
                            )
                        )
                    )

                vistos.add(repartidor_id)
                registrar_intervalo_si_solapa(
                    incidencias,
                    intervalos_por_repartidor,
                    dia,
                    nombre_turno,
                    asignacion
                )

    return incidencias


def registrar_intervalo_si_solapa(
    incidencias,
    intervalos_por_repartidor,
    dia,
    nombre_turno,
    asignacion
):

    repartidor_id = asignacion.get("repartidor_id")
    inicio = asignacion.get("hora_inicio")
    fin = asignacion.get("hora_fin")

    if not repartidor_id or not inicio or not fin:

        return

    intervalos = intervalos_por_repartidor.setdefault(repartidor_id, [])

    for existente in intervalos:

        if intervalos_solapados(inicio, fin, existente[0], existente[1]):

            incidencias.append(
                IncidenciaValidacion(
                    regla="validacion final de solapamientos",
                    dia=dia,
                    turno=nombre_turno,
                    restaurante=asignacion.get("restaurante", ""),
                    motivo=(
                        "Un repartidor tiene turnos solapados en el "
                        "cuadrante generado."
                    )
                )
            )
            break

    intervalos.append((inicio, fin))
