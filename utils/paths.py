import os
import shutil
import sys
from pathlib import Path

from app_info import APP_ID


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR_ENV = "PLANIFICADOR_DELIVERY_DATA_DIR"


def is_frozen():

    return bool(getattr(sys, "frozen", False))


def resource_path(*parts):

    base = Path(getattr(sys, "_MEIPASS", BASE_DIR))

    return base.joinpath(*parts)


def user_data_dir():

    configured = os.environ.get(DATA_DIR_ENV)

    if configured:

        return Path(configured)

    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:

        return Path(local_app_data) / APP_ID

    return Path.home() / "AppData" / "Local" / APP_ID


def database_path():

    return user_data_dir() / "delivery.db"


def legacy_database_path():

    return BASE_DIR / "delivery.db"


def backups_dir():

    return user_data_dir() / "backups"


def ensure_user_directories():

    user_data_dir().mkdir(parents=True, exist_ok=True)
    backups_dir().mkdir(parents=True, exist_ok=True)


def migrate_legacy_database_if_needed(target=None, legacy=None):

    target = Path(target or database_path())
    legacy = Path(legacy or legacy_database_path())

    if target.exists():

        return False

    if not legacy.exists():

        return False

    if target.resolve() == legacy.resolve():

        return False

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy, target)
    return True
