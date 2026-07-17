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
from ui.widgets import PageHeader, configure_table


reglas_service = ReglasConfigurablesService()


class VistaReglas(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)
        self.layout.addWidget(
            PageHeader(
                "Reglas configurables",
                (
                    "Consulta y prepara las reglas que utiliza el motor "
                    "de planificacion."
                )
            )
        )

        self.resumen = QLabel("")
        self.resumen.setWordWrap(True)
        self.resumen.setObjectName("infoPanel")
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
        self.configurar_tabla()
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(
            QAbstractItemView.DoubleClicked
            | QAbstractItemView.EditKeyPressed
        )
        self.layout.addWidget(self.tabla)

        self.btn_guardar.clicked.connect(self.guardar_configuracion)
        self.btn_restaurar.clicked.connect(self.restaurar_valores)

        self.cargar_datos()

    def configurar_tabla(self):

        self.tabla.setWordWrap(True)
        self.tabla.verticalHeader().setDefaultSectionSize(58)
        self.tabla.verticalHeader().setMinimumSectionSize(44)
        self.tabla.horizontalHeader().setStretchLastSection(False)
        self.tabla.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.Stretch
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.ResizeToContents
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            3,
            QHeaderView.Stretch
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            4,
            QHeaderView.ResizeToContents
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            5,
            QHeaderView.ResizeToContents
        )
        self.tabla.setColumnWidth(0, 260)
        self.tabla.setColumnWidth(3, 260)

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
            item_nombre.setToolTip(regla["nombre"])
            item_nombre.setFlags(item_nombre.flags() & ~Qt.ItemIsEditable)
            self.tabla.setItem(
                fila,
                0,
                item_nombre
            )
            self.set_item(fila, 1, regla["valor"])
            item_preparado = QTableWidgetItem(regla["valor_configurado"])
            item_preparado.setToolTip(regla["valor_configurado"])

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
            self.set_item(fila, 3, regla["origen"])
            self.set_item(fila, 4, "Si" if regla["editable"] else "No")
            self.set_item(fila, 5, "14.9B")

        self.tabla.resizeRowsToContents()

    def set_item(self, fila, columna, valor):

        item = QTableWidgetItem(str(valor))
        item.setToolTip(str(valor))
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        self.tabla.setItem(fila, columna, item)

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
