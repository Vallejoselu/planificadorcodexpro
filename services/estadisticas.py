from calendar import monthrange
from datetime import date, datetime, timedelta

from database.database import (
    conectar,
    crear_base_datos,
    descanso_es_valido,
    obtener_calendario_semanal,
    obtener_repartidores,
    obtener_turnos
)


MESES = (
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic"
)


def obtener_estadisticas(anio=None):

    crear_base_datos()

    if anio is None:

        anio = date.today().year

    repartidores = obtener_repartidores()
    turnos = {
        turno[0]: turno
        for turno in obtener_turnos()
    }
    calendario = obtener_calendario_semanal()

    horas_trabajadas = _sumar_horas_calendario(calendario, turnos)
    horas_contratadas = sum(int(repartidor[2] or 0) for repartidor in repartidores)
    horas_pendientes = max(0, horas_contratadas - horas_trabajadas)
    horas_complementarias = max(0, horas_trabajadas - horas_contratadas)
    descansos = [
        repartidor
        for repartidor in repartidores
        if repartidor[9] and repartidor[10]
    ]
    vacaciones = _obtener_ausencias("vacaciones", "activo")
    bajas = _obtener_ausencias("bajas", "activa")

    return {
        "resumen": {
            "horas_trabajadas": _formatear_numero(horas_trabajadas),
            "horas_pendientes": _formatear_numero(horas_pendientes),
            "horas_complementarias": _formatear_numero(horas_complementarias),
            "turnos": len(calendario),
            "descansos": len(descansos),
            "vacaciones": len(vacaciones),
            "bajas": len(bajas)
        },
        "turnos": _resumen_turnos(calendario, turnos),
        "descansos": _resumen_descansos(descansos),
        "vacaciones": vacaciones,
        "bajas": bajas,
        "mensual": _resumen_mensual(
            anio,
            horas_trabajadas,
            vacaciones,
            bajas
        )
    }


def _sumar_horas_calendario(calendario, turnos):

    total = 0

    for asignacion in calendario:

        turno = turnos.get(asignacion[2])

        if turno:

            total += float(turno[6] or 0)

    return total


def _resumen_turnos(calendario, turnos):

    resumen = {}

    for asignacion in calendario:

        turno = turnos.get(asignacion[2])

        if not turno:

            continue

        nombre = turno[2]

        if nombre not in resumen:

            resumen[nombre] = {
                "turno": nombre,
                "tipo": turno[1],
                "cantidad": 0,
                "horas": 0
            }

        resumen[nombre]["cantidad"] += 1
        resumen[nombre]["horas"] += float(turno[6] or 0)

    return [
        {
            "turno": datos["turno"],
            "tipo": datos["tipo"],
            "cantidad": datos["cantidad"],
            "horas": _formatear_numero(datos["horas"])
        }
        for datos in sorted(resumen.values(), key=lambda item: item["turno"])
    ]


def _resumen_descansos(descansos):

    return [
        {
            "repartidor": repartidor[1],
            "contrato": repartidor[2],
            "descanso": _formatear_descanso(repartidor)
        }
        for repartidor in descansos
    ]


def _formatear_descanso(repartidor):

    descanso = f"{repartidor[9]} - {repartidor[10]}"

    if not descanso_es_valido(repartidor[9], repartidor[10]):

        return descanso + " (no valido)"

    return descanso


def _obtener_ausencias(tabla, columna_activa):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute(f"""
    SELECT
        r.nombre,
        a.fecha_inicio,
        a.fecha_fin
    FROM {tabla} a
    INNER JOIN repartidores r
        ON r.id=a.repartidor_id
    WHERE a.{columna_activa}=1
    AND r.activo=1
    ORDER BY a.fecha_inicio, r.nombre
    """)

    ausencias = [
        {
            "repartidor": fila[0],
            "inicio": fila[1],
            "fin": fila[2] or fila[1]
        }
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return ausencias


def _resumen_mensual(anio, horas_semanales, vacaciones, bajas):

    filas = []

    for mes in range(1, 13):

        inicio = date(anio, mes, 1)
        fin = date(anio, mes, monthrange(anio, mes)[1])

        filas.append({
            "mes": MESES[mes - 1],
            "horas": _formatear_numero(
                horas_semanales * _semanas_en_rango(inicio, fin)
            ),
            "vacaciones": _dias_ausencia_mes(vacaciones, inicio, fin),
            "bajas": _dias_ausencia_mes(bajas, inicio, fin)
        })

    return filas


def _semanas_en_rango(inicio, fin):

    dias = (fin - inicio).days + 1

    return round(dias / 7, 2)


def _dias_ausencia_mes(ausencias, inicio_mes, fin_mes):

    total = 0

    for ausencia in ausencias:

        inicio = _parsear_fecha(ausencia["inicio"])
        fin = _parsear_fecha(ausencia["fin"]) or inicio

        if not inicio:

            continue

        inicio = max(inicio, inicio_mes)
        fin = min(fin, fin_mes)

        if inicio <= fin:

            total += (fin - inicio).days + 1

    return total


def _parsear_fecha(valor):

    if isinstance(valor, date):

        return valor

    if not valor:

        return None

    try:

        return datetime.strptime(str(valor), "%Y-%m-%d").date()

    except ValueError:

        return None


def _formatear_numero(valor):

    valor = float(valor or 0)

    if valor.is_integer():

        return int(valor)

    return round(valor, 2)
