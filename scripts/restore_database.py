import argparse
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

if str(ROOT) not in sys.path:

    sys.path.insert(0, str(ROOT))

from database.database import RUTA_BD
from database.database import registrar_historial_accion
from database.migrations import crear_base_datos
from scripts.backup_database import create_backup, validate_sqlite


def main():

    parser = argparse.ArgumentParser(
        description="Restaurar delivery.db desde una copia de seguridad."
    )
    parser.add_argument(
        "--database",
        default=str(RUTA_BD),
        help="Base de datos que sera reemplazada."
    )
    parser.add_argument(
        "--backup-dir",
        default=str(ROOT / "backups"),
        help="Carpeta de copias disponibles."
    )
    args = parser.parse_args()

    database = Path(args.database).resolve()
    backup_dir = Path(args.backup_dir).resolve()
    backups = list_backups(backup_dir)

    if not backups:

        print(f"No hay copias disponibles en {backup_dir}")
        return 1

    print("Copias disponibles:")

    for index, backup in enumerate(backups, start=1):

        print(f"{index}. {backup.name}")

    selected = input("Numero de copia a restaurar: ").strip()

    if not selected.isdigit() or not 1 <= int(selected) <= len(backups):

        print("Seleccion no valida. No se ha restaurado nada.")
        return 1

    backup = backups[int(selected) - 1]
    validate_sqlite(backup)

    print("")
    print(f"Se reemplazara: {database}")
    print(f"Con la copia:  {backup}")
    confirmation = input("Escribe RESTAURAR para confirmar: ").strip()

    if confirmation != "RESTAURAR":

        print("Confirmacion cancelada. No se ha restaurado nada.")
        return 1

    if database.exists():

        safety_dir = backup_dir / "pre_restore"
        safety = create_backup(database, safety_dir)
        print(f"Copia previa creada: {safety}")

    database.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(backup, database)
    validate_sqlite(database)
    registrar_restauracion(database, backup)

    print("Restauracion completada correctamente.")
    return 0


def registrar_restauracion(database, backup):

    crear_base_datos(database)
    return registrar_historial_accion(
        "Restaurar backup",
        "backup",
        f"Restaurado desde {backup}",
        ruta_bd=database
    )


def list_backups(backup_dir):

    if not backup_dir.exists():

        return []

    backups = [
        path
        for path in backup_dir.glob("*.db")
        if path.is_file()
    ]

    return sorted(backups, key=lambda path: path.stat().st_mtime, reverse=True)


if __name__ == "__main__":

    raise SystemExit(main())
