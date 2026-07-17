from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from services.configuracion_guiada import ConfiguracionGuiadaService
from services.datos_demo import DatosDemoService
from ui.widgets import PageHeader, configure_table


configuracion_guiada_service = ConfiguracionGuiadaService()
datos_demo_service = DatosDemoService()


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
                "Prepara la empresa paso a paso antes de generar cuadrantes."
            )
        )

        self.guia = QLabel(
            "Usa esta pantalla como checklist. Si quieres probar sin datos "
            "anteriores, usa 'Empezar de cero': crea una copia de seguridad y "
            "deja la aplicacion sin repartidores, restaurantes ni cuadrantes."
        )
        self.guia.setWordWrap(True)
        self.guia.setObjectName("guia_operativa")
        self.layout.addWidget(self.guia)

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
        self.tabla.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            2,
            QHeaderView.Stretch
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.doubleClicked.connect(self.abrir_pantalla_recomendada)
        self.layout.addWidget(self.tabla)

        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        self.btn_actualizar = QPushButton("Actualizar diagnostico")
        self.btn_abrir = QPushButton("Abrir pantalla recomendada")
        self.btn_cargar_demo = QPushButton("Cargar ejemplo")
        self.btn_limpiar_demo = QPushButton("Limpiar ejemplo")
        self.btn_empezar_cero = QPushButton("Empezar de cero")
        self.btn_empezar_cero.setProperty("variant", "danger")
        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.btn_abrir.clicked.connect(self.abrir_pantalla_recomendada)
        self.btn_cargar_demo.clicked.connect(self.cargar_datos_demo)
        self.btn_limpiar_demo.clicked.connect(self.limpiar_datos_demo)
        self.btn_empezar_cero.clicked.connect(self.empezar_de_cero)

        acciones.addWidget(self.btn_actualizar)
        acciones.addWidget(self.btn_abrir)
        acciones.addWidget(self.btn_cargar_demo)
        acciones.addWidget(self.btn_limpiar_demo)
        acciones.addWidget(self.btn_empezar_cero)
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
            "ok": "#DCFCE7",
            "aviso": "#FEF3C7",
            "pendiente": "#FEE2E2"
        }
        textos = {
            "ok": "#14532D",
            "aviso": "#78350F",
            "pendiente": "#7F1D1D"
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
            texto = QBrush(QColor(textos.get(paso["estado"], "#111827")))

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                item.setBackground(fondo)
                item.setForeground(texto)
                self.tabla.setItem(fila, columna, item)

        self.tabla.resizeRowsToContents()

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

    def cargar_datos_demo(self):

        respuesta = QMessageBox.question(
            self,
            "Cargar ejemplo",
            (
                "Se crearan datos de ejemplo marcados como [Demo]. "
                "No se modificaran tus datos reales. "
                "Puedes limpiarlos despues desde esta misma pantalla."
            )
        )

        if respuesta != QMessageBox.Yes:

            return

        resumen = datos_demo_service.cargar_demo()
        self.cargar_datos()
        QMessageBox.information(
            self,
            "Cargar ejemplo",
            (
                "Datos demo preparados: "
                f"{resumen['ciudades']} ciudades, "
                f"{resumen['restaurantes']} restaurantes, "
                f"{resumen['turnos']} turnos y "
                f"{resumen['repartidores']} repartidores."
            )
        )

    def limpiar_datos_demo(self):

        respuesta = QMessageBox.question(
            self,
            "Limpiar ejemplo",
            (
                "Se desactivaran solo los datos marcados como [Demo]. "
                "Tus datos reales no se tocaran."
            )
        )

        if respuesta != QMessageBox.Yes:

            return

        resumen = datos_demo_service.limpiar_demo()
        self.cargar_datos()
        QMessageBox.information(
            self,
            "Limpiar ejemplo",
            (
                "Datos demo desactivados: "
                f"{resumen['ciudades']} ciudades, "
                f"{resumen['restaurantes']} restaurantes y "
                f"{resumen['repartidores']} repartidores."
            )
        )

    def empezar_de_cero(self):

        respuesta = QMessageBox.question(
            self,
            "Empezar de cero",
            (
                "Se creara un backup automatico y se desactivaran los datos "
                "operativos actuales: repartidores, restaurantes, ciudades, "
                "turnos, demandas y cuadrantes.\n\n"
                "La estructura de la base de datos se conserva. Quieres "
                "continuar?"
            )
        )

        if respuesta != QMessageBox.Yes:

            return

        resumen = datos_demo_service.empezar_de_cero()
        self.cargar_datos()
        QMessageBox.information(
            self,
            "Empezar de cero",
            (
                "Aplicacion lista para empezar limpia.\n\n"
                f"Backup creado:\n{resumen['respaldo']}\n\n"
                f"Repartidores desactivados: {resumen['repartidores']}\n"
                f"Restaurantes desactivados: {resumen['restaurantes']}\n"
                f"Ciudades desactivadas: {resumen['ciudades']}\n"
                f"Turnos desactivados: {resumen['turnos']}\n"
                f"Asignaciones de cuadrante eliminadas: "
                f"{resumen['cuadrantes']}"
            )
        )
