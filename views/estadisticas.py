from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from services.estadisticas import obtener_estadisticas
from ui.widgets import configure_table


class VistaEstadisticas(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        cabecera = QHBoxLayout()

        titulo = QLabel("Panel de estadisticas")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.btn_actualizar = QPushButton("Actualizar")

        cabecera.addWidget(titulo)
        cabecera.addStretch()
        cabecera.addWidget(self.btn_actualizar)

        self.layout.addLayout(cabecera)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)

        self.contenido = QWidget()
        self.contenido_layout = QVBoxLayout(self.contenido)

        self.scroll.setWidget(self.contenido)
        self.layout.addWidget(self.scroll)

        self.btn_actualizar.clicked.connect(self.cargar_datos)

        self.cargar_datos()

    # ======================================

    def cargar_datos(self):

        datos = obtener_estadisticas()
        self.limpiar_contenido()

        self.crear_resumen(datos["resumen"])
        self.crear_grafica(datos["mensual"])
        self.crear_tablas(datos)

    # ======================================

    def limpiar_contenido(self):

        while self.contenido_layout.count():

            item = self.contenido_layout.takeAt(0)
            widget = item.widget()

            if widget:

                widget.deleteLater()

    # ======================================

    def crear_resumen(self, resumen):

        panel = QWidget()
        grid = QGridLayout(panel)

        tarjetas = [
            ("Horas trabajadas", resumen["horas_trabajadas"]),
            ("Horas pendientes", resumen["horas_pendientes"]),
            ("Horas complementarias", resumen["horas_complementarias"]),
            ("Turnos", resumen["turnos"]),
            ("Descansos", resumen["descansos"]),
            ("Vacaciones", resumen["vacaciones"]),
            ("Bajas", resumen["bajas"])
        ]

        for posicion, tarjeta in enumerate(tarjetas):

            grid.addWidget(
                TarjetaResumen(tarjeta[0], tarjeta[1]),
                posicion // 4,
                posicion % 4
            )

        self.contenido_layout.addWidget(panel)

    # ======================================

    def crear_grafica(self, mensual):

        titulo = QLabel("Graficas mensuales")
        titulo.setStyleSheet("""
            font-size:20px;
            font-weight:bold;
            margin-top:10px;
        """)

        self.contenido_layout.addWidget(titulo)
        self.contenido_layout.addWidget(GraficaMensual(mensual))

    # ======================================

    def crear_tablas(self, datos):

        fila_superior = QHBoxLayout()
        fila_superior.addWidget(
            self.crear_tabla(
                "Turnos",
                ["Turno", "Tipo", "Cantidad", "Horas"],
                [
                    [
                        item["turno"],
                        item["tipo"],
                        item["cantidad"],
                        item["horas"]
                    ]
                    for item in datos["turnos"]
                ]
            )
        )
        fila_superior.addWidget(
            self.crear_tabla(
                "Descansos",
                ["Repartidor", "Contrato", "Descanso"],
                [
                    [
                        item["repartidor"],
                        item["contrato"],
                        item["descanso"]
                    ]
                    for item in datos["descansos"]
                ]
            )
        )

        panel_superior = QWidget()
        panel_superior.setLayout(fila_superior)
        self.contenido_layout.addWidget(panel_superior)

        fila_inferior = QHBoxLayout()
        fila_inferior.addWidget(
            self.crear_tabla_ausencias("Vacaciones", datos["vacaciones"])
        )
        fila_inferior.addWidget(
            self.crear_tabla_ausencias("Bajas", datos["bajas"])
        )

        panel_inferior = QWidget()
        panel_inferior.setLayout(fila_inferior)
        self.contenido_layout.addWidget(panel_inferior)
        self.contenido_layout.addStretch()

    # ======================================

    def crear_tabla_ausencias(self, titulo, datos):

        return self.crear_tabla(
            titulo,
            ["Repartidor", "Inicio", "Fin"],
            [
                [
                    item["repartidor"],
                    item["inicio"],
                    item["fin"]
                ]
                for item in datos
            ]
        )

    # ======================================

    def crear_tabla(self, titulo, cabeceras, filas):

        contenedor = QFrame()
        contenedor.setFrameShape(QFrame.StyledPanel)

        layout = QVBoxLayout(contenedor)

        etiqueta = QLabel(titulo)
        etiqueta.setStyleSheet("""
            font-size:18px;
            font-weight:bold;
        """)

        tabla = QTableWidget()
        configure_table(tabla)
        tabla.setColumnCount(len(cabeceras))
        tabla.setHorizontalHeaderLabels(cabeceras)
        tabla.setRowCount(len(filas))

        for fila, datos in enumerate(filas):

            for columna, valor in enumerate(datos):

                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignCenter)
                tabla.setItem(fila, columna, item)

        tabla.resizeColumnsToContents()
        tabla.setMinimumHeight(180)

        layout.addWidget(etiqueta)
        layout.addWidget(tabla)

        return contenedor


