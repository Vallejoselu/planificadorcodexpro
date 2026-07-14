from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from services.reglas_configurables import ReglasConfigurablesService
from ui.widgets import configure_table


reglas_service = ReglasConfigurablesService()


class VistaReglas(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Reglas configurables")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)
        self.layout.addWidget(titulo)

        self.resumen = QLabel("")
        self.layout.addWidget(self.resumen)

        self.tabla = QTableWidget()
        configure_table(self.tabla)
        self.tabla.setColumnCount(5)
        self.tabla.setHorizontalHeaderLabels([
            "Regla",
            "Valor actual",
            "Origen",
            "Editable",
            "Fase"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.layout.addWidget(self.tabla)

        self.cargar_datos()

    def cargar_datos(self):

        reglas = reglas_service.listar_reglas()
        resumen = reglas_service.resumen()

        self.resumen.setText(
            f"Modo {resumen['modo']}: {resumen['total']} reglas visibles, "
            f"{resumen['editables']} editables."
        )
        self.tabla.setRowCount(len(reglas))

        for fila, regla in enumerate(reglas):

            self.tabla.setItem(
                fila,
                0,
                QTableWidgetItem(regla["nombre"])
            )
            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(regla["valor"])
            )
            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem(regla["origen"])
            )
            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem("Si" if regla["editable"] else "No")
            )
            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem("14.9A")
            )
