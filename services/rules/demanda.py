NIVEL_RESTAURANTE = "restaurante"
NIVEL_ZONA = "zona"
NIVEL_CIUDAD = "ciudad"
NIVEL_DEFECTO = "defecto"

PRIORIDAD_NIVELES_DEMANDA = (
    NIVEL_RESTAURANTE,
    NIVEL_ZONA,
    NIVEL_CIUDAD,
    NIVEL_DEFECTO
)
PRIORIDAD_PERIODOS_DEMANDA = (
    "fecha",
    "dia_semana"
)


def seleccionar_demanda_prioritaria(demandas, dia, fecha_iso=None):

    aplicables = [
        demanda
        for demanda in demandas or []
        if demanda.get("activo", 1)
        and demanda_coincide_periodo(demanda, dia, fecha_iso)
    ]

    if not aplicables:

        return None

    return min(aplicables, key=clave_prioridad_demanda)


def demanda_coincide_periodo(demanda, dia, fecha_iso=None):

    if fecha_iso and demanda.get("fecha") == fecha_iso:

        return True

    return demanda.get("dia_semana") == dia


def clave_prioridad_demanda(demanda):

    return (
        prioridad_nivel_demanda(demanda),
        prioridad_periodo_demanda(demanda)
    )


def prioridad_nivel_demanda(demanda):

    nivel = nivel_demanda(demanda)

    try:

        return PRIORIDAD_NIVELES_DEMANDA.index(nivel)

    except ValueError:

        return len(PRIORIDAD_NIVELES_DEMANDA)


def prioridad_periodo_demanda(demanda):

    if demanda.get("fecha"):

        return PRIORIDAD_PERIODOS_DEMANDA.index("fecha")

    if demanda.get("dia_semana"):

        return PRIORIDAD_PERIODOS_DEMANDA.index("dia_semana")

    return len(PRIORIDAD_PERIODOS_DEMANDA)


def nivel_demanda(demanda):

    nivel = demanda.get("nivel")

    if nivel:

        return str(nivel).strip().lower()

    if demanda.get("restaurante_id") is not None:

        return NIVEL_RESTAURANTE

    if demanda.get("zona"):

        return NIVEL_ZONA

    if demanda.get("ciudad_id") is not None:

        return NIVEL_CIUDAD

    return NIVEL_DEFECTO
