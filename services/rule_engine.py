"""
Fachada de compatibilidad para reglas de negocio.

El codigo nuevo debe importar desde services.rules.*. Este modulo conserva los
nombres publicos antiguos para el asistente, pruebas historicas y llamadas que
aun no han migrado de fases previas.
"""

from services.rules.ausencias import (
    dia_en_rango,
    esta_ausente,
    esta_ausente_por_tipo,
    rango_contiene
)
from services.rules.candidatos import (
    autorizado_para_ciudad,
    autorizado_para_restaurante,
    coste_desplazamiento,
    cumple_restaurante_o_zona,
    es_turno_noche,
    excede_dias_consecutivos,
    excede_horas_diarias,
    horario_no_permitido,
    motivo_no_puede_trabajar,
    puede_trabajar,
    preferencia_aplica,
    prioridad_repartidor,
    puntuacion_preferencia,
    puntuacion_preferencia_asistente,
    restriccion_aplica,
    solapa_con_asignacion,
    solapa_turno,
    turno_por_id,
    turnos_consecutivos
)
from services.rules.descansos import (
    DESCANSO_NO_NECESARIO,
    asegurar_descanso_consecutivo,
    calcular_descanso,
    descanso_es_consecutivo,
    dias_no_disponibles,
    disponibilidad_aporta_descanso,
    tiene_dias_consecutivos
)
from services.rules.disponibilidad import (
    categoria_turno,
    claves_disponibilidad_turno,
    esta_disponible,
    esta_disponible_dia,
    intervalo_turno,
    intervalos_solapados,
    minutos_hora as minutos,
    minutos_hora,
    nombre_turno_disponibilidad,
    parsear_fecha,
    turno_tiene_horario
)

__all__ = [
    "DESCANSO_NO_NECESARIO",
    "asegurar_descanso_consecutivo",
    "autorizado_para_ciudad",
    "autorizado_para_restaurante",
    "calcular_descanso",
    "categoria_turno",
    "claves_disponibilidad_turno",
    "coste_desplazamiento",
    "cumple_restaurante_o_zona",
    "descanso_es_consecutivo",
    "dia_en_rango",
    "dias_no_disponibles",
    "disponibilidad_aporta_descanso",
    "es_turno_noche",
    "esta_ausente",
    "esta_ausente_por_tipo",
    "esta_disponible",
    "esta_disponible_dia",
    "excede_dias_consecutivos",
    "excede_horas_diarias",
    "horario_no_permitido",
    "intervalo_turno",
    "intervalos_solapados",
    "minutos",
    "minutos_hora",
    "motivo_no_puede_trabajar",
    "nombre_turno_disponibilidad",
    "parsear_fecha",
    "preferencia_aplica",
    "prioridad_repartidor",
    "puede_trabajar",
    "puntuacion_preferencia",
    "puntuacion_preferencia_asistente",
    "rango_contiene",
    "restriccion_aplica",
    "solapa_con_asignacion",
    "solapa_turno",
    "tiene_dias_consecutivos",
    "turno_por_id",
    "turno_tiene_horario",
    "turnos_consecutivos"
]
