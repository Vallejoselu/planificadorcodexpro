from repositories.calendario_repository import CalendarioRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository
from services.configuracion_guiada import ConfiguracionGuiadaService


class CentroOperativoService:

    MAX_PENDIENTES_VISIBLES = 4

    def __init__(
        self,
        configuracion_service=None,
        calendario_repository=None,
        repartidores_repository=None,
        restaurantes_repository=None,
        turnos_repository=None
    ):

        self.configuracion_service = (
            configuracion_service or ConfiguracionGuiadaService()
        )
        self.calendario_repository = (
            calendario_repository or CalendarioRepository()
        )
        self.repartidores_repository = (
            repartidores_repository or RepartidoresRepository()
        )
        self.restaurantes_repository = (
            restaurantes_repository or RestaurantesRepository()
        )
        self.turnos_repository = turnos_repository or TurnosRepository()

    def obtener_resumen(self):

        diagnostico = self.configuracion_service.diagnosticar()
        pasos = diagnostico.get("pasos", [])
        resumen = diagnostico.get("resumen", {})

        repartidores = self.repartidores_repository.listar_activos()
        restaurantes = self.restaurantes_repository.listar_activos()
        turnos = self.turnos_repository.listar_activos()
        calendario = self.calendario_repository.listar_semana()

        pendientes = self.pasos_relevantes(pasos)

        return {
            "estado": self.estado_principal(resumen),
            "detalle": self.detalle_estado(resumen),
            "nivel": self.nivel_estado(resumen),
            "metricas": self.metricas(
                repartidores,
                restaurantes,
                turnos,
                calendario
            ),
            "pendientes": pendientes,
            "accion": self.accion_recomendada(pendientes, calendario),
            "resumen": resumen
        }

    def pasos_relevantes(self, pasos):

        relevantes = [
            paso
            for paso in pasos
            if paso.get("estado") in ("pendiente", "aviso")
        ]
        relevantes.sort(key=self.prioridad_paso)
        visibles = relevantes[:self.MAX_PENDIENTES_VISIBLES]
        sobrantes = len(relevantes) - len(visibles)

        if sobrantes > 0:

            visibles.append({
                "titulo": "Mas puntos",
                "estado": "aviso",
                "detalle": f"Hay {sobrantes} punto(s) mas para revisar.",
                "pagina": "puesta_marcha"
            })

        return visibles

    def prioridad_paso(self, paso):

        estado = paso.get("estado")

        if estado == "pendiente":

            return 0

        if estado == "aviso":

            return 1

        return 2

    def estado_principal(self, resumen):

        pendientes = resumen.get("pendientes", 0)
        avisos = resumen.get("avisos", 0)

        if pendientes:

            return "Faltan datos para generar bien"

        if avisos:

            return "Se puede generar con advertencias"

        return "Listo para generar cuadrantes"

    def detalle_estado(self, resumen):

        pendientes = resumen.get("pendientes", 0)
        avisos = resumen.get("avisos", 0)

        if pendientes:

            return (
                f"Hay {pendientes} paso(s) pendiente(s). "
                "Resuelve primero lo imprescindible."
            )

        if avisos:

            return (
                f"Hay {avisos} aviso(s). Puedes continuar, "
                "pero conviene revisarlos antes de publicar."
            )

        return "La configuracion basica esta completa."

    def nivel_estado(self, resumen):

        if resumen.get("pendientes", 0):

            return "pendiente"

        if resumen.get("avisos", 0):

            return "aviso"

        return "ok"

    def metricas(self, repartidores, restaurantes, turnos, calendario):

        asignaciones = len(calendario)
        cubiertas = sum(
            1
            for asignacion in calendario
            if self.repartidor_id(asignacion)
        )

        return [
            {
                "clave": "repartidores",
                "titulo": "Repartidores",
                "valor": len(repartidores)
            },
            {
                "clave": "restaurantes",
                "titulo": "Restaurantes",
                "valor": len(restaurantes)
            },
            {
                "clave": "turnos",
                "titulo": "Turnos",
                "valor": len(turnos)
            },
            {
                "clave": "cuadrante",
                "titulo": "Cuadrante actual",
                "valor": (
                    f"{cubiertas}/{asignaciones}"
                    if asignaciones
                    else "Sin crear"
                )
            }
        ]

    def accion_recomendada(self, pendientes, calendario):

        if pendientes:

            paso = pendientes[0]

            return {
                "texto": f"Resolver {paso.get('titulo', 'pendiente')}",
                "pagina": paso.get("pagina") or "puesta_marcha"
            }

        if calendario:

            return {
                "texto": "Abrir cuadrante",
                "pagina": "cuadrantes"
            }

        return {
            "texto": "Generar cuadrante",
            "pagina": "cuadrantes"
        }

    def valor(self, fila, indice, defecto=None):

        if isinstance(fila, dict):

            return fila.get(indice, defecto)

        try:

            return fila[indice]

        except (IndexError, KeyError, TypeError):

            return defecto

    def repartidor_id(self, asignacion):

        if isinstance(asignacion, dict):

            return asignacion.get("repartidor_id")

        return self.valor(asignacion, 9)
