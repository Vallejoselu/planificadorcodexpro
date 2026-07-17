import sqlite3
from pathlib import Path

from utils.paths import database_path, ensure_user_directories


def conectar(ruta_bd=None):

    ruta = Path(ruta_bd or database_path())

    if ruta == database_path():

        ensure_user_directories()

    else:

        ruta.parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(ruta)
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion

