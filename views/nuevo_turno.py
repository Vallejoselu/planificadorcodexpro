from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QTimeEdit,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QColorDialog,
    QHBoxLayout,
    QWidget
)

from PySide6.QtCore import QTime

from database.database import (
    TIPOS_TURNO,
    actualizar_turno,
    insertar_turno
)


class NuevoTurno(QDialog):

    def __init__(self, turno=None):
        super().__init__()

        self.turno = turno

        self.setWindowTitle(
            "Editar turno"
            if self.turno
            else "Nuevo turno"
        )
        self.resize(420, 360)

        layout = QVBoxLayout(self)

        formulario = QFormLayout()

        self.tipo = QComboBox()
        self.tipo.addItems(TIPOS_TURNO)

        self.nombre = QLineEdit()

        self.hora_inicio = QTimeEdit()
        self.hora_inicio.setDisplayFormat("HH:mm")

        self.hora_fin = QTimeEdit()
        self.hora_fin.setDisplayFormat("HH:mm")

        self.color = QLineEdit()

        color_widget = QWidget()
        color_layout = QHBoxLayout(color_widget)
        color_layout.setContentsMargins(0, 0, 0, 0)
        color_layout.addWidget(self.color)

        self.btn_color = QPushButton("Color")
        color_layout.addWidget(self.btn_color)

        self.duracion = QDoubleSpinBox()
        self.duracion.setRange(0.25, 24)
        self.duracion.setSingleStep(0.25)
        self.duracion.setSuffix(" h")

        self.activo = QCheckBox()
        self.activo.setChecked(True)

        formulario.addRow("Tipo", self.tipo)
        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Hora inicio", self.hora_inicio)
        formulario.addRow("Hora fin", self.hora_fin)
        formulario.addRow("Color", color_widget)
        formulario.addRow("Duracion", self.duracion)
        formulario.addRow("Activo", self.activo)

        layout.addLayout(formulario)

        self.boton = QPushButton("Guardar")
        self.boton.setProperty("variant", "primary")
        layout.addWidget(self.boton)

        self.tipo.currentTextChanged.connect(self.aplicar_tipo)
        self.btn_color.clicked.connect(self.seleccionar_color)
        self.boton.clicked.connect(self.guardar)

        if self.turno:

            self.cargar_turno()

        else:

            self.aplicar_tipo(self.tipo.currentText())

    def aplicar_tipo(self, tipo):

        if tipo == "Comida":

            self.nombre.setText("Comida")
            self.hora_inicio.setTime(QTime(13, 0))
            self.hora_fin.setTime(QTime(16, 0))
            self.color.setText("#F5A623")
            self.duracion.setValue(3)

        elif tipo == "Cena":

            self.nombre.setText("Cena")
            self.hora_inicio.setTime(QTime(20, 0))
            self.hora_fin.setTime(QTime(23, 30))
            self.color.setText("#4A90E2")
            self.duracion.setValue(3.5)

        elif tipo == "Turno partido":

            self.nombre.setText("Turno partido")
            self.hora_inicio.setTime(QTime(13, 0))
            self.hora_fin.setTime(QTime(23, 30))
            self.color.setText("#7ED321")
            self.duracion.setValue(7.5)

        elif tipo == "Personalizado":

            self.nombre.setText("Personalizado")
            self.hora_inicio.setTime(QTime(9, 0))
            self.hora_fin.setTime(QTime(17, 0))
            self.color.setText("#9013FE")
            self.duracion.setValue(8)

    def seleccionar_color(self):

        color = QColorDialog.getColor()

        if color.isValid():

            self.color.setText(color.name().upper())

    def cargar_turno(self):

        self.tipo.setCurrentText(self.turno[1])
        self.nombre.setText(self.turno[2])
        self.hora_inicio.setTime(
            QTime.fromString(self.turno[3], "HH:mm")
        )
        self.hora_fin.setTime(
            QTime.fromString(self.turno[4], "HH:mm")
        )
        self.color.setText(self.turno[5])
        self.duracion.setValue(float(self.turno[6]))
        self.activo.setChecked(bool(self.turno[7]))

    def guardar(self):

        try:

            if self.turno:

                actualizar_turno(
                    self.turno[0],
                    self.tipo.currentText(),
                    self.nombre.text(),
                    self.hora_inicio.time().toString("HH:mm"),
                    self.hora_fin.time().toString("HH:mm"),
                    self.color.text(),
                    self.duracion.value(),
                    int(self.activo.isChecked())
                )

            else:

                insertar_turno(
                    self.tipo.currentText(),
                    self.nombre.text(),
                    self.hora_inicio.time().toString("HH:mm"),
                    self.hora_fin.time().toString("HH:mm"),
                    self.color.text(),
                    self.duracion.value(),
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
