import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

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


def exportar_base(destino, ruta_bd=None):

    if not destino:

        raise ValueError("Selecciona un archivo de destino.")

    return crear_backup(destino=destino, ruta_bd=ruta_bd)


def restaurar_backup(origen, ruta_bd=None, crear_respaldo=True):

    origen = Path(origen)

    if not origen.exists():

        raise ValueError("El archivo seleccionado no existe.")

    validar_base_sqlite(origen)

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
        "respaldo": respaldo
    }


def importar_base(origen, ruta_bd=None):

    return restaurar_backup(origen, ruta_bd=ruta_bd, crear_respaldo=True)


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


def ruta_backup_por_defecto(ruta_bd=None, prefijo="backup"):

    ruta = Path(ruta_bd or database_path())
    carpeta = backups_dir() if ruta == database_path() else ruta.parent / "backups"
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M%S")
    return carpeta / f"{prefijo}-{ruta.stem}-{marca}.db"
