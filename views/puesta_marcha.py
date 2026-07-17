from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from services.configuracion_guiada import ConfiguracionGuiadaService
from ui.widgets import PageHeader, configure_table


configuracion_guiada_service = ConfiguracionGuiadaService()


class VistaPuestaMarcha(QWidget):

    def __init__(self, ventana=None):
        super().__init__()

        self.ventana = ventana
        self.pasos = []
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

        self.layout.addWidget(
            PageHeader(
                "Puesta en marcha",
                "Comprueba si la empresa esta lista para generar cuadrantes."
            )
        )

        self.resumen = QLabel("")
        self.resumen.setWordWrap(True)
        self.resumen.setObjectName("guia_operativa")
        self.resumen.setStyleSheet("""
            padding:10px 12px;
            border:1px solid #CBD5E1;
            border-radius:6px;
            background:#F8FAFC;
            color:#1E293B;
        """)
        self.layout.addWidget(self.resumen)

        self.tabla = QTableWidget(self)
        configure_table(self.tabla)
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels([
            "Paso",
            "Estado",
            "Detalle",
            "Pantalla"
        ])
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.doubleClicked.connect(self.abrir_pantalla_recomendada)
        self.layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        self.btn_actualizar = QPushButton("Actualizar diagnostico")
        self.btn_abrir = QPushButton("Abrir pantalla recomendada")
        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.btn_abrir.clicked.connect(self.abrir_pantalla_recomendada)

        acciones.addWidget(self.btn_actualizar)
        acciones.addWidget(self.btn_abrir)
        acciones.addStretch()
        self.layout.addLayout(acciones)

        self.cargar_datos()

    def cargar_datos(self):

        diagnostico = configuracion_guiada_service.diagnosticar()
        self.pasos = diagnostico["pasos"]
        resumen = diagnostico["resumen"]
        self.resumen.setText(
            f"{resumen['estado']} | "
            f"{resumen['correctos']} correctos, "
            f"{resumen['avisos']} avisos, "
            f"{resumen['pendientes']} pendientes."
        )
        self.pintar_tabla()

    def pintar_tabla(self):

        self.tabla.clearContents()
        self.tabla.setRowCount(len(self.pasos))

        colores = {
            "ok": "#EAF4EA",
            "aviso": "#FFF2CC",
            "pendiente": "#FCE4E4"
        }
        textos_estado = {
            "ok": "Correcto",
            "aviso": "Aviso",
            "pendiente": "Pendiente"
        }

        for fila, paso in enumerate(self.pasos):

            valores = [
                paso["titulo"],
                textos_estado.get(paso["estado"], paso["estado"]),
                paso["detalle"],
                paso["pagina"]
            ]
            fondo = QBrush(QColor(colores.get(paso["estado"], "#FFFFFF")))

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                item.setBackground(fondo)
                self.tabla.setItem(fila, columna, item)

        self.tabla.resizeColumnsToContents()

    def abrir_pantalla_recomendada(self):

        fila = self.tabla.currentRow()

        if fila < 0 or fila >= len(self.pasos):

            QMessageBox.warning(
                self,
                "Puesta en marcha",
                "Selecciona un paso de la tabla para abrir su pantalla."
            )
            return

        pagina = self.pasos[fila]["pagina"]

        if self.ventana:

            self.ventana.mostrar_pagina(pagina)
