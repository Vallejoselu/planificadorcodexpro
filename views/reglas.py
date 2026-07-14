from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
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

        barra = QHBoxLayout()
        self.btn_guardar = QPushButton("Guardar configuracion")
        self.btn_guardar.setProperty("variant", "primary")
        self.btn_restaurar = QPushButton("Restaurar valores")
        barra.addWidget(self.btn_guardar)
        barra.addWidget(self.btn_restaurar)
        barra.addStretch()
        self.layout.addLayout(barra)

        self.tabla = QTableWidget()
        configure_table(self.tabla)
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Regla",
            "Valor actual",
            "Valor preparado",
            "Origen",
            "Editable",
            "Fase"
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
        )
        self.layout.addWidget(self.tabla)

        self.btn_guardar.clicked.connect(self.guardar_configuracion)
        self.btn_restaurar.clicked.connect(self.restaurar_valores)

        self.cargar_datos()

    def cargar_datos(self):

        reglas = reglas_service.listar_reglas()
        resumen = reglas_service.resumen()

        self.resumen.setText(
            f"Modo {resumen['modo']}: {resumen['total']} reglas visibles, "
            f"{resumen['editables']} editables, "
            f"{resumen['configuradas']} configuradas."
        )
        self.tabla.setRowCount(len(reglas))

        for fila, regla in enumerate(reglas):

            item_nombre = QTableWidgetItem(regla["nombre"])
            item_nombre.setData(Qt.UserRole, regla["clave"])
            self.tabla.setItem(
                fila,
                0,
                item_nombre
            )
            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(regla["valor"])
            )
            item_preparado = QTableWidgetItem(regla["valor_configurado"])

            if regla["editable"]:

                item_preparado.setFlags(
                    item_preparado.flags()
                    | Qt.ItemIsEditable
                )

            else:

                item_preparado.setFlags(
                    item_preparado.flags()
                    & ~Qt.ItemIsEditable
                )

            self.tabla.setItem(
                fila,
                2,
                item_preparado
            )
            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(regla["origen"])
            )
            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem("Si" if regla["editable"] else "No")
            )
            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem("14.9B")
            )

    def guardar_configuracion(self):

        try:

            resultado = reglas_service.guardar_configuracion(
                self.valores_editables()
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Reglas",
                str(error)
            )
            return

        self.cargar_datos()
        QMessageBox.information(
            self,
            "Reglas",
            f"Reglas guardadas: {resultado['guardadas']}."
        )

    def restaurar_valores(self):

        resultado = reglas_service.restaurar_valores()
        self.cargar_datos()
        QMessageBox.information(
            self,
            "Reglas",
            f"Valores restaurados: {resultado['restauradas']}."
        )

    def valores_editables(self):

        valores = {}

        for fila in range(self.tabla.rowCount()):

            clave = self.tabla.item(fila, 0).data(Qt.UserRole)
            editable = self.tabla.item(fila, 4).text() == "Si"

            if not editable:

                continue

            valores[clave] = self.tabla.item(fila, 2).text()

        return valores
