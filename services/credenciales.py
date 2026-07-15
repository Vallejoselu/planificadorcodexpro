import json
import os
import stat
from pathlib import Path
from urllib.parse import urlparse


PREFIJO_ENTORNO = "env:"
ESQUEMA_LOCAL = "local"
VARIABLE_DIRECTORIO = "PLANIFICADOR_CREDENCIALES_DIR"


def directorio_credenciales_defecto():

    configurado = os.environ.get(VARIABLE_DIRECTORIO)

    if configurado:

        return Path(configurado)

    base = os.environ.get("APPDATA")

    if base:

        return Path(base) / "PlanificadorDeliveryPro" / "credenciales"

    return Path.home() / ".planificador_delivery_pro" / "credenciales"


def normalizar_parte_referencia(valor, etiqueta):

    valor = str(valor or "").strip().lower()

    if not valor:

        raise ValueError(f"{etiqueta} de credencial no valido.")

    permitido = valor.replace("_", "").replace("-", "")

    if not permitido.isalnum():

        raise ValueError(f"{etiqueta} de credencial no valido.")

    return valor


def referencia_entorno(variable):

    variable = str(variable or "").strip()

    if not variable or not variable.replace("_", "").isalnum():

        raise ValueError("Variable de entorno de credencial no valida.")

    return f"{PREFIJO_ENTORNO}{variable}"


def referencia_local(proveedor, nombre="principal"):

    proveedor = normalizar_parte_referencia(proveedor, "Proveedor")
    nombre = normalizar_parte_referencia(nombre, "Nombre")

    return f"{ESQUEMA_LOCAL}://{proveedor}/{nombre}"


def validar_referencia_credenciales(referencia):

    referencia = str(referencia or "").strip()

    if not referencia:

        return ""

    if referencia.startswith(PREFIJO_ENTORNO):

        referencia_entorno(referencia[len(PREFIJO_ENTORNO):])
        return referencia

    partes = urlparse(referencia)

    if partes.scheme != ESQUEMA_LOCAL:

        raise ValueError(
            "Las credenciales deben guardarse como referencia "
            "env:VARIABLE o local://proveedor/nombre."
        )

    proveedor = partes.netloc
    nombre = partes.path.strip("/")

    if "/" in nombre:

        raise ValueError("Referencia local de credencial no valida.")

    return referencia_local(proveedor, nombre)


def enmascarar_referencia(referencia):

    referencia = validar_referencia_credenciales(referencia)

    if not referencia:

        return ""

    if referencia.startswith(PREFIJO_ENTORNO):

        return "env:***"

    partes = urlparse(referencia)

    return f"{ESQUEMA_LOCAL}://{partes.netloc}/***"


class GestorCredencialesIntegracion:

    def __init__(self, directorio=None):

        self.directorio = Path(directorio or directorio_credenciales_defecto())

    def guardar_local(self, proveedor, nombre, valores):

        referencia = referencia_local(proveedor, nombre)
        ruta = self.ruta_local(referencia)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.aplicar_permisos_directorio(ruta.parent)
        datos = {
            "proveedor": normalizar_parte_referencia(proveedor, "Proveedor"),
            "nombre": normalizar_parte_referencia(nombre, "Nombre"),
            "valores": dict(valores or {})
        }

        with ruta.open("w", encoding="utf-8") as archivo:

            json.dump(datos, archivo, ensure_ascii=False, indent=2)

        self.aplicar_permisos_archivo(ruta)

        return referencia

    def obtener(self, referencia):

        referencia = validar_referencia_credenciales(referencia)

        if not referencia:

            return {}

        if referencia.startswith(PREFIJO_ENTORNO):

            variable = referencia[len(PREFIJO_ENTORNO):]
            valor = os.environ.get(variable)

            return {"valor": valor} if valor is not None else {}

        ruta = self.ruta_local(referencia)

        if not ruta.exists():

            return {}

        with ruta.open("r", encoding="utf-8") as archivo:

            return json.load(archivo).get("valores", {})

    def existe(self, referencia):

        referencia = validar_referencia_credenciales(referencia)

        if not referencia:

            return False

        if referencia.startswith(PREFIJO_ENTORNO):

            variable = referencia[len(PREFIJO_ENTORNO):]
            return os.environ.get(variable) is not None

        return self.ruta_local(referencia).exists()

    def eliminar(self, referencia):

        referencia = validar_referencia_credenciales(referencia)

        if not referencia or referencia.startswith(PREFIJO_ENTORNO):

            return False

        ruta = self.ruta_local(referencia)

        if not ruta.exists():

            return False

        ruta.unlink()

        return True

    def estado(self, referencia):

        referencia = validar_referencia_credenciales(referencia)

        return {
            "referencia": referencia,
            "mascara": enmascarar_referencia(referencia),
            "configurada": bool(referencia),
            "disponible": self.existe(referencia) if referencia else False
        }

    def ruta_local(self, referencia):

        referencia = validar_referencia_credenciales(referencia)
        partes = urlparse(referencia)

        if partes.scheme != ESQUEMA_LOCAL:

            raise ValueError("La referencia no corresponde al almacen local.")

        proveedor = normalizar_parte_referencia(partes.netloc, "Proveedor")
        nombre = normalizar_parte_referencia(
            partes.path.strip("/"),
            "Nombre"
        )

        return self.directorio / proveedor / f"{nombre}.json"

    @staticmethod
    def aplicar_permisos_directorio(ruta):

        try:

            ruta.chmod(stat.S_IRWXU)

        except OSError:

            pass

    @staticmethod
    def aplicar_permisos_archivo(ruta):

        try:

            ruta.chmod(stat.S_IRUSR | stat.S_IWUSR)

        except OSError:

            pass
