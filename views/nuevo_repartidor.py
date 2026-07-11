from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QLabel
)

from database.database import (
    DIAS_INICIO_DESCANSO,
    DIAS_SEMANA,
    HORAS_CONTRATO,
    OPCIONES_DISPONIBILIDAD,
    actualizar_repartidor,
    insertar_repartidor,
    siguiente_descanso_valido
)
from services.rule_engine import dias_no_disponibles, tiene_dias_consecutivos


DESCANSO_NO_NECESARIO_TEXTO = "No necesario por disponibilidad semanal"


class NuevoRepartidor(QDialog):

    def __init__(self, repartidor=None):
        super().__init__()

        self.repartidor = repartidor
        self.setWindowTitle(
            "Editar repartidor"
            if self.repartidor
            else "Nuevo repartidor"
        )
        self.resize(450, 500)

        layout = QVBoxLayout(self)

        formulario = QFormLayout()

        self.nombre = QLineEdit()

        self.horas = QComboBox()
        self.horas.addItems([
            str(horas)
            for horas in HORAS_CONTRATO
        ])
        self.horas.setCurrentText("30")

        self.zona = QComboBox()
        self.zona.addItems([
            "Ronda",
            "Grela",
            "Outeiro",
            "Milladoiro"
        ])

        self.descanso_inicio = QComboBox()
        self.descanso_inicio.addItem(DESCANSO_NO_NECESARIO_TEXTO)
        self.descanso_inicio.addItems(DIAS_INICIO_DESCANSO)

        self.descanso_fin = QLineEdit()
        self.descanso_fin.setReadOnly(True)
        self.actualizar_descanso_fin()
        self.dias_no_laborables = QLabel("")
        self.explicacion_descanso = QLabel("")

        self.disponibilidad = {}

        for dia in DIAS_SEMANA:

            selector = QComboBox()
            selector.addItems(OPCIONES_DISPONIBILIDAD)
            selector.setCurrentText("Ambos")

            self.disponibilidad[dia] = selector

        self.doble = QCheckBox()
        self.doble.setChecked(True)

        self.hasta1 = QCheckBox()
        self.hasta1.setChecked(True)

        self.prio_comida = QSpinBox()
        self.prio_comida.setRange(0, 100)
        self.prio_comida.setValue(50)

        self.prio_noche = QSpinBox()
        self.prio_noche.setRange(0, 100)
        self.prio_noche.setValue(50)

        self.prio_grela = QSpinBox()
        self.prio_grela.setRange(0, 100)
        self.prio_grela.setValue(50)

        self.obs = QTextEdit()

        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Horas", self.horas)
        formulario.addRow("Zona", self.zona)
        formulario.addRow("Dias no laborables fijos", self.dias_no_laborables)
        formulario.addRow("Descanso adicional", self.descanso_inicio)
        formulario.addRow("Fin descanso adicional", self.descanso_fin)
        formulario.addRow("", self.explicacion_descanso)

        for dia in DIAS_SEMANA:

            formulario.addRow(
                f"Disponibilidad {dia}",
                self.disponibilidad[dia]
            )

        formulario.addRow("Doble turno", self.doble)
        formulario.addRow("Puede hasta la 1", self.hasta1)
        formulario.addRow("Prioridad comida", self.prio_comida)
        formulario.addRow("Prioridad noche", self.prio_noche)
        formulario.addRow("Prioridad Grela", self.prio_grela)
        formulario.addRow("Observaciones", self.obs)

        layout.addLayout(formulario)

        self.boton = QPushButton("Guardar")
        self.boton.setProperty("variant", "primary")

        layout.addWidget(self.boton)

        self.boton.clicked.connect(self.guardar)
        self.descanso_inicio.currentTextChanged.connect(
            self.actualizar_descanso_fin
        )

        for selector in self.disponibilidad.values():

            selector.currentTextChanged.connect(
                self.actualizar_estado_descanso
            )

        if self.repartidor:

            self.cargar_repartidor()

        else:

            self.actualizar_estado_descanso()

    def actualizar_descanso_fin(self):

        if self.descanso_inicio.currentText() == DESCANSO_NO_NECESARIO_TEXTO:

            self.descanso_fin.setText("")
            return

        self.descanso_fin.setText(
            siguiente_descanso_valido(
                self.descanso_inicio.currentText()
            )
        )

    def actualizar_estado_descanso(self):

        no_laborables = dias_no_disponibles({
            "disponibilidad": self.obtener_disponibilidad()
        })
        self.dias_no_laborables.setText(
            ", ".join(no_laborables) if no_laborables else "Ninguno"
        )

        if tiene_dias_consecutivos(no_laborables):

            self.descanso_inicio.setCurrentText(
                DESCANSO_NO_NECESARIO_TEXTO
            )
            self.explicacion_descanso.setText(
                "La disponibilidad semanal ya aporta dos dias consecutivos sin trabajo."
            )

        else:

            if self.descanso_inicio.currentText() == DESCANSO_NO_NECESARIO_TEXTO:

                self.descanso_inicio.setCurrentText("lunes")

            self.explicacion_descanso.setText(
                "Hace falta configurar descanso adicional."
            )

        self.actualizar_descanso_fin()

    def cargar_repartidor(self):

        self.nombre.setText(self.repartidor["nombre"])
        self.horas.setCurrentText(str(self.repartidor["horas"]))
        self.zona.setCurrentText(self.repartidor["zona"] or "")
        self.doble.setChecked(bool(self.repartidor["doble_turno"]))
        self.hasta1.setChecked(bool(self.repartidor["puede_hasta_la_una"]))
        self.prio_comida.setValue(self.repartidor["prioridad_comida"])
        self.prio_noche.setValue(self.repartidor["prioridad_noche"])
        self.prio_grela.setValue(self.repartidor["prioridad_grela"])
        self.obs.setPlainText(self.repartidor["observaciones"])

        for dia, turnos in self.repartidor["disponibilidad"].items():

            if dia not in self.disponibilidad:

                continue

            if "comida" in turnos and "noche" in turnos:

                opcion = "Ambos"

            elif "comida" in turnos:

                opcion = "Comidas"

            elif "noche" in turnos:

                opcion = "Cenas"

            else:

                opcion = "No disponible"

            self.disponibilidad[dia].setCurrentText(opcion)

        self.actualizar_estado_descanso()

        if not tiene_dias_consecutivos(
            dias_no_disponibles({
                "disponibilidad": self.obtener_disponibilidad()
            })
        ):

            self.descanso_inicio.setCurrentText(
                self.repartidor["descanso_inicio"] or "lunes"
            )
            self.descanso_fin.setText(
                self.repartidor["descanso_fin"]
                or siguiente_descanso_valido(self.descanso_inicio.currentText())
            )

    def guardar(self):

        if self.nombre.text().strip() == "":

            QMessageBox.warning(
                self,
                "Error",
                "Introduce un nombre."
            )
            return

        try:

            disponibilidad = self.obtener_disponibilidad()
            descanso_inicio = self.descanso_inicio.currentText()
            descanso_fin = self.descanso_fin.text()

            if descanso_inicio == DESCANSO_NO_NECESARIO_TEXTO:

                no_laborables = dias_no_disponibles({
                    "disponibilidad": disponibilidad
                })

                if not tiene_dias_consecutivos(no_laborables):

                    QMessageBox.warning(
                        self,
                        "Error",
                        "Configura un descanso adicional valido."
                    )
                    return

                descanso_inicio = None
                descanso_fin = None

            funcion = (
                actualizar_repartidor
                if self.repartidor
                else insertar_repartidor
            )
            argumentos = []

            if self.repartidor:

                argumentos.append(self.repartidor["id"])

            funcion(

                *argumentos,

                self.nombre.text(),

                int(self.horas.currentText()),

                self.zona.currentText(),

                int(self.doble.isChecked()),

                int(self.hasta1.isChecked()),

                self.prio_comida.value(),

                self.prio_noche.value(),

                self.prio_grela.value(),

                self.obs.toPlainText(),

                descanso_inicio=descanso_inicio,

                descanso_fin=descanso_fin,

                disponibilidad=disponibilidad

            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Error",
                str(error)
            )
            return

        self.accept()

    def obtener_disponibilidad(self):

        disponibilidad = {}

        for dia, selector in self.disponibilidad.items():

            disponibilidad[dia] = selector.currentText()

        return disponibilidad
