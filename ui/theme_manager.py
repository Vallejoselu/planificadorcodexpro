from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from app_info import APP_ID
from utils.paths import resource_path

STYLES_DIR = resource_path("resources", "styles")
THEMES = {
    "light": STYLES_DIR / "light.qss",
    "dark": STYLES_DIR / "dark.qss"
}


class ThemeManager:

    ORGANIZATION = APP_ID
    APPLICATION = APP_ID
    KEY = "ui/theme"

    @classmethod
    def settings(cls):

        return QSettings(cls.ORGANIZATION, cls.APPLICATION)

    @classmethod
    def current_theme(cls):

        theme = cls.settings().value(cls.KEY, "light")

        if theme not in THEMES:

            return "light"

        return theme

    @classmethod
    def set_theme(cls, theme):

        if theme not in THEMES:

            theme = "light"

        cls.settings().setValue(cls.KEY, theme)
        cls.apply_theme(theme)

    @classmethod
    def apply_saved_theme(cls):

        cls.apply_theme(cls.current_theme())

    @classmethod
    def apply_theme(cls, theme):

        app = QApplication.instance()

        if not app:

            return

        path = THEMES.get(theme, THEMES["light"])

        try:

            style = path.read_text(encoding="utf-8")

        except OSError:

            raise RuntimeError(
                f"No se ha encontrado el archivo de estilo: {path}"
            )

        app.setStyleSheet(style)
        app.setProperty("theme", theme)
