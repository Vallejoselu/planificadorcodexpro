import sqlite3

from utils.paths import database_path, ensure_user_directories


def conectar(ruta_bd=None):

    ensure_user_directories()
    conexion = sqlite3.connect(ruta_bd or database_path())
    conexion.execute("PRAGMA foreign_keys = ON")

    return conexion

