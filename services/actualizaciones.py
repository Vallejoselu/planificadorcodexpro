import hashlib
import json
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from app_info import UPDATE_MANIFEST_URL, VERSION
from models.actualizacion import ActualizacionDisponible, ResultadoActualizacion
from utils.paths import user_data_dir


class ServicioActualizaciones:

    def __init__(self, version_actual=VERSION, manifest_url=UPDATE_MANIFEST_URL):

        self.version_actual = version_actual
        self.manifest_url = manifest_url

    def comprobar(self):

        if not self.manifest_url:

            return ResultadoActualizacion(
                correcto=True,
                mensaje=(
                    "No hay servidor de actualizaciones configurado. "
                    "La arquitectura esta preparada para activarlo mas adelante."
                )
            )

        try:

            datos = self._leer_manifest()
            actualizacion = self._normalizar_manifest(datos)

        except (OSError, URLError, ValueError, json.JSONDecodeError) as error:

            return ResultadoActualizacion(
                correcto=False,
                mensaje=f"No se pudo comprobar actualizaciones: {error}"
            )

        if not version_mayor(actualizacion.version, self.version_actual):

            return ResultadoActualizacion(
                correcto=True,
                mensaje=f"La version {self.version_actual} esta actualizada."
            )

        return ResultadoActualizacion(
            correcto=True,
            disponible=True,
            actualizacion=actualizacion,
            mensaje=(
                f"Hay una actualizacion disponible: "
                f"{self.version_actual} -> {actualizacion.version}."
            )
        )

    def descargar(self, actualizacion, destino=None):

        if not actualizacion.url:

            return ResultadoActualizacion(
                correcto=False,
                mensaje="La actualizacion no tiene URL de descarga.",
                disponible=True,
                actualizacion=actualizacion
            )

        destino = Path(destino) if destino else self.directorio_descargas()
        destino.mkdir(parents=True, exist_ok=True)
        archivo = destino / f"PlanificadorDeliveryPro-{actualizacion.version}.exe"

        try:

            with urlopen(actualizacion.url, timeout=30) as respuesta:

                archivo.write_bytes(respuesta.read())

            if actualizacion.sha256:

                validar_sha256(archivo, actualizacion.sha256)

        except (OSError, URLError, ValueError) as error:

            return ResultadoActualizacion(
                correcto=False,
                mensaje=f"No se pudo descargar la actualizacion: {error}",
                disponible=True,
                actualizacion=actualizacion
            )

        return ResultadoActualizacion(
            correcto=True,
            mensaje=(
                "Actualizacion descargada. La base de datos del usuario "
                "permanece fuera de la carpeta de instalacion."
            ),
            disponible=True,
            actualizacion=actualizacion,
            ruta_descarga=str(archivo)
        )

    def mensaje_para_usuario(self, resultado):

        if resultado.disponible and resultado.actualizacion:

            notas = resultado.actualizacion.notas

            if notas:

                return resultado.mensaje + "\n\nNotas:\n" + notas

        return resultado.mensaje

    def directorio_descargas(self):

        return user_data_dir() / "updates"

    def _leer_manifest(self):

        with urlopen(self.manifest_url, timeout=15) as respuesta:

            return json.loads(respuesta.read().decode("utf-8"))

    def _normalizar_manifest(self, datos):

        version = str(datos.get("version", "")).strip()

        if not version:

            raise ValueError("El manifiesto no incluye version.")

        return ActualizacionDisponible(
            version=version,
            url=str(datos.get("url", "") or ""),
            sha256=str(datos.get("sha256", "") or ""),
            notas=str(datos.get("notas", "") or ""),
            obligatoria=bool(datos.get("obligatoria", False))
        )


def version_mayor(nueva, actual):

    return partes_version(nueva) > partes_version(actual)


def partes_version(version):

    partes = []

    for parte in str(version).split("."):

        try:

            partes.append(int(parte))

        except ValueError:

            partes.append(0)

    return tuple(partes)


def validar_sha256(ruta, esperado):

    digest = hashlib.sha256()

    with Path(ruta).open("rb") as archivo:

        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):

            digest.update(bloque)

    obtenido = digest.hexdigest()

    if obtenido.lower() != esperado.lower():

        raise ValueError("La firma SHA256 de la descarga no coincide.")
