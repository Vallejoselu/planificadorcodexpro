from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget
)

from services.asistente_creacion_guiada import AsistenteCreacionGuiadaService
from ui.widgets import PageHeader, make_button


class VistaCreacionGuiada(QWidget):

    def __init__(self, ventana=None, asistente_service=None):
        super().__init__()

        self.ventana = ventana
        self.asistente_service = (
            asistente_service or AsistenteCreacionGuiadaService()
        )
        self.pasos = []
        self.indice_actual = 0
        self.usar_recomendado_inicial = True

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

        self.layout.addWidget(
            PageHeader(
                "Crear paso a paso",
                "Configura la empresa en orden sin saltar entre pantallas."
            )
        )

        self.crear_panel_paso()
        self.crear_progreso()
        self.crear_acciones()
        self.layout.addStretch()

        self.cargar_datos()

    def crear_panel_paso(self):

        self.panel = QFrame()
        self.panel.setObjectName("card")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(18, 16, 18, 16)
        panel_layout.setSpacing(10)

        self.indicador = QLabel("")
        self.indicador.setObjectName("pageSubtitle")
        self.indicador.setWordWrap(True)

        self.titulo = QLabel("")
        self.titulo.setObjectName("cardValue")
        self.titulo.setWordWrap(True)

        self.estado = QLabel("")
        self.estado.setObjectName("infoPanel")
        self.estado.setWordWrap(True)

        self.detalle = QLabel("")
        self.detalle.setObjectName("pageSubtitle")
        self.detalle.setWordWrap(True)

        self.ayuda = QLabel(
            "Abre el paso, guarda los datos en su pantalla y vuelve aqui para "
            "continuar. Esta pantalla no modifica datos directamente."
        )
        self.ayuda.setObjectName("pageSubtitle")
        self.ayuda.setWordWrap(True)

        panel_layout.addWidget(self.indicador)
        panel_layout.addWidget(self.titulo)
        panel_layout.addWidget(self.estado)
        panel_layout.addWidget(self.detalle)
        panel_layout.addWidget(self.ayuda)

        self.layout.addWidget(self.panel)

    def crear_progreso(self):

        self.grid_pasos = QGridLayout()
        self.grid_pasos.setSpacing(8)
        self.labels_pasos = []

        for indice in range(8):

            label = QLabel("")
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setMinimumHeight(58)
            label.setObjectName("pasoGuia")
            self.labels_pasos.append(label)
            self.grid_pasos.addWidget(label, indice // 4, indice % 4)

        self.layout.addLayout(self.grid_pasos)

    def crear_acciones(self):

        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        self.btn_anterior = make_button("Atras", "secondary")
        self.btn_siguiente = make_button("Siguiente", "secondary")
        self.btn_abrir = make_button("Abrir este paso", "primary")
        self.btn_actualizar = make_button("Actualizar", "secondary")

        self.btn_anterior.clicked.connect(self.paso_anterior)
        self.btn_siguiente.clicked.connect(self.paso_siguiente)
        self.btn_abrir.clicked.connect(self.abrir_paso)
        self.btn_actualizar.clicked.connect(self.cargar_datos)

        acciones.addWidget(self.btn_anterior)
        acciones.addWidget(self.btn_siguiente)
        acciones.addWidget(self.btn_abrir)
        acciones.addWidget(self.btn_actualizar)
        acciones.addStretch()
        self.layout.addLayout(acciones)

    def cargar_datos(self):

        flujo = self.asistente_service.obtener_flujo()
        self.pasos = flujo["pasos"]

        if not self.pasos:

            return

        if self.usar_recomendado_inicial:

            self.indice_actual = flujo["indice_recomendado"]
            self.usar_recomendado_inicial = False

        self.indice_actual = max(
            0,
            min(self.indice_actual, len(self.pasos) - 1)
        )
        self.pintar_paso()
        self.pintar_progreso()

    def pintar_paso(self):

        paso = self.paso_actual()

        self.indicador.setText(
            f"Paso {paso['numero']} de {paso['total']}"
        )
        self.titulo.setText(paso["titulo"])
        self.estado.setText(self.texto_estado(paso))
        self.detalle.setText(paso["detalle"])
        self.btn_abrir.setText(paso["accion"])

        self.btn_anterior.setEnabled(self.indice_actual > 0)
        self.btn_siguiente.setEnabled(
            self.indice_actual < len(self.pasos) - 1
        )

    def pintar_progreso(self):

        for indice, label in enumerate(self.labels_pasos):

            if indice >= len(self.pasos):

                label.hide()
                continue

            paso = self.pasos[indice]
            label.setText(f"{paso['numero']}. {paso['titulo']}")
            label.setStyleSheet(self.estilo_paso(paso, indice))
            label.show()

    def texto_estado(self, paso):

        textos = {
            "ok": "Correcto",
            "aviso": "Conviene revisar",
            "pendiente": "Pendiente"
        }

        return textos.get(paso["estado"], paso["estado"])

    def estilo_paso(self, paso, indice):

        colores = {
            "ok": ("#BBF7D0", "#166534", "#052E16"),
            "aviso": ("#FDE68A", "#A16207", "#422006"),
            "pendiente": ("#FECACA", "#B91C1C", "#450A0A")
        }
        fondo, borde, texto = colores.get(
            paso["estado"],
            ("#E5E7EB", "#6B7280", "#111827")
        )

        if indice == self.indice_actual:

            borde = "#4F6BFF"

        return (
            "QLabel#pasoGuia {"
            f"background:{fondo};"
            f"border:2px solid {borde};"
            "border-radius:8px;"
            "padding:8px;"
            f"color:{texto};"
            "}"
        )

    def paso_actual(self):

        return self.pasos[self.indice_actual]

    def paso_anterior(self):

        if self.indice_actual > 0:

            self.indice_actual -= 1
            self.pintar_paso()
            self.pintar_progreso()

    def paso_siguiente(self):

        if self.indice_actual < len(self.pasos) - 1:

            self.indice_actual += 1
            self.pintar_paso()
            self.pintar_progreso()

    def abrir_paso(self):

        if self.ventana:

            self.ventana.mostrar_pagina(self.paso_actual()["pagina"])
