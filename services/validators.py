from services.constraints import DESCANSOS_VALIDOS


def validar_horario(resultado):

    errores = []
    resumen_por_id = {
        repartidor["id"]: repartidor
        for repartidor in resultado.get("resumen", [])
    }

    for resumen in resultado.get("resumen", []):

        if resumen.get("horas", 0) > resumen.get("maximo", 0):

            errores.append(
                f"{resumen['nombre']} supera sus horas maximas."
            )

        if resumen.get("descanso") and resumen.get("descanso") not in DESCANSOS_VALIDOS:

            errores.append(
                f"{resumen['nombre']} tiene descanso no valido."
            )

    for dia, turnos in resultado.get("horario", {}).items():

        for nombre_turno, asignaciones in turnos.items():

            repartidores_en_turno = set()

            for asignacion in asignaciones:

                repartidor_id = asignacion.get("repartidor_id")
                resumen = resumen_por_id.get(repartidor_id)

                if repartidor_id in repartidores_en_turno:

                    errores.append(
                        f"Repartidor duplicado en {dia} {nombre_turno}."
                    )

                repartidores_en_turno.add(repartidor_id)

                if resumen and dia in resumen.get("descanso", []):

                    errores.append(
                        f"{resumen['nombre']} asignado durante descanso."
                    )

    return errores
