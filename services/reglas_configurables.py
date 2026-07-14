class ReglasConfigurablesService:

    def listar_reglas(self):

        return [
            {
                "clave": "descanso_consecutivo",
                "nombre": "Descanso de dos dias consecutivos",
                "valor": "Obligatorio",
                "origen": "services.rules.descansos",
                "editable": False
            },
            {
                "clave": "disponibilidad",
                "nombre": "Disponibilidad semanal",
                "valor": "Obligatoria por dia y turno",
                "origen": "services.rules.disponibilidad",
                "editable": False
            },
            {
                "clave": "vacaciones_bajas",
                "nombre": "Vacaciones y bajas",
                "valor": "Bloquean asignacion",
                "origen": "services.rules.ausencias",
                "editable": False
            },
            {
                "clave": "solapamientos",
                "nombre": "Solapamientos horarios",
                "valor": "No permitidos",
                "origen": "services.rules.candidatos",
                "editable": False
            },
            {
                "clave": "horas_contratadas",
                "nombre": "Horas contratadas",
                "valor": "10, 20, 25, 30, 35, 40",
                "origen": "database.schema",
                "editable": False
            },
            {
                "clave": "horas_complementarias",
                "nombre": "Horas complementarias",
                "valor": "Segun repartidor",
                "origen": "services.rules.candidatos",
                "editable": False
            },
            {
                "clave": "max_horas_diarias",
                "nombre": "Maximo de horas diarias",
                "valor": "Segun repartidor",
                "origen": "services.rules.candidatos",
                "editable": False
            },
            {
                "clave": "max_dias_consecutivos",
                "nombre": "Maximo de dias consecutivos",
                "valor": "Segun repartidor",
                "origen": "services.rules.candidatos",
                "editable": False
            },
            {
                "clave": "autorizaciones",
                "nombre": "Restaurantes y ciudades autorizadas",
                "valor": "Principal, autorizados o apoyo flexible",
                "origen": "services.rules.candidatos",
                "editable": False
            },
            {
                "clave": "prioridad_demanda",
                "nombre": "Prioridad de demanda",
                "valor": "Restaurante > zona > ciudad > defecto",
                "origen": "services.demanda",
                "editable": False
            }
        ]

    def resumen(self):

        reglas = self.listar_reglas()
        editables = [
            regla
            for regla in reglas
            if regla["editable"]
        ]

        return {
            "total": len(reglas),
            "editables": len(editables),
            "modo": "lectura"
        }
