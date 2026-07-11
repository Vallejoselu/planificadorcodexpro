from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget
)

from services.asistente_horarios import responder


class VistaAsistente(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Asistente de horarios")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        entrada = QHBoxLayout()

        self.pregunta = QLineEdit()
        self.pregunta.setPlaceholderText("Escribe una pregunta sobre repartidores, turnos u horarios")

        self.btn_consultar = QPushButton("Consultar")
        self.btn_consultar.setProperty("variant", "primary")

        entrada.addWidget(self.pregunta)
        entrada.addWidget(self.btn_consultar)

        self.layout.addLayout(entrada)

        self.resultado = QTextEdit()
        self.resultado.setReadOnly(True)

        self.layout.addWidget(self.resultado)

        ejemplos_titulo = QLabel("Ejemplos")
        ejemplos_titulo.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
        """)

        self.layout.addWidget(ejemplos_titulo)

        ejemplos = [
            "Quien lleva menos horas esta semana?",
            "Quien tiene horas pendientes?",
            "Quien descansa el lunes?",
            "Quien esta disponible el viernes?",
            "Quien tiene contrato de 20 horas?",
            "Que turnos estan sin cubrir?",
            "Quien puede cubrir la cena del viernes?",
            "Que ocurre si Juan esta de vacaciones el jueves?",
            "Quien podria sustituir a Maria manana?",
            "Se puede cubrir el viernes sin horas complementarias?",
            "Que ocurre si un restaurante necesita un repartidor adicional?"
        ]

        for texto in ejemplos:

            boton = QPushButton(texto)
            boton.clicked.connect(
                lambda checked=False, pregunta=texto: self.usar_ejemplo(pregunta)
            )
            self.layout.addWidget(boton)

        self.layout.addStretch()

        self.btn_consultar.clicked.connect(self.consultar)
        self.pregunta.returnPressed.connect(self.consultar)

    # ======================================

    def usar_ejemplo(self, pregunta):

        self.pregunta.setText(pregunta)
        self.consultar()

    # ======================================

    def consultar(self):

        pregunta = self.pregunta.text().strip()

        if not pregunta:

            QMessageBox.warning(
                self,
                "Pregunta vacia",
                "Escribe una pregunta para consultar el asistente."
            )
            return

        try:

            respuesta = responder(pregunta)

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                str(error)
            )
            return

        self.resultado.append(f"Pregunta: {pregunta}")
        self.resultado.append(f"Respuesta: {respuesta}")
        self.resultado.append("")
