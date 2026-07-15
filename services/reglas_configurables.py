from repositories.reglas_repository import ReglasRepository
from services.reglas_runtime import (
    REGLAS_MOTOR_DEFECTO,
    actualizar_reglas_motor
)


class ReglasConfigurablesService:

    CATALOGO = [
        {
            "clave": "descanso_consecutivo",
            "nombre": "Descanso de dos dias consecutivos",
            "valor": "Obligatorio",
            "origen": "services.rules.descansos",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "disponibilidad",
            "nombre": "Disponibilidad semanal",
            "valor": "Obligatoria por dia y turno",
            "origen": "services.rules.disponibilidad",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "vacaciones_bajas",
            "nombre": "Vacaciones y bajas",
            "valor": "Bloquean asignacion",
            "origen": "services.rules.ausencias",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "solapamientos",
            "nombre": "Solapamientos horarios",
            "valor": "No permitidos",
            "origen": "services.rules.candidatos",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "horas_contratadas",
            "nombre": "Horas contratadas",
            "valor": "10, 20, 25, 30, 35, 40",
            "origen": "database.schema",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "max_horas_semanales",
            "nombre": "Maximo de horas semanales",
            "valor": str(int(REGLAS_MOTOR_DEFECTO["max_horas_semanales"])),
            "origen": "services.scheduler",
            "editable": True,
            "tipo": "decimal",
            "min": 1,
            "max": 80,
            "aplicada_motor": True
        },
        {
            "clave": "horas_complementarias",
            "nombre": "Horas complementarias",
            "valor": "segun repartidor",
            "origen": "services.rules.candidatos",
            "editable": True,
            "tipo": "opcion",
            "opciones": ("segun repartidor", "permitir", "prohibir"),
            "aplicada_motor": True
        },
        {
            "clave": "penalizacion_desplazamiento",
            "nombre": "Penalizacion por desplazamiento",
            "valor": str(int(REGLAS_MOTOR_DEFECTO["penalizacion_desplazamiento"])),
            "origen": "services.planning_scoring",
            "editable": True,
            "tipo": "decimal",
            "min": 0,
            "max": 10,
            "aplicada_motor": True
        },
        {
            "clave": "peso_prioridad_zona",
            "nombre": "Peso de prioridad por zona",
            "valor": str(int(REGLAS_MOTOR_DEFECTO["peso_prioridad_zona"])),
            "origen": "services.rules.candidatos",
            "editable": True,
            "tipo": "decimal",
            "min": 0,
            "max": 100,
            "aplicada_motor": True
        },
        {
            "clave": "peso_restaurante_fijo",
            "nombre": "Peso de restaurante fijo",
            "valor": str(int(REGLAS_MOTOR_DEFECTO["peso_restaurante_fijo"])),
            "origen": "services.rules.candidatos",
            "editable": True,
            "tipo": "decimal",
            "min": 0,
            "max": 100,
            "aplicada_motor": True
        },
        {
            "clave": "peso_balance_comidas_cenas",
            "nombre": "Balance comidas/cenas",
            "valor": str(int(REGLAS_MOTOR_DEFECTO["peso_balance_comidas_cenas"])),
            "origen": "services.planning_scoring",
            "editable": True,
            "tipo": "decimal",
            "min": 0,
            "max": 10,
            "aplicada_motor": True
        },
        {
            "clave": "max_horas_diarias",
            "nombre": "Maximo de horas diarias",
            "valor": "10",
            "origen": "services.rules.candidatos",
            "editable": True,
            "tipo": "decimal",
            "min": 1,
            "max": 24,
            "aplicada_motor": False
        },
        {
            "clave": "max_dias_consecutivos",
            "nombre": "Maximo de dias consecutivos",
            "valor": "5",
            "origen": "services.rules.candidatos",
            "editable": True,
            "tipo": "entero",
            "min": 1,
            "max": 7,
            "aplicada_motor": False
        },
        {
            "clave": "autorizaciones",
            "nombre": "Restaurantes y ciudades autorizadas",
            "valor": "Principal, autorizados o apoyo flexible",
            "origen": "services.rules.candidatos",
            "editable": False,
            "tipo": "texto"
        },
        {
            "clave": "prioridad_demanda",
            "nombre": "Prioridad de demanda",
            "valor": "Restaurante > zona > ciudad > defecto",
            "origen": "services.demanda",
            "editable": False,
            "tipo": "texto"
        }
    ]

    def __init__(self, reglas_repository=None):

        self.reglas_repository = reglas_repository or ReglasRepository()

    def listar_reglas(self):

        configuracion = self.configuracion_por_clave()
        actualizar_reglas_motor(self.configuracion_motor(configuracion))
        reglas = []

        for regla in self.CATALOGO:

            valor_configurado = configuracion.get(regla["clave"])
            datos = dict(regla)
            datos["valor_configurado"] = (
                valor_configurado
                if valor_configurado is not None
                else regla["valor"]
            )
            datos["configurado"] = valor_configurado is not None
            reglas.append(datos)

        return reglas

    def configuracion_por_clave(self):

        return {
            fila[0]: fila[1]
            for fila in self.reglas_repository.listar_configuracion()
            if fila[2]
        }

    def resumen(self):

        reglas = self.listar_reglas()
        editables = [
            regla
            for regla in reglas
            if regla["editable"]
        ]
        configuradas = [
            regla
            for regla in reglas
            if regla["configurado"]
        ]

        return {
            "total": len(reglas),
            "editables": len(editables),
            "configuradas": len(configuradas),
            "aplicadas_motor": len([
                regla
                for regla in reglas
                if regla.get("aplicada_motor")
            ]),
            "modo": "preparacion"
        }

    def configuracion_motor(self, configuracion=None):

        if configuracion is None:

            configuracion = self.configuracion_por_clave()

        resultado = dict(REGLAS_MOTOR_DEFECTO)

        if "max_horas_semanales" in configuracion:

            resultado["max_horas_semanales"] = float(
                configuracion["max_horas_semanales"]
            )

        if "horas_complementarias" in configuracion:

            resultado["horas_complementarias"] = configuracion[
                "horas_complementarias"
            ]

        if "penalizacion_desplazamiento" in configuracion:

            resultado["penalizacion_desplazamiento"] = float(
                configuracion["penalizacion_desplazamiento"]
            )

        if "peso_prioridad_zona" in configuracion:

            resultado["peso_prioridad_zona"] = float(
                configuracion["peso_prioridad_zona"]
            )

        if "peso_restaurante_fijo" in configuracion:

            resultado["peso_restaurante_fijo"] = float(
                configuracion["peso_restaurante_fijo"]
            )

        if "peso_balance_comidas_cenas" in configuracion:

            resultado["peso_balance_comidas_cenas"] = float(
                configuracion["peso_balance_comidas_cenas"]
            )

        return resultado

    def guardar_configuracion(self, valores):

        guardadas = 0

        for clave, valor in valores.items():

            regla = self.obtener_regla_catalogo(clave)

            if not regla:

                raise ValueError(f"Regla desconocida: {clave}.")

            if not regla["editable"]:

                raise ValueError(f"La regla {regla['nombre']} no es editable.")

            valor_validado = self.validar_valor(regla, valor)
            self.reglas_repository.guardar(clave, valor_validado)
            guardadas += 1

        actualizar_reglas_motor(self.configuracion_motor())

        return {
            "guardadas": guardadas
        }

    def restaurar_valores(self):

        claves = [
            regla["clave"]
            for regla in self.CATALOGO
            if regla["editable"]
        ]
        self.reglas_repository.eliminar(claves)
        actualizar_reglas_motor(self.configuracion_motor())

        return {
            "restauradas": len(claves)
        }

    def obtener_regla_catalogo(self, clave):

        for regla in self.CATALOGO:

            if regla["clave"] == clave:

                return regla

        return None

    def validar_valor(self, regla, valor):

        valor = str(valor or "").strip()

        if not valor:

            raise ValueError(f"{regla['nombre']} necesita un valor.")

        if regla["tipo"] == "opcion":

            valor = valor.lower()

            if valor not in regla["opciones"]:

                opciones = ", ".join(regla["opciones"])
                raise ValueError(
                    f"{regla['nombre']} debe ser uno de: {opciones}."
                )

            return valor

        if regla["tipo"] == "decimal":

            try:

                numero = float(valor.replace(",", "."))

            except ValueError as error:

                raise ValueError(
                    f"{regla['nombre']} debe ser numerico."
                ) from error

            minimo = float(regla.get("min", 1))
            maximo = float(regla.get("max", 24))

            if numero < minimo or numero > maximo:

                raise ValueError(
                    f"{regla['nombre']} debe estar entre "
                    f"{formatear_numero(minimo)} y {formatear_numero(maximo)}."
                )

            return str(int(numero)) if numero.is_integer() else str(numero)

        if regla["tipo"] == "entero":

            try:

                numero = int(float(valor.replace(",", ".")))

            except ValueError as error:

                raise ValueError(
                    f"{regla['nombre']} debe ser un numero entero."
                ) from error

            minimo = int(regla.get("min", 1))
            maximo = int(regla.get("max", 7))

            if numero < minimo or numero > maximo:

                raise ValueError(
                    f"{regla['nombre']} debe estar entre {minimo} y {maximo}."
                )

            return str(numero)

        return valor


def formatear_numero(valor):

    valor = float(valor)

    if valor.is_integer():

        return str(int(valor))

    return str(valor)
