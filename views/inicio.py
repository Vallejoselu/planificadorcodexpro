from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QVBoxLayout,
    QWidget
)

from services.centro_operativo import CentroOperativoService
from ui.widgets import CardWidget, PageHeader, make_button


class VistaInicio(QWidget):

    def __init__(self, ventana=None, centro_operativo_service=None):
        super().__init__()

        self.ventana = ventana
        self.centro_operativo_service = (
            centro_operativo_service or CentroOperativoService()
        )
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(16)

        self.layout.addWidget(
            PageHeader(
                "Inicio",
                "Centro operativo simple"
            )
        )

        self.crear_panel_estado()
        self.crear_metricas()
        self.crear_panel_pendientes()
        self.crear_acciones()
        self.layout.addStretch()

        self.cargar_datos()

    # ======================================

    def crear_panel_estado(self):

        self.panel_estado = QFrame()
        self.panel_estado.setObjectName("estadoPanel")
        estado_layout = QVBoxLayout(self.panel_estado)
        estado_layout.setContentsMargins(18, 16, 18, 16)
        estado_layout.setSpacing(6)

        self.estado_titulo = QLabel("Comprobando estado")
        self.estado_titulo.setObjectName("cardValue")
        self.estado_titulo.setWordWrap(True)

        self.estado_detalle = QLabel("")
        self.estado_detalle.setObjectName("pageSubtitle")
        self.estado_detalle.setWordWrap(True)

        self.guia_operativa = QLabel("")
        self.guia_operativa.setObjectName("estadoDetalle")
        self.guia_operativa.setWordWrap(True)

        estado_layout.addWidget(self.estado_titulo)
        estado_layout.addWidget(self.estado_detalle)
        estado_layout.addWidget(self.guia_operativa)
        self.layout.addWidget(self.panel_estado)

    def crear_metricas(self):

        self.grid = QGridLayout()
        self.grid.setSpacing(12)

        self.cards = {
            "repartidores": CardWidget("Repartidores"),
            "restaurantes": CardWidget("Restaurantes"),
            "turnos": CardWidget("Turnos"),
            "cuadrante": CardWidget("Cuadrante actual")
        }

        posiciones = [
            ("repartidores", 0, 0),
            ("restaurantes", 0, 1),
            ("turnos", 1, 0),
            ("cuadrante", 1, 1)
        ]

        for clave, fila, columna in posiciones:

            self.grid.addWidget(self.cards[clave], fila, columna)

        self.layout.addLayout(self.grid)

    def crear_panel_pendientes(self):

        self.panel_pendientes = QFrame()
        self.panel_pendientes.setObjectName("card")
        pendientes_layout = QVBoxLayout(self.panel_pendientes)
        pendientes_layout.setContentsMargins(18, 16, 18, 16)
        pendientes_layout.setSpacing(8)

        titulo = QLabel("Que falta")
        titulo.setObjectName("cardTitle")

        self.pendientes_labels = []
        pendientes_layout.addWidget(titulo)

        for _ in range(5):

            label = QLabel("")
            label.setObjectName("pageSubtitle")
            label.setWordWrap(True)
            self.pendientes_labels.append(label)
            pendientes_layout.addWidget(label)

        self.layout.addWidget(self.panel_pendientes)

    def crear_acciones(self):

        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        self.btn_accion_principal = make_button("Generar cuadrante", "primary")
        self.btn_accion_principal.clicked.connect(self.ejecutar_accion_principal)

        self.btn_comprobar = make_button("Comprobar configuracion", "secondary")
        self.btn_comprobar.clicked.connect(
            lambda checked=False: self.ir_a("puesta_marcha")
        )

        self.btn_guia = make_button("Guia de uso", "secondary")
        self.btn_guia.clicked.connect(
            lambda checked=False: self.ir_a("guia_uso")
        )

        acciones.addWidget(self.btn_accion_principal)
        acciones.addWidget(self.btn_comprobar)
        acciones.addWidget(self.btn_guia)
        acciones.addStretch()
        self.layout.addLayout(acciones)

    # ======================================

    def cargar_datos(self):

        resumen = self.centro_operativo_service.obtener_resumen()
        self.accion_actual = resumen["accion"]

        self.estado_titulo.setText(resumen["estado"])
        self.estado_detalle.setText(resumen["detalle"])
        self.guia_operativa.setText(
            "Antes de generar, revisa solo los puntos marcados abajo. "
            "Si todo esta correcto, abre Cuadrantes y genera la semana."
        )
        self.panel_estado.setStyleSheet(self.estilo_estado(resumen["nivel"]))

        for metrica in resumen["metricas"]:

            self.cards[metrica["clave"]].set_value(metrica["valor"])

        self.actualizar_pendientes(resumen["pendientes"])
        self.btn_accion_principal.setText(resumen["accion"]["texto"])

    # ======================================

    def actualizar_pendientes(self, pendientes):

        if not pendientes:

            pendientes = [{
                "titulo": "Todo listo",
                "detalle": "No hay bloqueos importantes para generar.",
                "estado": "ok"
            }]

        for indice, label in enumerate(self.pendientes_labels):

            if indice >= len(pendientes):

                label.hide()
                continue

            paso = pendientes[indice]
            label.setText(
                f"- {paso.get('titulo')}: {paso.get('detalle')}"
            )
            label.show()

    def ejecutar_accion_principal(self):

        self.ir_a(self.accion_actual.get("pagina", "cuadrantes"))

    def estilo_estado(self, nivel):

        colores = {
            "ok": ("#102A1D", "#22C55E", "#BBF7D0"),
            "aviso": ("#2A220F", "#F59E0B", "#FDE68A"),
            "pendiente": ("#2A1418", "#F87171", "#FECACA")
        }
        fondo, borde, detalle = colores.get(nivel, colores["pendiente"])

        return (
            "QFrame#estadoPanel {"
            f"background:{fondo};"
            f"border:1px solid {borde};"
            "border-radius:8px;"
            "}"
            "QFrame#estadoPanel QLabel {"
            "background:transparent;"
            "color:#F9FAFB;"
            "}"
            "QFrame#estadoPanel QLabel#pageSubtitle,"
            "QFrame#estadoPanel QLabel#estadoDetalle {"
            f"color:{detalle};"
            "}"
        )

    # ======================================

    def ir_a(self, pagina):

        if self.ventana:

            self.ventana.mostrar_pagina(pagina)
