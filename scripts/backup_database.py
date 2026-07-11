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


def main():

    parser = argparse.ArgumentParser(
        description="Crear una copia de seguridad de delivery.db."
    )
    parser.add_argument(
        "--database",
        default=str(RUTA_BD),
        help="Ruta de la base de datos a copiar."
    )
    parser.add_argument(
        "--backup-dir",
        default=str(ROOT / "backups"),
        help="Carpeta donde guardar la copia."
    )
    args = parser.parse_args()

    database = Path(args.database).resolve()
    backup_dir = Path(args.backup_dir).resolve()

    backup = create_backup(database, backup_dir)

    print(f"Copia creada correctamente: {backup}")
    return 0


def create_backup(database, backup_dir):

    if not database.exists():

        raise FileNotFoundError(f"No existe la base de datos: {database}")

    validate_sqlite(database)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"{database.stem}-{timestamp}.db"
    counter = 1

    while backup.exists():

        backup = backup_dir / f"{database.stem}-{timestamp}-{counter}.db"
        counter += 1

    shutil.copy2(database, backup)
    validate_sqlite(backup)

    return backup


def validate_sqlite(path):

    try:

        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        connection.execute("PRAGMA schema_version").fetchone()
        connection.close()

    except sqlite3.Error as error:

        raise ValueError(f"No es una base SQLite valida: {path}") from error


if __name__ == "__main__":

    raise SystemExit(main())
