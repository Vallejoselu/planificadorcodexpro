from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from database.schema import DIAS_SEMANA
from repositories.demandas_zona_repository import DemandasZonaRepository
from repositories.integraciones_repository import IntegracionesRepository
from repositories.turnos_repository import TurnosRepository
from services.actualizaciones import ServicioActualizaciones
from ui.theme_manager import ThemeManager
from ui.widgets import PageHeader, configure_table, make_button


demandas_zona_repository = DemandasZonaRepository()
integraciones_repository = IntegracionesRepository()
turnos_repository = TurnosRepository()


class VistaConfiguracion(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)
        self.demandas_zona = []
        self.turnos_demanda_zona = []

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

        self.crear_panel_demanda_zona()

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
        self.btn_agregar_demanda_zona.clicked.connect(
            self.agregar_demanda_zona
        )
        self.btn_eliminar_demanda_zona.clicked.connect(
            self.eliminar_demanda_zona
        )
        self.btn_guardar_demanda_zona.clicked.connect(
            self.guardar_demanda_zona
        )

        self.cargar_datos()

    # ======================================

    def crear_panel_demanda_zona(self):

        self.panel_demanda_zona = QFrame()
        self.panel_demanda_zona.setObjectName("card")
        layout = QVBoxLayout(self.panel_demanda_zona)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Demanda por zona y turno"))

        formulario = QHBoxLayout()

        self.selector_zona_demanda = QComboBox()
        self.selector_zona_demanda.setEditable(True)

        self.selector_turno_demanda = QComboBox()

        self.selector_dia_demanda = QComboBox()
        self.selector_dia_demanda.addItem("", "")

        for dia in DIAS_SEMANA:

            self.selector_dia_demanda.addItem(dia, dia)

        self.campo_fecha_demanda = QLineEdit()
        self.campo_fecha_demanda.setPlaceholderText("YYYY-MM-DD")

        self.campo_repartidores_demanda = QSpinBox()
        self.campo_repartidores_demanda.setRange(0, 200)
        self.campo_repartidores_demanda.setValue(1)

        formulario.addWidget(QLabel("Zona"))
        formulario.addWidget(self.selector_zona_demanda)
        formulario.addWidget(QLabel("Turno"))
        formulario.addWidget(self.selector_turno_demanda)
        formulario.addWidget(QLabel("Dia"))
        formulario.addWidget(self.selector_dia_demanda)
        formulario.addWidget(QLabel("Fecha"))
        formulario.addWidget(self.campo_fecha_demanda)
        formulario.addWidget(QLabel("Repartidores"))
        formulario.addWidget(self.campo_repartidores_demanda)

        layout.addLayout(formulario)

        acciones = QHBoxLayout()
        self.btn_agregar_demanda_zona = make_button(
            "Agregar demanda",
            "secondary"
        )
        self.btn_eliminar_demanda_zona = make_button(
            "Eliminar demanda",
            "secondary"
        )
        self.btn_guardar_demanda_zona = make_button(
            "Guardar demanda por zona",
            "primary"
        )
        acciones.addWidget(self.btn_agregar_demanda_zona)
        acciones.addWidget(self.btn_eliminar_demanda_zona)
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar_demanda_zona)
        layout.addLayout(acciones)

        self.tabla_demanda_zona = QTableWidget()
        configure_table(self.tabla_demanda_zona)
        layout.addWidget(self.tabla_demanda_zona)

        self.layout.addWidget(self.panel_demanda_zona)

    # ======================================

    def cargar_datos(self):

        self.cargar_demanda_zona()
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

    def cargar_demanda_zona(self):

        self.turnos_demanda_zona = turnos_repository.listar_activos()
        self.demandas_zona = [
            {
                "id": demanda[0],
                "zona": demanda[1],
                "turno_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            }
            for demanda in demandas_zona_repository.listar()
            if demanda[6]
        ]

        zonas = set(demandas_zona_repository.listar_zonas())
        zonas.update(demanda["zona"] for demanda in self.demandas_zona)

        texto_actual = self.selector_zona_demanda.currentText()
        self.selector_zona_demanda.clear()

        for zona in sorted(zonas):

            self.selector_zona_demanda.addItem(zona, zona)

        if texto_actual:

            self.selector_zona_demanda.setCurrentText(texto_actual)

        turno_actual = self.selector_turno_demanda.currentData()
        self.selector_turno_demanda.clear()

        for turno in self.turnos_demanda_zona:

            self.selector_turno_demanda.addItem(turno[2], turno[0])

        indice_turno = self.selector_turno_demanda.findData(turno_actual)

        if indice_turno >= 0:

            self.selector_turno_demanda.setCurrentIndex(indice_turno)

        self.refrescar_tabla_demanda_zona()

    # ======================================

    def agregar_demanda_zona(self):

        zona = self.selector_zona_demanda.currentText().strip()
        turno_id = self.selector_turno_demanda.currentData()
        dia_semana = self.selector_dia_demanda.currentData() or None
        fecha = self.campo_fecha_demanda.text().strip() or None

        if not zona:

            QMessageBox.warning(self, "Demanda por zona", "Introduce una zona.")
            return

        if not turno_id:

            QMessageBox.warning(self, "Demanda por zona", "Selecciona un turno.")
            return

        if bool(fecha) == bool(dia_semana):

            QMessageBox.warning(
                self,
                "Demanda por zona",
                "Configura una fecha concreta o un dia de semana, solo uno."
            )
            return

        clave = (
            zona.casefold(),
            int(turno_id),
            "fecha" if fecha else "dia",
            fecha or dia_semana
        )

        for demanda in self.demandas_zona:

            clave_existente = (
                demanda["zona"].casefold(),
                int(demanda["turno_id"]),
                "fecha" if demanda.get("fecha") else "dia",
                demanda.get("fecha") or demanda.get("dia_semana")
            )

            if clave == clave_existente:

                QMessageBox.warning(
                    self,
                    "Demanda por zona",
                    "Ya existe demanda para esa zona, turno y periodo."
                )
                return

        self.demandas_zona.append({
            "zona": zona,
            "turno_id": int(turno_id),
            "fecha": fecha,
            "dia_semana": dia_semana,
            "repartidores_necesarios": self.campo_repartidores_demanda.value(),
            "activo": 1
        })
        self.refrescar_tabla_demanda_zona()

    # ======================================

    def eliminar_demanda_zona(self):

        fila = self.tabla_demanda_zona.currentRow()

        if fila < 0 or fila >= len(self.demandas_zona):

            QMessageBox.warning(
                self,
                "Demanda por zona",
                "Selecciona una demanda."
            )
            return

        del self.demandas_zona[fila]
        self.refrescar_tabla_demanda_zona()

    # ======================================

    def guardar_demanda_zona(self):

        try:

            demandas_zona_repository.guardar(self.demandas_zona)

        except ValueError as error:

            QMessageBox.warning(self, "Demanda por zona", str(error))
            return

        self.cargar_demanda_zona()
        QMessageBox.information(
            self,
            "Demanda por zona",
            "Demanda por zona guardada."
        )

    # ======================================

    def refrescar_tabla_demanda_zona(self):

        nombres_turno = {
            turno[0]: turno[2]
            for turno in self.turnos_demanda_zona
        }

        self.tabla_demanda_zona.setColumnCount(5)
        self.tabla_demanda_zona.setHorizontalHeaderLabels([
            "Zona",
            "Turno",
            "Dia",
            "Fecha",
            "Repartidores"
        ])
        self.tabla_demanda_zona.setRowCount(len(self.demandas_zona))

        for fila, demanda in enumerate(self.demandas_zona):

            valores = [
                demanda["zona"],
                nombres_turno.get(demanda["turno_id"], demanda["turno_id"]),
                demanda.get("dia_semana") or "",
                demanda.get("fecha") or "",
                demanda["repartidores_necesarios"]
            ]
            self.pintar_fila(self.tabla_demanda_zona, fila, valores)

        self.tabla_demanda_zona.resizeColumnsToContents()

    # ======================================

    def cargar_integraciones(self):

        datos = integraciones_repository.listar_configuraciones()

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

        datos = integraciones_repository.listar_eventos()

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
