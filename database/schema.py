FECHA_INICIO_SEMANA_LEGADO = "1970-01-05"
SCHEMA_VERSION_ACTUAL = 3

HORAS_CONTRATO = (10, 20, 25, 30, 35, 40)
DIAS_SEMANA = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo"
)
DESCANSOS_VALIDOS = (
    ("lunes", "martes"),
    ("martes", "miercoles"),
    ("miercoles", "jueves"),
    ("jueves", "viernes")
)
DIAS_INICIO_DESCANSO = tuple(
    descanso[0]
    for descanso in DESCANSOS_VALIDOS
)
TURNOS_DISPONIBILIDAD = (
    "comida",
    "noche"
)
OPCIONES_DISPONIBILIDAD = (
    "Comidas",
    "Cenas",
    "Ambos",
    "No disponible"
)
TIPOS_TURNO = (
    "Comida",
    "Cena",
    "Turno partido",
    "Personalizado"
)
PROVEEDORES_INTEGRACION = (
    "shipday",
    "glovo",
    "uber",
    "api_generica"
)
CIUDAD_SIN_CIUDAD = "Sin ciudad"
