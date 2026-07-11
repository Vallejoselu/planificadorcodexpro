from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView
)

from PySide6.QtCore import Qt

from database.database import (
    actualizar_restaurante,
    insertar_restaurante,
    obtener_repartidores
)


class NuevoRestaurante(QDialog):

    def __init__(self, restaurante=None, repartidores_fijos=None):
        super().__init__()

        self.restaurante = restaurante
        self.repartidores_fijos = repartidores_fijos or []

        self.setWindowTitle(
            "Editar restaurante"
            if self.restaurante
            else "Nuevo restaurante"
        )
        self.resize(520, 620)

        layout = QVBoxLayout(self)

        formulario = QFormLayout()

        self.nombre = QLineEdit()
        self.direccion = QLineEdit()

        self.zona = QComboBox()
        self.zona.addItems([
            "Ronda",
            "Grela",
            "Outeiro",
            "Milladoiro"
        ])

        self.telefono = QLineEdit()

        self.activo = QCheckBox()
        self.activo.setChecked(True)

        self.horario_comida = QLineEdit()
        self.horario_comida.setPlaceholderText("13:00 - 16:00")

        self.horario_cena = QLineEdit()
        self.horario_cena.setPlaceholderText("20:00 - 23:30")

        self.repartidores = QListWidget()
        self.repartidores.setSelectionMode(
            QAbstractItemView.MultiSelection
        )

        self.cargar_repartidores()

        self.obs = QTextEdit()

        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Zona", self.zona)
        formulario.addRow("Direccion", self.direccion)
        formulario.addRow("Telefono", self.telefono)
        formulario.addRow("Activo", self.activo)
        formulario.addRow("Horario comida", self.horario_comida)
        formulario.addRow("Horario cena", self.horario_cena)
        formulario.addRow("Repartidores fijos", self.repartidores)
        formulario.addRow("Observaciones", self.obs)

        layout.addLayout(formulario)

        self.boton = QPushButton("Guardar")
        self.boton.setProperty("variant", "primary")

        layout.addWidget(self.boton)

        self.boton.clicked.connect(self.guardar)

        if self.restaurante:

            self.cargar_restaurante()

    def cargar_repartidores(self):

        for repartidor in obtener_repartidores():

            item = QListWidgetItem(repartidor[1])
            item.setData(Qt.UserRole, repartidor[0])
            self.repartidores.addItem(item)

            if repartidor[0] in self.repartidores_fijos:

                item.setSelected(True)

    def cargar_restaurante(self):

        self.nombre.setText(self.restaurante[1])
        self.direccion.setText(
            self.restaurante[2]
            if self.restaurante[2]
            else ""
        )
        self.zona.setCurrentText(
            self.restaurante[3]
            if self.restaurante[3]
            else "Ronda"
        )
        self.telefono.setText(
            self.restaurante[4]
            if self.restaurante[4]
            else ""
        )
        self.activo.setChecked(bool(self.restaurante[6]))
        self.horario_comida.setText(
            self.restaurante[7]
            if self.restaurante[7]
            else ""
        )
        self.horario_cena.setText(
            self.restaurante[8]
            if self.restaurante[8]
            else ""
        )

    def obtener_repartidores_fijos(self):

        repartidores = []

        for item in self.repartidores.selectedItems():

            repartidores.append(item.data(Qt.UserRole))

        return repartidores

    def guardar(self):

        if self.nombre.text().strip() == "":

            QMessageBox.warning(
                self,
                "Error",
                "Introduce un nombre."
            )
            return

        if self.restaurante:

            actualizar_restaurante(
                self.restaurante[0],
                self.nombre.text(),
                self.direccion.text(),
                self.zona.currentText(),
                self.telefono.text(),
                int(self.activo.isChecked()),
                self.horario_comida.text(),
                self.horario_cena.text(),
                self.obtener_repartidores_fijos()
            )

        else:

            insertar_restaurante(

                self.nombre.text(),

                self.direccion.text(),

                self.zona.currentText(),

                self.telefono.text(),

                50,

                self.obs.toPlainText(),

                int(self.activo.isChecked()),

                self.horario_comida.text(),

                self.horario_cena.text(),

                self.obtener_repartidores_fijos()

            )

        self.accept()
