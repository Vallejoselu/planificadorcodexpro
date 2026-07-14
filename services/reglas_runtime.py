from services.constraints import MAX_HORAS_SEMANALES


REGLAS_MOTOR_DEFECTO = {
    "max_horas_semanales": float(MAX_HORAS_SEMANALES),
    "horas_complementarias": "segun repartidor",
    "penalizacion_desplazamiento": 1.0
}

_reglas_motor = dict(REGLAS_MOTOR_DEFECTO)


def obtener_reglas_motor():

    return dict(_reglas_motor)


def actualizar_reglas_motor(reglas):

    _reglas_motor.update(reglas or {})


def resetear_reglas_motor():

    _reglas_motor.clear()
    _reglas_motor.update(REGLAS_MOTOR_DEFECTO)
