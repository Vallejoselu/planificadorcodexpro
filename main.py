import sys
from PySide6.QtWidgets import QApplication, QMessageBox
from app_info import APP_NAME
from database.database import crear_base_datos
from ui.theme_manager import ThemeManager
from utils.paths import ensure_user_directories
from views.ventana_principal import VentanaPrincipal


def main():

    app = QApplication(sys.argv)

    try:

        ensure_user_directories()
        crear_base_datos()
        ThemeManager.apply_saved_theme()
        ventana = VentanaPrincipal()

        if "--smoke-test" in sys.argv:

            for pagina in list(ventana.paginas.keys()):

                ventana.mostrar_pagina(pagina)

            return 0

        ventana.show()
        return app.exec()

    except Exception as error:

        QMessageBox.critical(
            None,
            APP_NAME,
            "No se ha podido iniciar la aplicacion.\n\n"
            f"Detalle: {error}"
        )
        return 1


if __name__ == "__main__":

    sys.exit(main())
