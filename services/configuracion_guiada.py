from repositories.ciudades_repository import CiudadesRepository
from repositories.demandas_ciudad_repository import DemandasCiudadRepository
from repositories.demandas_zona_repository import DemandasZonaRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository


class ConfiguracionGuiadaService:

    ESTADO_OK = "ok"
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_AVISO = "aviso"

    def __init__(
        self,
        ciudades_repository=None,
        repartidores_repository=None,
        restaurantes_repository=None,
        turnos_repository=None,
        demandas_zona_repository=None,
        demandas_ciudad_repository=None
    ):

        self.ciudades_repository = ciudades_repository or CiudadesRepository()
        self.repartidores_repository = (
            repartidores_repository or RepartidoresRepository()
        )
        self.restaurantes_repository = (
            restaurantes_repository or RestaurantesRepository()
        )
        self.turnos_repository = turnos_repository or TurnosRepository()
        self.demandas_zona_repository = (
            demandas_zona_repository or DemandasZonaRepository()
        )
        self.demandas_ciudad_repository = (
            demandas_ciudad_repository or DemandasCiudadRepository()
        )

    def diagnosticar(self):

        ciudades = self.ciudades_repository.listar_activas()
        repartidores = self.repartidores_repository.listar_activos()
        restaurantes = self.restaurantes_repository.listar_activos()
        turnos = self.turnos_repository.listar_activos()
        restaurante_turnos = self.turnos_restaurante(restaurantes)
        demandas_restaurante = self.demandas_restaurante(restaurantes)
        demandas_zona = [
            demanda
            for demanda in self.demandas_zona_repository.listar()
            if self.demanda_activa(demanda, 6)
        ]
        demandas_ciudad = [
            demanda
            for demanda in self.demandas_ciudad_repository.listar()
            if self.demanda_activa(demanda, 7)
        ]

        pasos = [
            self.paso_ciudades(ciudades),
            self.paso_restaurantes(restaurantes),
            self.paso_turnos(turnos, restaurante_turnos),
            self.paso_demanda(
                restaurantes,
                demandas_restaurante,
                demandas_zona,
                demandas_ciudad
            ),
            self.paso_repartidores(repartidores),
            self.paso_disponibilidad(repartidores),
            self.paso_autorizaciones(repartidores),
            self.paso_generacion(
                repartidores,
                restaurantes,
                turnos,
                restaurante_turnos,
                demandas_restaurante,
                demandas_zona,
                demandas_ciudad
            )
        ]
        resumen = self.resumen(pasos)

        return {
            "pasos": pasos,
            "resumen": resumen,
            "listo": resumen["pendientes"] == 0
        }

    def paso(self, codigo, titulo, estado, detalle, pagina):

        return {
            "codigo": codigo,
            "titulo": titulo,
            "estado": estado,
            "detalle": detalle,
            "pagina": pagina
        }

    def paso_ciudades(self, ciudades):

        if ciudades:

            return self.paso(
                "ciudades",
                "Ciudades",
                self.ESTADO_OK,
                f"{len(ciudades)} ciudades activas.",
                "ciudades"
            )

        return self.paso(
            "ciudades",
            "Ciudades",
            self.ESTADO_AVISO,
            "No hay ciudades activas. Puedes trabajar, pero conviene crearlas.",
            "ciudades"
        )

    def paso_restaurantes(self, restaurantes):

        if not restaurantes:

            return self.paso(
                "restaurantes",
                "Restaurantes",
                self.ESTADO_PENDIENTE,
                "No hay restaurantes activos.",
                "restaurantes"
            )

        sin_ciudad = [
            restaurante
            for restaurante in restaurantes
            if not self.valor(restaurante, 9)
        ]

        if sin_ciudad:

            return self.paso(
                "restaurantes",
                "Restaurantes",
                self.ESTADO_AVISO,
                (
                    f"{len(restaurantes)} restaurantes activos; "
                    f"{len(sin_ciudad)} sin ciudad asignada."
                ),
                "restaurantes"
            )

        return self.paso(
            "restaurantes",
            "Restaurantes",
            self.ESTADO_OK,
            f"{len(restaurantes)} restaurantes activos con ciudad.",
            "restaurantes"
        )

    def paso_turnos(self, turnos, restaurante_turnos):

        total = len(turnos) + len(restaurante_turnos)

        if total:

            return self.paso(
                "turnos",
                "Turnos",
                self.ESTADO_OK,
                (
                    f"{len(turnos)} turnos globales y "
                    f"{len(restaurante_turnos)} turnos propios."
                ),
                "turnos"
            )

        return self.paso(
            "turnos",
            "Turnos",
            self.ESTADO_AVISO,
            "No hay turnos configurados; el generador creara turnos base.",
            "turnos"
        )

    def paso_demanda(
        self,
        restaurantes,
        demandas_restaurante,
        demandas_zona,
        demandas_ciudad
    ):

        total = (
            len(demandas_restaurante)
            + len(demandas_zona)
            + len(demandas_ciudad)
        )

        if not restaurantes:

            return self.paso(
                "demanda",
                "Demanda",
                self.ESTADO_PENDIENTE,
                "Crea restaurantes antes de configurar demanda.",
                "restaurantes"
            )

        if total:

            return self.paso(
                "demanda",
                "Demanda",
                self.ESTADO_OK,
                (
                    f"{len(demandas_restaurante)} por restaurante, "
                    f"{len(demandas_zona)} por zona y "
                    f"{len(demandas_ciudad)} por ciudad."
                ),
                "configuracion"
            )

        return self.paso(
            "demanda",
            "Demanda",
            self.ESTADO_AVISO,
            "No hay demanda configurada; la cobertura no sera realista.",
            "configuracion"
        )

    def paso_repartidores(self, repartidores):

        if repartidores:

            return self.paso(
                "repartidores",
                "Repartidores",
                self.ESTADO_OK,
                f"{len(repartidores)} repartidores activos.",
                "repartidores"
            )

        return self.paso(
            "repartidores",
            "Repartidores",
            self.ESTADO_PENDIENTE,
            "No hay repartidores activos.",
            "repartidores"
        )

    def paso_disponibilidad(self, repartidores):

        if not repartidores:

            return self.paso(
                "disponibilidad",
                "Disponibilidad",
                self.ESTADO_PENDIENTE,
                "Crea repartidores antes de configurar disponibilidad.",
                "repartidores"
            )

        sin_disponibilidad = [
            repartidor
            for repartidor in repartidores
            if not self.valor(repartidor, 11)
        ]

        if sin_disponibilidad:

            return self.paso(
                "disponibilidad",
                "Disponibilidad",
                self.ESTADO_AVISO,
                (
                    f"{len(sin_disponibilidad)} repartidores sin "
                    "disponibilidad semanal configurada."
                ),
                "repartidores"
            )

        return self.paso(
            "disponibilidad",
            "Disponibilidad",
            self.ESTADO_OK,
            "Todos los repartidores activos tienen disponibilidad.",
            "repartidores"
        )

    def paso_autorizaciones(self, repartidores):

        if not repartidores:

            return self.paso(
                "autorizaciones",
                "Autorizaciones",
                self.ESTADO_PENDIENTE,
                "Crea repartidores antes de configurar autorizaciones.",
                "repartidores"
            )

        sin_destino = [
            repartidor
            for repartidor in repartidores
            if not self.repartidor_tiene_destino(repartidor)
        ]

        if sin_destino:

            return self.paso(
                "autorizaciones",
                "Autorizaciones",
                self.ESTADO_AVISO,
                (
                    f"{len(sin_destino)} repartidores sin ciudad, "
                    "restaurante, autorizacion o apoyo flexible."
                ),
                "repartidores"
            )

        return self.paso(
            "autorizaciones",
            "Autorizaciones",
            self.ESTADO_OK,
            "Los repartidores tienen destino principal, autorizacion o apoyo.",
            "repartidores"
        )

    def paso_generacion(
        self,
        repartidores,
        restaurantes,
        turnos,
        restaurante_turnos,
        demandas_restaurante,
        demandas_zona,
        demandas_ciudad
    ):

        bloqueantes = []

        if not repartidores:

            bloqueantes.append("repartidores")

        if not restaurantes:

            bloqueantes.append("restaurantes")

        if bloqueantes:

            return self.paso(
                "generacion",
                "Generacion",
                self.ESTADO_PENDIENTE,
                "Faltan datos bloqueantes: " + ", ".join(bloqueantes) + ".",
                "cuadrantes"
            )

        avisos = []

        if not turnos and not restaurante_turnos:

            avisos.append("sin turnos configurados")

        if not (demandas_restaurante or demandas_zona or demandas_ciudad):

            avisos.append("sin demanda real")

        if avisos:

            return self.paso(
                "generacion",
                "Generacion",
                self.ESTADO_AVISO,
                "Se puede generar con advertencias: " + ", ".join(avisos) + ".",
                "cuadrantes"
            )

        return self.paso(
            "generacion",
            "Generacion",
            self.ESTADO_OK,
            "La empresa esta lista para generar cuadrantes.",
            "cuadrantes"
        )

    def resumen(self, pasos):

        pendientes = sum(
            1
            for paso in pasos
            if paso["estado"] == self.ESTADO_PENDIENTE
        )
        avisos = sum(
            1
            for paso in pasos
            if paso["estado"] == self.ESTADO_AVISO
        )
        correctos = sum(
            1
            for paso in pasos
            if paso["estado"] == self.ESTADO_OK
        )
        estado = (
            "Lista para generar cuadrantes"
            if pendientes == 0 and avisos == 0
            else "Puede generar con advertencias"
            if pendientes == 0
            else "Configuracion incompleta"
        )

        return {
            "estado": estado,
            "correctos": correctos,
            "avisos": avisos,
            "pendientes": pendientes,
            "total": len(pasos)
        }

    def turnos_restaurante(self, restaurantes):

        turnos = []

        for restaurante in restaurantes:

            turnos.extend(
                [
                    turno
                    for turno in self.restaurantes_repository.listar_turnos(
                        self.valor(restaurante, 0)
                    )
                    if self.demanda_activa(turno, 7)
                ]
            )

        return turnos

    def demandas_restaurante(self, restaurantes):

        demandas = []

        for restaurante in restaurantes:

            demandas.extend(
                [
                    demanda
                    for demanda in self.restaurantes_repository.listar_demanda(
                        self.valor(restaurante, 0)
                    )
                    if self.demanda_activa(demanda, 6)
                ]
            )

        return demandas

    def repartidor_tiene_destino(self, repartidor):

        return any((
            self.valor(repartidor, 15),
            self.valor(repartidor, 16),
            self.valor(repartidor, 17),
            self.valor(repartidor, 21),
            self.valor(repartidor, 22)
        ))

    def demanda_activa(self, fila, indice):

        return bool(self.valor(fila, indice))

    def valor(self, fila, indice, defecto=None):

        if fila is None:

            return defecto

        if isinstance(fila, dict):

            return fila.get(indice, defecto)

        try:

            return fila[indice]

        except (IndexError, KeyError, TypeError):

            return defecto
