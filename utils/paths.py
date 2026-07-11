import os
import sys
from pathlib import Path

from app_info import APP_ID


BASE_DIR = Path(__file__).resolve().parent.parent


def is_frozen():

    return bool(getattr(sys, "frozen", False))


def resource_path(*parts):

    base = Path(getattr(sys, "_MEIPASS", BASE_DIR))

    return base.joinpath(*parts)


def user_data_dir():

    if not is_frozen():

        return BASE_DIR

    local_app_data = os.environ.get("LOCALAPPDATA")

    if local_app_data:

        return Path(local_app_data) / APP_ID

    return Path.home() / "AppData" / "Local" / APP_ID


def database_path():

    return user_data_dir() / "delivery.db"


def ensure_user_directories():

    user_data_dir().mkdir(parents=True, exist_ok=True)
