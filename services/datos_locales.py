import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from database.diagnostics import (
    diagnosticar_base_datos,
    reparar_base_datos
)
from database.migrations import crear_base_datos
from utils.paths import (
    backups_dir,
    database_path,
    ensure_user_directories,
    legacy_database_path,
    migrate_legacy_database_if_needed,
    user_data_dir
)


def informacion_almacenamiento(ruta_bd=None):

    ruta = Path(ruta_bd or database_path())
    carpeta_datos = ruta.parent
    carpeta_backups = backups_dir()

    return {
        "ruta_bd": ruta,
        "carpeta_datos": carpeta_datos,
        "carpeta_backups": carpeta_backups,
        "existe": ruta.exists(),
        "tamano_bytes": ruta.stat().st_size if ruta.exists() else 0,
        "legacy": legacy_database_path(),
        "carpeta_usuario": user_data_dir()
    }


def preparar_base_local(ruta_bd=None):

    ruta = Path(ruta_bd or database_path())

    if ruta == database_path():

        migrate_legacy_database_if_needed(ruta)

    crear_base_datos(ruta)
    return informacion_almacenamiento(ruta)


def crear_backup(destino=None, ruta_bd=None):

    ruta = Path(ruta_bd or database_path())
    crear_base_datos(ruta)
    validar_base_sqlite(ruta)

    destino = Path(destino) if destino else ruta_backup_por_defecto(ruta)
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ruta, destino)
    return destino


def listar_backups(limite=10, ruta_bd=None):

    ruta = Path(ruta_bd or database_path())
    carpeta = backups_dir() if ruta == database_path() else ruta.parent / "backups"

    if not carpeta.exists():

        return []

    backups = []

    for archivo in carpeta.glob("*.db"):

        stat = archivo.stat()
        backups.append({
            "ruta": archivo,
            "nombre": archivo.name,
            "tamano_bytes": stat.st_size,
            "modificado": datetime.fromtimestamp(stat.st_mtime)
        })

    backups.sort(key=lambda item: item["modificado"], reverse=True)
    return backups[:limite]


def diagnosticar_datos(ruta_bd=None):

    ruta = Path(ruta_bd or database_path())

    if not ruta.exists():

        return {
            "ok": False,
            "errores": ["La base de datos local no existe todavia."],
            "advertencias": [],
            "info": [f"Ruta esperada: {ruta}"]
        }

    validar_base_sqlite(ruta)
    diagnostico = diagnosticar_base_datos(ruta)
    diagnostico["resumen"] = resumen_diagnostico(diagnostico)
    return diagnostico


def reparar_datos(ruta_bd=None):

    ruta = Path(ruta_bd or database_path())

    if not ruta.exists():

        crear_base_datos(ruta)
        respaldo = None

    else:

        validar_base_sqlite(ruta)
        respaldo = crear_backup(ruta_bd=ruta)

    diagnostico = reparar_base_datos(ruta)
    diagnostico["respaldo"] = respaldo
    diagnostico["resumen"] = resumen_diagnostico(diagnostico)
    return diagnostico


def exportar_base(destino, ruta_bd=None):

    if not destino:

        raise ValueError("Selecciona un archivo de destino.")

    return crear_backup(destino=destino, ruta_bd=ruta_bd)


def restaurar_backup(origen, ruta_bd=None, crear_respaldo=True):

    origen = Path(origen)

    if not origen.exists():

        raise ValueError("El archivo seleccionado no existe.")

    validacion = validar_restauracion(origen)

    ruta = Path(ruta_bd or database_path())
    ruta.parent.mkdir(parents=True, exist_ok=True)

    respaldo = None

    if crear_respaldo and ruta.exists():

        respaldo = ruta_backup_por_defecto(ruta, prefijo="antes_restaurar")
        respaldo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ruta, respaldo)

    shutil.copy2(origen, ruta)
    crear_base_datos(ruta)

    return {
        "ruta_bd": ruta,
        "origen": origen,
        "respaldo": respaldo,
        "validacion": validacion
    }


def importar_base(origen, ruta_bd=None):

    return restaurar_backup(origen, ruta_bd=ruta_bd, crear_respaldo=True)


def validar_restauracion(origen):

    origen = Path(origen)
    validar_base_sqlite(origen)

    with tempfile.TemporaryDirectory() as temporal:

        copia = Path(temporal) / "validacion.db"
        shutil.copy2(origen, copia)
        crear_base_datos(copia)
        diagnostico = diagnosticar_base_datos(copia)

    if diagnostico["errores"]:

        raise ValueError(
            "La base seleccionada tiene errores criticos: "
            + "; ".join(diagnostico["errores"])
        )

    diagnostico["resumen"] = resumen_diagnostico(diagnostico)
    return diagnostico


def validar_base_sqlite(ruta):

    ruta = Path(ruta)

    try:

        conexion = sqlite3.connect(f"file:{ruta.as_posix()}?mode=ro", uri=True)
        cursor = conexion.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1"
        )
        cursor.fetchone()

    except sqlite3.DatabaseError as error:

        raise ValueError("El archivo no parece una base SQLite valida.") from error

    finally:

        try:

            conexion.close()

        except UnboundLocalError:

            pass

    return True


def resumen_diagnostico(diagnostico):

    errores = len(diagnostico.get("errores", []))
    advertencias = len(diagnostico.get("advertencias", []))

    if errores:

        return f"Critico: {errores} errores y {advertencias} advertencias."

    if advertencias:

        return f"Revisar: {advertencias} advertencias."

    return "Base de datos correcta."


def ruta_backup_por_defecto(ruta_bd=None, prefijo="backup"):

    ruta = Path(ruta_bd or database_path())
    carpeta = backups_dir() if ruta == database_path() else ruta.parent / "backups"
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    return carpeta / f"{prefijo}-{ruta.stem}-{marca}.db"
