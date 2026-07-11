from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from database.database import (
    actualizar_ciudad,
    insertar_ciudad,
    obtener_ciudad,
    obtener_ciudades
)
from ui.widgets import configure_table


class VistaCiudades(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Gestion de ciudades")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)
        self.layout.addWidget(titulo)

        barra = QHBoxLayout()
        self.btn_nueva = QPushButton("Nueva ciudad")
        self.btn_nueva.setProperty("variant", "primary")
        self.btn_editar = QPushButton("Editar")
        self.btn_actualizar = QPushButton("Actualizar")

        barra.addWidget(self.btn_nueva)
        barra.addWidget(self.btn_editar)
        barra.addWidget(self.btn_actualizar)
        barra.addStretch()
        self.layout.addLayout(barra)

        self.tabla = QTableWidget()
        configure_table(self.tabla)
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Activo"
        ])
        self.layout.addWidget(self.tabla)

        self.btn_nueva.clicked.connect(self.nueva_ciudad)
        self.btn_editar.clicked.connect(self.editar_ciudad)
        self.btn_actualizar.clicked.connect(self.cargar_tabla)
        self.tabla.doubleClicked.connect(self.editar_ciudad)

        self.cargar_tabla()

    def cargar_tabla(self):

        datos = obtener_ciudades()
        self.tabla.setRowCount(len(datos))

        for fila, ciudad in enumerate(datos):

            self.tabla.setItem(fila, 0, QTableWidgetItem(str(ciudad[0])))
            self.tabla.setItem(fila, 1, QTableWidgetItem(ciudad[1]))
            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem("Si" if ciudad[2] else "No")
            )

    def ciudad_seleccionada(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Selecciona una ciudad."
            )
            return None

        return int(self.tabla.item(fila, 0).text())

    def nueva_ciudad(self):

        dialogo = DialogoCiudad()

        if dialogo.exec():

            self.cargar_tabla()

    def editar_ciudad(self):

        id_ciudad = self.ciudad_seleccionada()

        if not id_ciudad:

            return

        ciudad = obtener_ciudad(id_ciudad)
        dialogo = DialogoCiudad(ciudad)

        if dialogo.exec():

            self.cargar_tabla()


class DialogoCiudad(QDialog):

    def __init__(self, ciudad=None):
        super().__init__()

        self.ciudad = ciudad
        self.setWindowTitle("Editar ciudad" if ciudad else "Nueva ciudad")

        layout = QVBoxLayout(self)
        formulario = QFormLayout()

        self.nombre = QLineEdit()
        self.activo = QCheckBox()
        self.activo.setChecked(True)

        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Activo", self.activo)
        layout.addLayout(formulario)

        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setProperty("variant", "primary")
        layout.addWidget(self.btn_guardar)
        self.btn_guardar.clicked.connect(self.guardar)

        if ciudad:

            self.nombre.setText(ciudad[1])
            self.activo.setChecked(bool(ciudad[2]))

    def guardar(self):

        try:

            if self.ciudad:

                actualizar_ciudad(
                    self.ciudad[0],
                    self.nombre.text(),
                    int(self.activo.isChecked())
                )

            else:

                insertar_ciudad(
                    self.nombre.text(),
                    int(self.activo.isChecked())
                )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Error",
                str(error)
            )
            return

        self.accept()
