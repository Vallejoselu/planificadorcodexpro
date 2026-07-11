from dataclasses import dataclass, field


@dataclass
class ConfiguracionIntegracion:

    proveedor: str
    nombre: str
    activo: bool = False
    base_url: str = ""
    credenciales_referencia: str = ""
    opciones: dict = field(default_factory=dict)


@dataclass
class ResultadoIntegracion:

    correcto: bool
    proveedor: str
    accion: str
    mensaje: str
    datos: dict = field(default_factory=dict)
