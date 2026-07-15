import json

from models.integracion import ConfiguracionIntegracion
from repositories.integraciones_repository import IntegracionesRepository
from services.integraciones.generica import IntegracionGenerica
from services.integraciones.glovo import GlovoIntegracion
from services.integraciones.shipday import ShipdayIntegracion
from services.integraciones.uber import UberIntegracion
from services.credenciales import validar_referencia_credenciales


PROVEEDORES = {
    ShipdayIntegracion.proveedor: ShipdayIntegracion,
    GlovoIntegracion.proveedor: GlovoIntegracion,
    UberIntegracion.proveedor: UberIntegracion,
    IntegracionGenerica.proveedor: IntegracionGenerica
}
integraciones_repository = IntegracionesRepository()


def obtener_proveedores_disponibles():

    return [
        {
            "proveedor": proveedor,
            "nombre": clase.nombre
        }
        for proveedor, clase in sorted(PROVEEDORES.items())
    ]


def crear_integracion(proveedor):

    clase = PROVEEDORES.get(proveedor, IntegracionGenerica)
    configuracion = cargar_configuracion(proveedor, clase)

    return clase(configuracion)


def cargar_configuracion(proveedor, clase=None):

    datos = integraciones_repository.obtener_configuracion(proveedor)

    if not datos:

        clase = clase or PROVEEDORES.get(proveedor, IntegracionGenerica)

        return ConfiguracionIntegracion(
            proveedor=proveedor,
            nombre=clase.nombre
        )

    opciones = {}

    if datos[5]:

        try:

            opciones = json.loads(datos[5])

        except json.JSONDecodeError:

            opciones = {}

    return ConfiguracionIntegracion(
        proveedor=datos[0],
        nombre=datos[1],
        activo=bool(datos[2]),
        base_url=datos[3] or "",
        credenciales_referencia=datos[4] or "",
        opciones=opciones
    )


def guardar_configuracion(configuracion):

    credenciales_referencia = validar_referencia_credenciales(
        configuracion.credenciales_referencia
    )

    integraciones_repository.guardar_configuracion(
        configuracion.proveedor,
        configuracion.nombre,
        int(configuracion.activo),
        configuracion.base_url,
        credenciales_referencia,
        json.dumps(configuracion.opciones)
    )


def ejecutar_accion(proveedor, accion, *args, **kwargs):

    integracion = crear_integracion(proveedor)
    metodo = getattr(integracion, accion)
    resultado = metodo(*args, **kwargs)

    integraciones_repository.registrar_evento(
        resultado.proveedor,
        resultado.accion,
        "OK" if resultado.correcto else "PENDIENTE",
        resultado.mensaje
    )

    return resultado
