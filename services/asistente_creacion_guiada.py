from services.configuracion_guiada import ConfiguracionGuiadaService


class AsistenteCreacionGuiadaService:

    def __init__(self, configuracion_service=None):

        self.configuracion_service = (
            configuracion_service or ConfiguracionGuiadaService()
        )

    def obtener_flujo(self):

        diagnostico = self.configuracion_service.diagnosticar()
        pasos = diagnostico["pasos"]
        total = len(pasos)
        pasos_guiados = []

        for indice, paso in enumerate(pasos):

            pasos_guiados.append({
                "numero": indice + 1,
                "total": total,
                "codigo": paso["codigo"],
                "titulo": paso["titulo"],
                "estado": paso["estado"],
                "detalle": paso["detalle"],
                "pagina": paso["pagina"],
                "accion": self.accion_para_paso(paso)
            })

        indice_recomendado = self.indice_recomendado(pasos_guiados)

        return {
            "pasos": pasos_guiados,
            "indice_recomendado": indice_recomendado,
            "resumen": diagnostico["resumen"],
            "listo": diagnostico["listo"]
        }

    def indice_recomendado(self, pasos):

        for indice, paso in enumerate(pasos):

            if paso["estado"] != ConfiguracionGuiadaService.ESTADO_OK:

                return indice

        return max(0, len(pasos) - 1)

    def accion_para_paso(self, paso):

        acciones = {
            "ciudades": "Crear o revisar ciudades",
            "restaurantes": "Crear o revisar restaurantes",
            "turnos": "Crear o revisar turnos",
            "demanda": "Configurar demanda por zona o local",
            "repartidores": "Crear o revisar repartidores",
            "disponibilidad": "Revisar disponibilidad",
            "autorizaciones": "Revisar destinos y autorizaciones",
            "generacion": "Ir a cuadrantes"
        }

        return acciones.get(paso["codigo"], "Abrir pantalla")
