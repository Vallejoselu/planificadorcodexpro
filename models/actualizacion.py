from dataclasses import dataclass


@dataclass
class ActualizacionDisponible:

    version: str
    url: str = ""
    sha256: str = ""
    notas: str = ""
    obligatoria: bool = False


@dataclass
class ResultadoActualizacion:

    correcto: bool
    mensaje: str
    disponible: bool = False
    actualizacion: ActualizacionDisponible | None = None
    ruta_descarga: str = ""
