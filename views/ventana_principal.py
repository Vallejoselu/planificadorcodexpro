from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget
)

from app_info import APP_NAME, VERSION
from views.asistente import VistaAsistente
from views.ciudades import VistaCiudades
from views.configuracion import VistaConfiguracion
from views.cuadrantes import VistaCuadrantes
from views.estadisticas import VistaEstadisticas
from views.exportaciones import VistaExportaciones
from views.guia_uso import VistaGuiaUso
from views.inicio import VistaInicio
from views.puesta_marcha import VistaPuestaMarcha
from views.repartidores import VistaRepartidores
from views.reglas import VistaReglas
from views.restaurantes import VistaRestaurantes
from views.turnos import VistaTurnos


class VentanaPrincipal(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} {VERSION}")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)

        self.paginas = {}
        self.botones = {}

        central = QWidget()
        self.setCentralWidget(central)

        self.layout_principal = QHBoxLayout(central)
        self.layout_principal.setContentsMargins(0, 0, 0, 0)
        self.layout_principal.setSpacing(0)

        self.menu = QFrame()
        self.menu.setObjectName("sidebar")
        self.menu.setFixedWidth(260)

        self.menu_layout = QVBoxLayout(self.menu)
        self.menu_layout.setContentsMargins(18, 18, 18, 18)
        self.menu_layout.setSpacing(8)

        titulo = QLabel("Planificador\nDelivery Pro")
        titulo.setObjectName("appTitle")
        titulo.setAlignment(Qt.AlignLeft)
        self.menu_layout.addWidget(titulo)
        self.menu_layout.addSpacing(12)

        self.grupo_botones = QButtonGroup(self)
        self.grupo_botones.setExclusive(True)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        self.layout_principal.addWidget(self.menu)
        self.layout_principal.addWidget(self.stack, 1)

        self.crear_paginas()
        self.crear_menu()
        self.mostrar_pagina("inicio")

    # =====================================

    def crear_paginas(self):

        self.registrar_pagina("inicio", VistaInicio(self))
        self.registrar_pagina("guia_uso", VistaGuiaUso())
        self.registrar_pagina("puesta_marcha", VistaPuestaMarcha(self))
        self.registrar_pagina("repartidores", VistaRepartidores())
        self.registrar_pagina("ciudades", VistaCiudades())
        self.registrar_pagina("restaurantes", VistaRestaurantes())
        self.registrar_pagina("turnos", VistaTurnos())
        self.registrar_pagina("cuadrantes", VistaCuadrantes())
        self.registrar_pagina("asistente", VistaAsistente())
        self.registrar_pagina("reglas", VistaReglas())
        self.registrar_pagina("estadisticas", VistaEstadisticas())
        self.registrar_pagina("exportar", VistaExportaciones())
        self.registrar_pagina("configuracion", VistaConfiguracion())

    # =====================================

    def registrar_pagina(self, clave, widget):

        self.paginas[clave] = widget
        self.stack.addWidget(widget)

    # =====================================

    def crear_menu(self):

        self.agregar_seccion("GENERAL")
        self.agregar_boton(
            "inicio",
            "Inicio",
            QStyle.SP_ComputerIcon
        )
        self.agregar_boton(
            "guia_uso",
            "Guia de uso",
            QStyle.SP_DialogHelpButton
        )
        self.agregar_boton(
            "puesta_marcha",
            "Puesta en marcha",
            QStyle.SP_DialogApplyButton
        )

        self.agregar_seccion("GESTION")
        self.agregar_boton(
            "repartidores",
            "Repartidores",
            QStyle.SP_FileDialogDetailedView
        )
        self.agregar_boton(
            "ciudades",
            "Ciudades",
            QStyle.SP_DriveNetIcon
        )
        self.agregar_boton(
            "restaurantes",
            "Restaurantes",
            QStyle.SP_DirHomeIcon
        )
        self.agregar_boton(
            "turnos",
            "Turnos",
            QStyle.SP_BrowserReload
        )

        self.agregar_seccion("PLANIFICACION")
        self.agregar_boton(
            "cuadrantes",
            "Cuadrantes",
            QStyle.SP_FileDialogListView
        )
        self.agregar_boton(
            "asistente",
            "Asistente",
            QStyle.SP_MessageBoxInformation
        )
        self.agregar_boton(
            "reglas",
            "Reglas",
            QStyle.SP_FileDialogContentsView
        )
        self.agregar_boton(
            "estadisticas",
            "Estadisticas",
            QStyle.SP_FileDialogInfoView
        )

        self.agregar_seccion("HERRAMIENTAS")
        self.agregar_boton(
            "exportar",
            "Exportar",
            QStyle.SP_DialogSaveButton
        )
        self.agregar_boton(
            "configuracion",
            "Configuracion",
            QStyle.SP_FileDialogContentsView
        )

        self.menu_layout.addStretch()

    # =====================================

    def agregar_seccion(self, texto):

        label = QLabel(texto)
        label.setObjectName("sectionTitle")
        self.menu_layout.addSpacing(8)
        self.menu_layout.addWidget(label)

    # =====================================

    def agregar_boton(self, clave, texto, icono):

        boton = QPushButton(texto)
        boton.setObjectName("navButton")
        boton.setCheckable(True)
        boton.setIcon(self.style().standardIcon(icono))
        boton.clicked.connect(
            lambda checked=False, pagina=clave: self.mostrar_pagina(pagina)
        )

        self.grupo_botones.addButton(boton)
        self.botones[clave] = boton
        self.menu_layout.addWidget(boton)

    # =====================================

    def mostrar_pagina(self, clave):

        widget = self.paginas.get(clave)

        if not widget:

            return

        self.stack.setCurrentWidget(widget)

        boton = self.botones.get(clave)

        if boton:

            boton.setChecked(True)

        if hasattr(widget, "cargar_datos"):

            widget.cargar_datos()

        if hasattr(widget, "cargar_tabla"):

            widget.cargar_tabla()

    # =====================================

    def cambiar_contenido(self, widget):

        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    # =====================================

    def abrir_repartidores(self):

        self.mostrar_pagina("repartidores")

    # =====================================

    def abrir_restaurantes(self):

        self.mostrar_pagina("restaurantes")

    # =====================================

    def abrir_turnos(self):

        self.mostrar_pagina("turnos")

    # =====================================

    def abrir_cuadrantes(self):

        self.mostrar_pagina("cuadrantes")

    # =====================================

    def abrir_asistente(self):

        self.mostrar_pagina("asistente")

    # =====================================

    def abrir_exportaciones(self):

        self.mostrar_pagina("exportar")

    # =====================================

    def abrir_estadisticas(self):

        self.mostrar_pagina("estadisticas")

    # =====================================

    def abrir_configuracion(self):

        self.mostrar_pagina("configuracion")
