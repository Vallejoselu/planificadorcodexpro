import json
from datetime import datetime, timedelta

from repositories.sincronizaciones_repository import SincronizacionesRepository


ESTADO_PENDIENTE = "pendiente"
ESTADO_COMPLETADO = "completado"
ESTADO_REINTENTO = "reintento"
ESTADO_ERROR = "error"
ESTADO_AGOTADO = "agotado"


class ServicioSincronizacion:

    def __init__(self, repository=None):

        self.repository = repository or SincronizacionesRepository()

    def registrar_pendiente(
        self,
        proveedor,
        accion,
        payload=None,
        max_reintentos=3,
        proximo_intento=None
    ):

        return self.repository.registrar(
            proveedor,
            accion,
            ESTADO_PENDIENTE,
            serializar(payload),
            "",
            "",
            0,
            max_reintentos,
            proximo_intento
        )

    def registrar_completado(self, sincronizacion_id, respuesta=None):

        self.repository.actualizar(
            sincronizacion_id,
            ESTADO_COMPLETADO,
            serializar(respuesta),
            "",
            proximo_intento=None
        )

        return self.repository.obtener(sincronizacion_id)

    def registrar_error(
        self,
        sincronizacion_id,
        error,
        respuesta=None,
        ahora=None,
        base_minutos=15
    ):

        sincronizacion = self.repository.obtener(sincronizacion_id)

        if not sincronizacion:

            raise ValueError("Sincronizacion no encontrada.")

        intentos = int(sincronizacion[7] or 0) + 1
        max_reintentos = int(sincronizacion[8] or 0)

        if intentos >= max_reintentos:

            estado = ESTADO_AGOTADO
            proximo_intento = None

        else:

            estado = ESTADO_REINTENTO
            proximo_intento = calcular_proximo_intento(
                intentos,
                ahora,
                base_minutos
            )

        self.repository.actualizar(
            sincronizacion_id,
            estado,
            serializar(respuesta),
            str(error or ""),
            intentos,
            proximo_intento
        )

        return self.repository.obtener(sincronizacion_id)

    def listar_pendientes(self, ahora=None, limite=100):

        ahora = formatear_fecha_hora(ahora or datetime.now())

        return self.repository.listar_pendientes(ahora, limite)

    def listar(self, limite=100, estado=None, proveedor=None):

        return self.repository.listar(limite, estado, proveedor)


def calcular_proximo_intento(intentos, ahora=None, base_minutos=15):

    ahora = ahora or datetime.now()
    retraso = int(base_minutos) * (2 ** max(0, int(intentos) - 1))

    return formatear_fecha_hora(ahora + timedelta(minutes=retraso))


def formatear_fecha_hora(valor):

    if isinstance(valor, datetime):

        return valor.replace(microsecond=0).isoformat(sep=" ")

    return str(valor)


def serializar(valor):

    if valor is None:

        return ""

    if isinstance(valor, str):

        return valor

    return json.dumps(valor, ensure_ascii=False, sort_keys=True)
