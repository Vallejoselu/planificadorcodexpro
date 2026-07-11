from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from database.database import (
    obtener_eventos_integracion,
    obtener_integraciones_api
)
from services.actualizaciones import ServicioActualizaciones
from ui.theme_manager import ThemeManager
from ui.widgets import PageHeader, configure_table, make_button


class VistaConfiguracion(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

        self.layout.addWidget(
            PageHeader(
                "Configuracion",
                "Tema visual e integraciones preparadas"
            )
        )

        self.panel_tema = QFrame()
        self.panel_tema.setObjectName("card")
        tema_layout = QFormLayout(self.panel_tema)
        tema_layout.setContentsMargins(16, 16, 16, 16)

        self.selector_tema = QComboBox()
        self.selector_tema.addItem("Tema claro", "light")
        self.selector_tema.addItem("Tema oscuro", "dark")
        self.selector_tema.setCurrentIndex(
            self.selector_tema.findData(ThemeManager.current_theme())
        )
        tema_layout.addRow("Tema", self.selector_tema)

        self.layout.addWidget(self.panel_tema)

        self.panel_actualizaciones = QFrame()
        self.panel_actualizaciones.setObjectName("card")
        actualizaciones_layout = QHBoxLayout(self.panel_actualizaciones)
        actualizaciones_layout.setContentsMargins(16, 16, 16, 16)

        self.estado_actualizaciones = QLabel(
            "Actualizaciones preparadas. Servidor pendiente de configurar."
        )
        self.btn_comprobar_actualizaciones = make_button(
            "Comprobar actualizaciones",
            "secondary"
        )

        actualizaciones_layout.addWidget(self.estado_actualizaciones, 1)
        actualizaciones_layout.addWidget(self.btn_comprobar_actualizaciones)

        self.layout.addWidget(self.panel_actualizaciones)

        barra = QHBoxLayout()
        self.btn_actualizar = make_button("Actualizar", "secondary")
        barra.addWidget(self.btn_actualizar)
        barra.addStretch()
        self.layout.addLayout(barra)

        self.tabla_integraciones = QTableWidget()
        self.tabla_eventos = QTableWidget()
        configure_table(self.tabla_integraciones)
        configure_table(self.tabla_eventos)

        self.layout.addWidget(QLabel("Integraciones preparadas"))
        self.layout.addWidget(self.tabla_integraciones)
        self.layout.addWidget(QLabel("Eventos de integracion"))
        self.layout.addWidget(self.tabla_eventos)

        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.selector_tema.currentIndexChanged.connect(self.cambiar_tema)
        self.btn_comprobar_actualizaciones.clicked.connect(
            self.comprobar_actualizaciones
        )

        self.cargar_datos()

    # ======================================

    def cargar_datos(self):

        self.cargar_integraciones()
        self.cargar_eventos()

    # ======================================

    def cambiar_tema(self):

        ThemeManager.set_theme(self.selector_tema.currentData())

    # ======================================

    def comprobar_actualizaciones(self):

        servicio = ServicioActualizaciones()
        resultado = servicio.comprobar()
        mensaje = servicio.mensaje_para_usuario(resultado)
        self.estado_actualizaciones.setText(mensaje)

        if resultado.correcto:

            QMessageBox.information(
                self,
                "Actualizaciones",
                mensaje
            )

        else:

            QMessageBox.warning(
                self,
                "Actualizaciones",
                mensaje
            )

    # ======================================

    def cargar_integraciones(self):

        datos = obtener_integraciones_api()

        self.tabla_integraciones.setColumnCount(7)
        self.tabla_integraciones.setHorizontalHeaderLabels([
            "Proveedor",
            "Nombre",
            "Activo",
            "Base URL",
            "Credenciales",
            "Opciones",
            "Actualizado"
        ])
        self.tabla_integraciones.setRowCount(len(datos))

        for fila, integracion in enumerate(datos):

            valores = [
                integracion[0],
                integracion[1],
                "Si" if integracion[2] else "No",
                integracion[3] or "",
                integracion[4] or "",
                integracion[5] or "",
                integracion[6] or ""
            ]

            self.pintar_fila(self.tabla_integraciones, fila, valores)

        self.tabla_integraciones.resizeColumnsToContents()

    # ======================================

    def cargar_eventos(self):

        datos = obtener_eventos_integracion()

        self.tabla_eventos.setColumnCount(5)
        self.tabla_eventos.setHorizontalHeaderLabels([
            "Proveedor",
            "Tipo",
            "Estado",
            "Mensaje",
            "Fecha"
        ])
        self.tabla_eventos.setRowCount(len(datos))

        for fila, evento in enumerate(datos):

            self.pintar_fila(self.tabla_eventos, fila, evento)

        self.tabla_eventos.resizeColumnsToContents()

    # ======================================

    def pintar_fila(self, tabla, fila, valores):

        for columna, valor in enumerate(valores):

            item = QTableWidgetItem(str(valor))
            item.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, columna, item)