class TarjetaResumen(QFrame):

    def __init__(self, titulo, valor):
        super().__init__()

        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(90)
        self.setStyleSheet("""
            QFrame {
                background:#F7F9FB;
                border:1px solid #D8DEE6;
                border-radius:6px;
            }
        """)

        layout = QVBoxLayout(self)

        etiqueta = QLabel(titulo)
        etiqueta.setStyleSheet("font-size:13px;color:#5B6778;")

        numero = QLabel(str(valor))
        numero.setStyleSheet("""
            font-size:26px;
            font-weight:bold;
            color:#1F2937;
        """)

        layout.addWidget(etiqueta)
        layout.addWidget(numero)
        layout.addStretch()


class GraficaMensual(QWidget):

    def __init__(self, datos):
        super().__init__()

        self.datos = datos
        self.setMinimumHeight(300)

    def paintEvent(self, event):

        if not self.datos:

            return

        pintor = QPainter(self)
        pintor.setRenderHint(QPainter.Antialiasing)

        margen_izquierdo = 46
        margen_superior = 24
        margen_inferior = 42
        ancho = self.width() - margen_izquierdo - 18
        alto = self.height() - margen_superior - margen_inferior
        base = margen_superior + alto

        maximo = max(
            max(float(item["horas"] or 0), item["vacaciones"], item["bajas"])
            for item in self.datos
        ) or 1

        pintor.setPen(QPen(QColor("#D8DEE6"), 1))
        pintor.drawLine(margen_izquierdo, base, margen_izquierdo + ancho, base)
        pintor.drawLine(margen_izquierdo, margen_superior, margen_izquierdo, base)

        ancho_mes = ancho / len(self.datos)
        ancho_barra = max(5, ancho_mes / 5)

        colores = {
            "horas": QColor("#3D85C6"),
            "vacaciones": QColor("#6AA84F"),
            "bajas": QColor("#CC0000")
        }

        for indice, item in enumerate(self.datos):

            centro = margen_izquierdo + indice * ancho_mes + ancho_mes / 2

            self.dibujar_barra(
                pintor,
                centro - ancho_barra * 1.5,
                base,
                ancho_barra,
                alto,
                float(item["horas"] or 0),
                maximo,
                colores["horas"]
            )
            self.dibujar_barra(
                pintor,
                centro - ancho_barra * 0.5,
                base,
                ancho_barra,
                alto,
                item["vacaciones"],
                maximo,
                colores["vacaciones"]
            )
            self.dibujar_barra(
                pintor,
                centro + ancho_barra * 0.5,
                base,
                ancho_barra,
                alto,
                item["bajas"],
                maximo,
                colores["bajas"]
            )

            pintor.setPen(QColor("#4B5563"))
            pintor.drawText(
                int(centro - ancho_mes / 2),
                base + 18,
                int(ancho_mes),
                18,
                Qt.AlignCenter,
                item["mes"]
            )

        self.dibujar_leyenda(pintor)
        pintor.end()

    # ======================================

    def dibujar_barra(self, pintor, x, base, ancho, alto, valor, maximo, color):

        altura = 0

        if maximo:

            altura = alto * (float(valor or 0) / maximo)

        pintor.setPen(Qt.NoPen)
        pintor.setBrush(color)
        pintor.drawRect(
            int(x),
            int(base - altura),
            int(ancho),
            int(altura)
        )

    # ======================================

    def dibujar_leyenda(self, pintor):

        elementos = [
            ("Horas", QColor("#3D85C6")),
            ("Vacaciones", QColor("#6AA84F")),
            ("Bajas", QColor("#CC0000"))
        ]

        x = 54

        for texto, color in elementos:

            pintor.setPen(Qt.NoPen)
            pintor.setBrush(color)
            pintor.drawRect(x, 8, 12, 12)
            pintor.setPen(QColor("#374151"))
            pintor.drawText(x + 18, 19, texto)
            x += 112
