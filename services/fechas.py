from datetime import date, datetime, timedelta

from database.schema import FECHA_INICIO_SEMANA_LEGADO


def normalizar_fecha_inicio_semana(fecha_inicio_semana=None):

    if fecha_inicio_semana is None:

        return FECHA_INICIO_SEMANA_LEGADO

    if isinstance(fecha_inicio_semana, datetime):

        fecha = fecha_inicio_semana.date()

    elif isinstance(fecha_inicio_semana, date):

        fecha = fecha_inicio_semana

    else:

        fecha = datetime.strptime(
            str(fecha_inicio_semana),
            "%Y-%m-%d"
        ).date()

    inicio = fecha - timedelta(days=fecha.weekday())

    return inicio.isoformat()
