from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QMessageBox,
    QAbstractItemView,
    QDateEdit,
    QDialog,
    QTextEdit,
    QDialogButtonBox,
    QLineEdit,
    QCheckBox,
    QSizePolicy
)

from PySide6.QtGui import QColor, QBrush, QUndoCommand, QUndoStack
from PySide6.QtCore import Qt, QDate

from database.schema import DIAS_SEMANA
from services.cuadrantes_service import CuadrantesService
from services.fechas import normalizar_fecha_inicio_semana
from ui.widgets import configure_table


cuadrantes_service = CuadrantesService()


class VistaCuadrantes(QWidget):

    def __init__(self):
        super().__init__()

        self.turnos = []
        self.ciudades = []
        self.restaurante_turnos = []
        self.demandas_restaurante = []
        self.demandas_zona = []
        self.demandas_ciudad = []
        self.restaurantes = []
        self.repartidores = []
        self.asignaciones = {}
        self.alertas = []
        self.celdas_semana = {}
        self.filas_locales = []
        self.filas_repartidores = []
        self.plantillas = []
        self.portapapeles = None
        self.undo_stack = QUndoStack(self)

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Calendario semanal")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        self.guia_operativa = QLabel(
            "Para generar bien: crea repartidores activos, restaurantes, "
            "turnos y demanda. 'Sin repartidor' significa plaza pendiente "
            "de cubrir; no es una persona asignada."
        )
        self.guia_operativa.setWordWrap(True)
        self.guia_operativa.setObjectName("guia_operativa")
        self.guia_operativa.setStyleSheet("""
            padding:10px 12px;
            border:1px solid #334155;
            border-radius:6px;
            background:#0F172A;
            color:#E2E8F0;
        """)
        self.layout.addWidget(self.guia_operativa)

        self.leyenda_cuadrante = QLabel(
            "Leyenda: LIBRE = no trabaja | COMIDA = turno de comida | "
            "CENA = turno de cena | DOBLE = comida y cena | - = disponible "
            "sin turno | Sin repartidor = plaza pendiente"
        )
        self.leyenda_cuadrante.setWordWrap(True)
        self.leyenda_cuadrante.setObjectName("guia_operativa")
        self.leyenda_cuadrante.setStyleSheet("""
            padding:8px 12px;
            border:1px solid #CBD5E1;
            border-radius:6px;
            background:#F8FAFC;
            color:#1E293B;
        """)
        self.layout.addWidget(self.leyenda_cuadrante)

        self.selector_restaurante = QComboBox()
        self.selector_turno = QComboBox()
        self.selector_repartidor = QComboBox()
        self.selector_vista = QComboBox()
        self.selector_semana = QDateEdit()
        self.selector_semana.setCalendarPopup(True)
        self.selector_semana.setDisplayFormat("yyyy-MM-dd")
        hoy = QDate.currentDate()
        self.selector_semana.setDate(
            hoy.addDays(1 - hoy.dayOfWeek())
        )
        self.estado_semana = QLabel("")
        self.estado_semana.setMinimumWidth(170)
        self.estado_semana.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.detalle_seleccion = QLabel(
            "Selecciona una celda para ver que se va a editar."
        )
        self.detalle_seleccion.setWordWrap(True)
        self.detalle_seleccion.setObjectName("detalle_seleccion")
        self.diagnostico_cuadrante = QLabel("")
        self.diagnostico_cuadrante.setWordWrap(True)
        self.diagnostico_cuadrante.setObjectName("guia_operativa")
        self.estado_publicacion = QLabel("Estado: borrador")
        self.estado_publicacion.setWordWrap(True)

        self.btn_comprobar = QPushButton("Comprobar configuracion")
        self.btn_generar = QPushButton("Generar cuadrante")
        self.btn_generar.setProperty("variant", "primary")
        self.btn_marcar_listo = QPushButton("Marcar listo")
        self.btn_publicar = QPushButton("Publicar")
        self.btn_publicar.setProperty("variant", "primary")
        self.btn_editar = QPushButton("Editar celda")
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.setProperty("variant", "primary")
        self.btn_copiar = QPushButton("Copiar")
        self.btn_pegar = QPushButton("Pegar")
        self.btn_copiar_semana = QPushButton("Copiar semana")
        self.btn_guardar_plantilla = QPushButton("Guardar plantilla")
        self.btn_aplicar_plantilla = QPushButton("Aplicar plantilla")
        self.btn_eliminar = QPushButton("Quitar asignacion")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_eliminar.setToolTip(
            "Quita la asignacion seleccionada del cuadrante. "
            "No elimina restaurantes ni repartidores."
        )
        self.btn_deshacer = QPushButton("Deshacer")
        self.btn_rehacer = QPushButton("Rehacer")
        self.btn_actualizar = QPushButton("Actualizar")

        self.selector_vista.addItem("Semana", "semana")
        self.selector_vista.addItem("Por local", "local")
        self.selector_vista.addItem("Por empleado", "empleado")
        self.selector_vista.setCurrentIndex(2)

        self.btn_copiar.setShortcut("Ctrl+C")
        self.btn_pegar.setShortcut("Ctrl+V")
        self.btn_eliminar.setShortcut("Del")
        self.btn_deshacer.setShortcut("Ctrl+Z")
        self.btn_rehacer.setShortcut("Ctrl+Y")

        self.configurar_controles_barra()
        self.crear_barras_superiores()

        self.tabla = TablaCalendario(self)
        configure_table(self.tabla)
        self.tabla.setColumnCount(len(DIAS_SEMANA))
        self.tabla.setHorizontalHeaderLabels(DIAS_SEMANA)
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla.verticalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectItems)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)
        self.tabla.setDragDropMode(QAbstractItemView.InternalMove)
        self.tabla.setDragEnabled(True)
        self.tabla.setAcceptDrops(True)
        self.tabla.setDropIndicatorShown(True)
        self.tabla.itemSelectionChanged.connect(
            self.actualizar_detalle_seleccion
        )
        self.tabla.cellDoubleClicked.connect(self.editar_celda)

        self.layout.addWidget(self.tabla)

        self.tabla_locales = QTableWidget(self)
        configure_table(self.tabla_locales)
        self.tabla_locales.setColumnCount(len(DIAS_SEMANA) + 1)
        self.tabla_locales.setHorizontalHeaderLabels([
            "Local",
            *DIAS_SEMANA
        ])
        self.tabla_locales.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla_locales.verticalHeader().setVisible(False)
        self.tabla_locales.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_locales.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_locales.hide()

        self.layout.addWidget(self.tabla_locales)

        self.tabla_empleados = QTableWidget(self)
        configure_table(self.tabla_empleados)
        self.tabla_empleados.setColumnCount(len(DIAS_SEMANA) + 2)
        self.tabla_empleados.setHorizontalHeaderLabels([
            "Empleado",
            "Contrato",
            *DIAS_SEMANA
        ])
        self.tabla_empleados.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        self.tabla_empleados.horizontalHeader().setSectionResizeMode(
            0,
            QHeaderView.ResizeToContents
        )
        self.tabla_empleados.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.ResizeToContents
        )
        self.tabla_empleados.verticalHeader().setVisible(False)
        self.tabla_empleados.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_empleados.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla_empleados.hide()

        self.layout.addWidget(self.tabla_empleados)

        self.titulo_alertas = QLabel("Alertas del cuadrante")
        self.titulo_alertas.setStyleSheet("font-weight:bold;")
        self.layout.addWidget(self.titulo_alertas)

        self.tabla_alertas = QTableWidget(self)
        configure_table(self.tabla_alertas)
        self.tabla_alertas.setColumnCount(3)
        self.tabla_alertas.setHorizontalHeaderLabels([
            "Tipo",
            "Detalle",
            "Nivel"
        ])
        self.tabla_alertas.horizontalHeader().setSectionResizeMode(
            1,
            QHeaderView.Stretch
        )
        self.tabla_alertas.verticalHeader().setVisible(False)
        self.tabla_alertas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_alertas.setMaximumHeight(180)
        self.layout.addWidget(self.tabla_alertas)

        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.selector_semana.dateChanged.connect(self.cambiar_semana)
        self.selector_vista.currentIndexChanged.connect(self.cambiar_vista)
        self.btn_comprobar.clicked.connect(self.comprobar_configuracion)
        self.btn_generar.clicked.connect(self.generar_cuadrante)
        self.btn_marcar_listo.clicked.connect(self.marcar_cuadrante_listo)
        self.btn_publicar.clicked.connect(self.publicar_cuadrante)
        self.btn_editar.clicked.connect(self.editar_celda_actual)
        self.btn_asignar.clicked.connect(self.asignar_seleccion)
        self.btn_copiar.clicked.connect(self.copiar)
        self.btn_pegar.clicked.connect(self.pegar)
        self.btn_copiar_semana.clicked.connect(self.copiar_semana)
        self.btn_guardar_plantilla.clicked.connect(self.guardar_plantilla)
        self.btn_aplicar_plantilla.clicked.connect(self.aplicar_plantilla)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.btn_deshacer.clicked.connect(self.undo_stack.undo)
        self.btn_rehacer.clicked.connect(self.undo_stack.redo)

        self.cargar_datos()

    # ======================================

    def configurar_controles_barra(self):

        self.selector_semana.setFixedWidth(112)
        self.selector_vista.setFixedWidth(96)
        self.selector_restaurante.setMinimumWidth(160)
        self.selector_turno.setMinimumWidth(130)
        self.selector_repartidor.setMinimumWidth(150)

        for selector in (
            self.selector_restaurante,
            self.selector_turno,
            self.selector_repartidor
        ):

            selector.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        for boton in (
            self.btn_comprobar,
            self.btn_generar,
            self.btn_marcar_listo,
            self.btn_publicar,
            self.btn_editar,
            self.btn_asignar,
            self.btn_copiar,
            self.btn_pegar,
            self.btn_copiar_semana,
            self.btn_guardar_plantilla,
            self.btn_aplicar_plantilla,
            self.btn_eliminar,
            self.btn_deshacer,
            self.btn_rehacer,
            self.btn_actualizar
        ):

            boton.setMinimumHeight(36)
            boton.setMinimumWidth(max(82, boton.sizeHint().width() + 18))
            boton.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    # ======================================

    def crear_barras_superiores(self):

        self.barra_filtros_widget = QWidget()
        barra_filtros = QHBoxLayout(self.barra_filtros_widget)
        barra_filtros.setContentsMargins(0, 0, 0, 0)
        barra_filtros.setSpacing(8)

        barra_filtros.addWidget(QLabel("Semana"))
        barra_filtros.addWidget(self.selector_semana)
        barra_filtros.addWidget(QLabel("Vista"))
        barra_filtros.addWidget(self.selector_vista)
        barra_filtros.addWidget(self.estado_semana)
        barra_filtros.addWidget(self.btn_comprobar)
        barra_filtros.addWidget(self.btn_generar)
        barra_filtros.addWidget(self.btn_marcar_listo)
        barra_filtros.addWidget(self.btn_publicar)

        self.barra_acciones_widget = QWidget()
        barra_acciones = QHBoxLayout(self.barra_acciones_widget)
        barra_acciones.setContentsMargins(0, 0, 0, 0)
        barra_acciones.setSpacing(8)

        barra_acciones.addWidget(self.selector_restaurante)
        barra_acciones.addWidget(self.selector_turno)
        barra_acciones.addWidget(self.selector_repartidor)
        barra_acciones.addWidget(self.btn_editar)
        barra_acciones.addWidget(self.btn_asignar)
        barra_acciones.addWidget(self.btn_copiar)
        barra_acciones.addWidget(self.btn_pegar)
        barra_acciones.addWidget(self.btn_copiar_semana)
        barra_acciones.addWidget(self.btn_guardar_plantilla)
        barra_acciones.addWidget(self.btn_aplicar_plantilla)
        barra_acciones.addWidget(self.btn_eliminar)
        barra_acciones.addWidget(self.btn_deshacer)
        barra_acciones.addWidget(self.btn_rehacer)
        barra_acciones.addWidget(self.btn_actualizar)

        self.barra_filtros_scroll = self.crear_barra_desplazable(
            self.barra_filtros_widget
        )
        self.barra_acciones_scroll = self.crear_barra_desplazable(
            self.barra_acciones_widget
        )

        self.layout.addWidget(self.barra_filtros_scroll)
        self.layout.addWidget(self.barra_acciones_scroll)
        self.layout.addWidget(self.detalle_seleccion)
        self.layout.addWidget(self.diagnostico_cuadrante)
        self.layout.addWidget(self.estado_publicacion)

    # ======================================

    def crear_barra_desplazable(self, widget):

        widget.adjustSize()
        widget.setMinimumWidth(widget.sizeHint().width())
        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidgetResizable(False)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        scroll.setWidget(widget)
        scroll.setFixedHeight(widget.sizeHint().height() + 18)
        return scroll

    # ======================================

    def cambiar_semana(self):

        self.undo_stack.clear()
        self.cargar_tabla()

    # ======================================

    def cambiar_vista(self):

        vista = self.selector_vista.currentData()
        vista_local = vista == "local"
        vista_empleado = vista == "empleado"
        self.tabla.setVisible(vista == "semana")
        self.tabla_locales.setVisible(vista_local)
        self.tabla_empleados.setVisible(vista_empleado)

    # ======================================

    def fecha_inicio_semana(self):

        return normalizar_fecha_inicio_semana(
            self.selector_semana.date().toPython()
        )

    # ======================================

    def generar_cuadrante(self):

        precomprobacion = cuadrantes_service.precomprobar_generacion(
            self.contexto_cuadrante(),
            self.fecha_inicio_semana()
        )

        if not precomprobacion["puede_generar"]:

            QMessageBox.warning(
                self,
                "No se puede generar el cuadrante",
                precomprobacion["texto"]
            )
            return

        try:

            generacion = cuadrantes_service.generar_cuadrante(
                self.contexto_cuadrante(),
                self.fecha_inicio_semana()
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "No se puede generar el cuadrante",
                str(error)
            )
            return

        resultado = generacion["resultado"]
        asignaciones = generacion["asignaciones"]
        self.actualizar_panel_alertas(
            cuadrantes_service.alertas_generacion(resultado)
        )

        if not self.mostrar_resumen_generacion(resultado):

            return

        if self.hay_asignaciones_guardadas():

            if not self.confirmar_sobrescritura():

                return

        cuadrantes_service.guardar_cuadrante(
            self.fecha_inicio_semana(),
            asignaciones
        )
        self.cargar_datos()

        QMessageBox.information(
            self,
            "Generar cuadrante",
            (
                "Cuadrante guardado correctamente para la semana "
                f"{self.texto_fecha_inicio_semana()}."
            )
        )

    # ======================================

    def comprobar_configuracion(self):

        precomprobacion = cuadrantes_service.precomprobar_generacion(
            self.contexto_cuadrante(),
            self.fecha_inicio_semana()
        )
        titulo = (
            "Configuracion lista"
            if precomprobacion["puede_generar"]
            else "Configuracion incompleta"
        )

        QMessageBox.information(
            self,
            titulo,
            precomprobacion["texto"]
        )

    # ======================================

    def contexto_cuadrante(self):

        return {
            "ciudades": self.ciudades,
            "turnos": self.turnos,
            "restaurantes": self.restaurantes,
            "restaurante_turnos": self.restaurante_turnos,
            "demandas_restaurante": self.demandas_restaurante,
            "demandas_zona": self.demandas_zona,
            "demandas_ciudad": self.demandas_ciudad,
            "repartidores": self.repartidores
        }

    # ======================================

    def mostrar_resumen_generacion(self, resultado):

        dialogo = DialogoResumenGeneracion(
            self,
            cuadrantes_service.texto_resumen_generacion(resultado)
        )

        return dialogo.exec() == QDialog.Accepted

    # ======================================

    def hay_asignaciones_guardadas(self):

        return cuadrantes_service.semana_tiene_datos(
            self.fecha_inicio_semana()
        )

    # ======================================

    def confirmar_sobrescritura(self):

        mensaje = QMessageBox(self)
        mensaje.setWindowTitle("Sobrescribir semana")
        mensaje.setText(
            (
                "La semana "
                f"{self.texto_fecha_inicio_semana()} "
                "ya tiene horarios guardados."
            )
        )
        mensaje.setInformativeText(
            (
                "Si continuas se reemplazaran solo los turnos de esa "
                "semana. Las semanas anteriores y posteriores se conservaran."
            )
        )
        boton_sobrescribir = mensaje.addButton(
            "Sobrescribir semana",
            QMessageBox.AcceptRole
        )
        mensaje.addButton(
            "Cancelar",
            QMessageBox.RejectRole
        )
        mensaje.exec()

        return mensaje.clickedButton() == boton_sobrescribir

    # ======================================

    def confirmar_sobrescritura_destino(self, fecha_destino):

        mensaje = QMessageBox(self)
        mensaje.setWindowTitle("Copiar semana")
        mensaje.setText(
            (
                "La semana destino "
                f"{fecha_destino} ya tiene horarios guardados."
            )
        )
        mensaje.setInformativeText(
            (
                "Si continuas se reemplazaran solo los turnos de esa "
                "semana. La semana origen no se modificara."
            )
        )
        boton_sobrescribir = mensaje.addButton(
            "Copiar y sobrescribir",
            QMessageBox.AcceptRole
        )
        mensaje.addButton(
            "Cancelar",
            QMessageBox.RejectRole
        )
        mensaje.exec()

        return mensaje.clickedButton() == boton_sobrescribir

    # ======================================

    def texto_fecha_inicio_semana(self):

        fecha = self.fecha_inicio_semana()

        if hasattr(fecha, "isoformat"):

            return fecha.isoformat()

        return str(fecha)

    # ======================================

    def cargar_datos(self):

        contexto = cuadrantes_service.obtener_contexto()
        self.ciudades = contexto["ciudades"]
        self.turnos = contexto["turnos"]
        self.restaurantes = contexto["restaurantes"]
        self.restaurante_turnos = contexto["restaurante_turnos"]
        self.demandas_restaurante = contexto["demandas_restaurante"]
        self.demandas_zona = contexto["demandas_zona"]
        self.demandas_ciudad = contexto["demandas_ciudad"]
        self.repartidores = contexto["repartidores"]
        self.plantillas = cuadrantes_service.listar_plantillas()

        self.cargar_selectores()
        self.cargar_tabla()

    # ======================================

    def cargar_selectores(self):

        self.selector_restaurante.clear()
        self.selector_turno.clear()
        self.selector_repartidor.clear()

        for restaurante in self.restaurantes:

            self.selector_restaurante.addItem(
                restaurante[1],
                restaurante[0]
            )

        for turno in self.turnos:

            self.selector_turno.addItem(
                turno[2],
                turno[0]
            )

        self.selector_repartidor.addItem("Sin repartidor", None)

        for repartidor in self.repartidores:

            self.selector_repartidor.addItem(
                repartidor[1],
                repartidor[0]
            )

    # ======================================

    def cargar_tabla(self):

        self.tabla.clearContents()
        self.tabla.setRowCount(len(self.turnos))

        self.tabla.setVerticalHeaderLabels([
            turno[2]
            for turno in self.turnos
        ])

        estado = cuadrantes_service.preparar_estado_semana(
            self.fecha_inicio_semana(),
            self.turnos,
            self.restaurantes,
            self.repartidores,
            demandas_restaurante=self.demandas_restaurante,
            demandas_zona=self.demandas_zona,
            demandas_ciudad=self.demandas_ciudad,
            restaurante_turnos=self.restaurante_turnos
        )
        self.asignaciones = estado["asignaciones"]
        self.alertas = estado["alertas"]
        self.celdas_semana = estado["celdas_semana"]
        self.filas_locales = estado["filas_locales"]
        self.filas_repartidores = estado["filas_repartidores"]
        self.estado_semana.setText(estado["estado_texto"])
        self.estado_semana.setToolTip(estado["estado_texto"])
        self.actualizar_diagnostico(estado["diagnostico"])
        self.actualizar_publicacion(estado["publicacion"])

        self.pintar_tabla()
        self.pintar_tabla_locales()
        self.pintar_tabla_empleados()
        self.actualizar_panel_alertas(self.alertas)
        self.cambiar_vista()
        self.actualizar_detalle_seleccion()

    # ======================================

    def pintar_tabla(self):

        for fila, turno in enumerate(self.turnos):

            for columna, dia in enumerate(DIAS_SEMANA):

                celda = self.celdas_semana.get((dia, turno[0]), {})

                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)

                if celda.get("texto"):

                    item.setText(celda["texto"])

                if celda.get("tooltip"):

                    item.setToolTip(celda["tooltip"])

                if celda.get("fondo"):

                    item.setBackground(
                        QBrush(QColor(celda["fondo"]))
                    )

                if celda.get("color_texto"):

                    item.setForeground(
                        QBrush(QColor(celda["color_texto"]))
                    )

                item.setData(
                    Qt.UserRole,
                    {
                        "dia": dia,
                        "turno_id": turno[0]
                    }
                )
                self.tabla.setItem(fila, columna, item)

    # ======================================

    def actualizar_detalle_seleccion(self):

        detalle = self.detalle_celda_actual()
        self.detalle_seleccion.setText(detalle["texto"])
        self.detalle_seleccion.setToolTip(detalle["tooltip"])
        self.sincronizar_selectores_con_celda(detalle)

    # ======================================

    def detalle_celda_actual(self):

        clave = self.clave_actual()

        if not clave:

            return {
                "texto": (
                    "Selecciona una celda para ver que se va a editar."
                ),
                "tooltip": ""
            }

        dia, turno_id = clave
        turno = self.turno_por_id(turno_id)
        asignaciones = self.asignaciones.get(clave, [])
        nombre_turno = turno[2] if turno else "Turno"
        horario = cuadrantes_service.texto_horario_turno(turno)
        partes = [
            f"Seleccion: {dia.capitalize()} | {nombre_turno}"
        ]

        if horario:

            partes.append(horario)

        if asignaciones:

            partes.append(
                f"{len(asignaciones)} asignacion(es) en esta celda."
            )
            for asignacion in asignaciones:

                partes.append(
                    "- "
                    + self.texto_asignacion_resumen(asignacion)
                )

        else:

            partes.append(
                "Sin asignacion. Puedes asignar desde los controles o "
                "hacer doble clic para editar."
            )

        texto = "\n".join(partes)

        return {
            "texto": texto,
            "tooltip": texto,
            "dia": dia,
            "turno_id": turno_id,
            "turno": turno,
            "asignaciones": asignaciones
        }

    # ======================================

    def texto_asignacion_resumen(self, asignacion):

        restaurante = self.restaurante_por_id(
            asignacion.get("restaurante_id")
        )
        repartidor = self.repartidor_por_id(
            asignacion.get("repartidor_id")
        )
        return (
            f"{restaurante[1] if restaurante else 'Restaurante desconocido'}"
            " - "
            f"{repartidor[1] if repartidor else 'Sin repartidor'}"
        )

    # ======================================

    def sincronizar_selectores_con_celda(self, detalle):

        if not detalle.get("turno_id"):

            return

        self.seleccionar_combo(self.selector_turno, detalle["turno_id"])
        asignaciones = detalle.get("asignaciones") or []

        if len(asignaciones) != 1:

            return

        asignacion = asignaciones[0]
        self.seleccionar_combo(
            self.selector_restaurante,
            asignacion.get("restaurante_id")
        )
        self.seleccionar_combo(
            self.selector_repartidor,
            asignacion.get("repartidor_id")
        )

    # ======================================

    def seleccionar_combo(self, combo, valor):

        indice = combo.findData(valor)

        if indice >= 0:

            combo.setCurrentIndex(indice)

    # ======================================

    def editar_celda(self, fila, columna):

        clave = self.clave_celda(fila, columna)

        if not clave:

            return

        dia, turno_id = clave
        turno = self.turno_por_id(turno_id)
        asignaciones = self.asignaciones.get(clave, [])
        asignacion = asignaciones[0] if asignaciones else {}
        dialogo = DialogoEditarAsignacion(
            self,
            dia,
            turno,
            self.restaurantes,
            self.repartidores,
            asignacion
        )

        if dialogo.exec() != QDialog.Accepted:

            return

        if dialogo.vaciar():

            self.aplicar_comando(
                dia,
                turno_id,
                None,
                None,
                fila,
                columna,
                limpiar=True
            )
            return

        self.aplicar_edicion_celda(
            dia,
            turno_id,
            dialogo.restaurante_id(),
            dialogo.repartidor_id(),
            fila,
            columna
        )

    # ======================================

    def editar_celda_actual(self):

        fila = self.tabla.currentRow()
        columna = self.tabla.currentColumn()

        if fila < 0 or columna < 0:

            QMessageBox.warning(
                self,
                "Editar celda",
                "Selecciona una celda del cuadrante antes de editar."
            )
            return

        self.editar_celda(fila, columna)

    # ======================================

    def aplicar_edicion_celda(
        self,
        dia,
        turno_id,
        restaurante_id,
        repartidor_id,
        fila,
        columna
    ):

        anterior = cuadrantes_service.clonar_asignaciones_turno(
            self.asignaciones.get((dia, turno_id), [])
        )
        nuevo = cuadrantes_service.agregar_asignacion(
            [],
            restaurante_id,
            repartidor_id
        )
        propuestas = self.asignaciones_con_cambio(dia, turno_id, nuevo)

        if not self.validar_asignaciones_propuestas(propuestas):

            return

        self.undo_stack.push(
            CambioCalendario(
                self,
                self.fecha_inicio_semana(),
                dia,
                turno_id,
                anterior,
                nuevo,
                fila,
                columna
            )
        )

    # ======================================

    def turno_por_id(self, turno_id):

        for turno in self.turnos:

            if turno[0] == turno_id:

                return turno

        return None

    # ======================================

    def restaurante_por_id(self, restaurante_id):

        for restaurante in self.restaurantes:

            if restaurante[0] == restaurante_id:

                return restaurante

        return None

    # ======================================

    def repartidor_por_id(self, repartidor_id):

        for repartidor in self.repartidores:

            if repartidor[0] == repartidor_id:

                return repartidor

        return None

    # ======================================

    def pintar_tabla_locales(self):

        self.tabla_locales.clearContents()
        self.tabla_locales.setRowCount(len(self.filas_locales))

        for fila, restaurante in enumerate(self.filas_locales):

            self.tabla_locales.setItem(
                fila,
                0,
                QTableWidgetItem(restaurante["nombre"])
            )

            for columna, dia in enumerate(DIAS_SEMANA, start=1):

                item = QTableWidgetItem(
                    restaurante["dias"].get(dia, "")
                )
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.tabla_locales.setItem(fila, columna, item)

    # ======================================

    def pintar_tabla_empleados(self):

        self.tabla_empleados.clearContents()
        self.tabla_empleados.setRowCount(len(self.filas_repartidores))

        for fila, repartidor in enumerate(self.filas_repartidores):

            self.tabla_empleados.setItem(
                fila,
                0,
                QTableWidgetItem(repartidor["nombre"])
            )
            self.tabla_empleados.setItem(
                fila,
                1,
                QTableWidgetItem(repartidor["contrato"])
            )

            for columna, dia in enumerate(DIAS_SEMANA, start=2):

                celda = repartidor["celdas"].get(dia, {})
                item = QTableWidgetItem(celda.get("texto", ""))
                item.setTextAlignment(Qt.AlignCenter)
                item.setToolTip(celda.get("tooltip", ""))
                item.setBackground(
                    QBrush(QColor(
                        self.color_celda_empleado(celda.get("estado"))
                    ))
                )
                item.setForeground(
                    QBrush(QColor(
                        self.color_texto_celda_empleado(celda.get("estado"))
                    ))
                )
                self.tabla_empleados.setItem(fila, columna, item)

        self.tabla_empleados.resizeRowsToContents()

    # ======================================

    def color_celda_empleado(self, estado):

        colores = {
            "libre": "#FEE2E2",
            "doble": "#FEF3C7",
            "comida": "#DBEAFE",
            "cena": "#EDE9FE",
            "disponible": "#F8FAFC",
            "turno": "#DCFCE7"
        }

        return colores.get(estado, "#F8FAFC")

    # ======================================

    def color_texto_celda_empleado(self, estado):

        colores = {
            "libre": "#7F1D1D",
            "doble": "#78350F",
            "comida": "#1E3A8A",
            "cena": "#312E81",
            "disponible": "#475569",
            "turno": "#14532D"
        }

        return colores.get(estado, "#334155")

    # ======================================

    def actualizar_panel_alertas(self, alertas):

        self.alertas = alertas or []
        filas = self.alertas or [{
            "tipo": "Sin alertas",
            "detalle": "No hay problemas detectados en el cuadrante.",
            "severidad": "ok"
        }]
        self.tabla_alertas.clearContents()
        self.tabla_alertas.setRowCount(len(filas))

        colores = {
            "alta": ("#FEE2E2", "#7F1D1D"),
            "media": ("#FEF3C7", "#78350F"),
            "ok": ("#DCFCE7", "#14532D")
        }

        for fila, alerta in enumerate(filas):

            valores = [
                alerta.get("tipo", ""),
                alerta.get("detalle", ""),
                alerta.get("severidad", "")
            ]
            fondo, texto = colores.get(
                alerta.get("severidad"),
                ("#F8FAFC", "#334155")
            )

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                item.setBackground(QBrush(QColor(fondo)))
                item.setForeground(QBrush(QColor(texto)))
                self.tabla_alertas.setItem(fila, columna, item)

        self.tabla_alertas.resizeColumnsToContents()

    # ======================================

    def actualizar_diagnostico(self, diagnostico):

        self.diagnostico_cuadrante.setText(diagnostico.get("texto", ""))
        self.diagnostico_cuadrante.setToolTip(
            diagnostico.get("resumen", "")
        )

    # ======================================

    def actualizar_publicacion(self, publicacion):

        estado = publicacion.get("estado", "borrador")
        texto = f"Estado de publicacion: {estado}"

        if publicacion.get("publicado_en"):

            texto += f" | Publicado: {publicacion['publicado_en']}"

        self.estado_publicacion.setText(texto)
        self.estado_publicacion.setToolTip(publicacion.get("resumen", ""))

    # ======================================

    def marcar_cuadrante_listo(self):

        try:

            revision = cuadrantes_service.marcar_cuadrante_listo(
                self.fecha_inicio_semana(),
                self.turnos,
                self.restaurantes,
                self.repartidores,
                demandas_restaurante=self.demandas_restaurante,
                demandas_zona=self.demandas_zona,
                demandas_ciudad=self.demandas_ciudad,
                restaurante_turnos=self.restaurante_turnos
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "No se puede marcar listo",
                str(error)
            )
            return

        self.cargar_datos()
        QMessageBox.information(
            self,
            "Cuadrante listo",
            revision["resumen"]
        )

    # ======================================

    def publicar_cuadrante(self):

        try:

            revision = cuadrantes_service.publicar_cuadrante(
                self.fecha_inicio_semana(),
                self.turnos,
                self.restaurantes,
                self.repartidores,
                demandas_restaurante=self.demandas_restaurante,
                demandas_zona=self.demandas_zona,
                demandas_ciudad=self.demandas_ciudad,
                restaurante_turnos=self.restaurante_turnos
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "No se puede publicar",
                str(error)
            )
            return

        self.cargar_datos()
        QMessageBox.information(
            self,
            "Cuadrante publicado",
            revision["resumen"]
        )

    # ======================================

    def asignar_seleccion(self):

        fila = self.tabla.currentRow()
        columna = self.tabla.currentColumn()

        if fila < 0 or columna < 0:

            QMessageBox.warning(
                self,
                "Asignar turno",
                "Selecciona una celda del calendario antes de asignar."
            )
            return

        if self.selector_restaurante.currentData() is None:

            QMessageBox.warning(
                self,
                "Asignar turno",
                (
                    "No hay restaurantes activos. Crea un restaurante "
                    "antes de asignar turnos."
                )
            )
            return

        if self.selector_turno.currentData() is None:

            QMessageBox.warning(
                self,
                "Asignar turno",
                "No hay turnos activos. Crea un turno antes de asignar."
            )
            return

        turno_id = self.selector_turno.currentData()
        dia = DIAS_SEMANA[columna]
        fila_turno = self.fila_turno(turno_id)

        if fila_turno is None:

            return

        self.aplicar_comando(
            dia,
            turno_id,
            self.selector_restaurante.currentData(),
            self.selector_repartidor.currentData(),
            fila_turno,
            columna
        )

    # ======================================

    def aplicar_comando(
        self,
        dia,
        turno_id,
        restaurante_id,
        repartidor_id,
        fila,
        columna,
        limpiar=False
    ):

        cambio = cuadrantes_service.preparar_cambio_asignacion(
            self.asignaciones,
            dia,
            turno_id,
            restaurante_id,
            repartidor_id,
            limpiar
        )
        if not limpiar:

            propuestas = self.asignaciones_con_cambio(
                dia,
                turno_id,
                cambio["nuevo"]
            )

            if not self.validar_asignaciones_propuestas(propuestas):

                return

        self.undo_stack.push(
            CambioCalendario(
                self,
                self.fecha_inicio_semana(),
                dia,
                turno_id,
                cambio["anterior"],
                cambio["nuevo"],
                fila,
                columna
            )
        )

    # ======================================

    def aplicar_asignacion(self, dia, turno_id, asignaciones):

        self.aplicar_asignacion_semana(
            self.fecha_inicio_semana(),
            dia,
            turno_id,
            asignaciones
        )

    # ======================================

    def aplicar_asignacion_semana(
        self,
        fecha_inicio_semana,
        dia,
        turno_id,
        asignaciones
    ):

        asignaciones = asignaciones or []
        fecha_inicio_semana = normalizar_fecha_inicio_semana(
            fecha_inicio_semana
        )

        if asignaciones:

            self.asignaciones[(dia, turno_id)] = (
                cuadrantes_service.clonar_asignaciones_turno(asignaciones)
            )
            cuadrantes_service.guardar_asignacion_turno(
                fecha_inicio_semana,
                dia,
                turno_id,
                asignaciones
            )

        else:

            self.asignaciones.pop((dia, turno_id), None)
            cuadrantes_service.guardar_asignacion_turno(
                fecha_inicio_semana,
                dia,
                turno_id,
                []
            )

        self.actualizar_presentacion_asignaciones()
        self.pintar_tabla()
        self.pintar_tabla_locales()

    # ======================================

    def actualizar_presentacion_asignaciones(self):

        self.celdas_semana = cuadrantes_service.construir_celdas_semana(
            self.asignaciones,
            self.turnos,
            self.restaurantes,
            self.repartidores
        )
        self.filas_locales = cuadrantes_service.construir_filas_locales(
            self.asignaciones,
            self.turnos,
            self.restaurantes,
            self.repartidores
        )
        self.filas_repartidores = (
            cuadrantes_service.construir_filas_repartidores(
                self.asignaciones,
                self.turnos,
                self.restaurantes,
                self.repartidores,
                self.fecha_inicio_semana()
            )
        )

    # ======================================

    def mover_asignacion(self, fila_origen, columna_origen, fila_destino, columna_destino):

        if fila_origen == fila_destino and columna_origen == columna_destino:

            return

        if fila_origen < 0 or columna_origen < 0:

            return

        origen = self.clave_celda(fila_origen, columna_origen)
        destino = self.clave_celda(fila_destino, columna_destino)

        if not origen or not destino:

            return

        asignacion = self.asignaciones.get(origen)

        if not asignacion:

            return

        propuestas = {
            clave: [
                dict(item)
                for item in elementos
            ]
            for clave, elementos in self.asignaciones.items()
        }
        propuestas.pop(origen, None)
        propuestas[destino] = [
            dict(item)
            for item in asignacion
        ]

        if not self.validar_asignaciones_propuestas(propuestas):

            return

        self.undo_stack.push(
            MoverCalendario(
                self,
                self.fecha_inicio_semana(),
                origen,
                destino,
                [dict(item) for item in asignacion],
                self.asignaciones.get(destino)
            )
        )

    # ======================================

    def copiar(self):

        clave = self.clave_actual()

        if not clave:

            return

        asignacion = self.asignaciones.get(clave)

        if asignacion:

            self.portapapeles = [
                dict(item)
                for item in asignacion
            ]

    # ======================================

    def copiar_semana(self):

        dialogo = DialogoCopiarSemana(
            self,
            self.fecha_inicio_semana()
        )

        if dialogo.exec() != QDialog.Accepted:

            return

        fecha_origen = dialogo.fecha_origen()
        fecha_destino = dialogo.fecha_destino()

        try:

            if fecha_origen == fecha_destino:

                raise ValueError(
                    "La semana origen y la semana destino deben ser distintas."
                )

            if not cuadrantes_service.semana_tiene_datos(fecha_origen):

                raise ValueError(
                    "La semana origen no tiene cuadrante guardado."
                )

            if cuadrantes_service.semana_tiene_datos(fecha_destino):

                if not self.confirmar_sobrescritura_destino(fecha_destino):

                    return

            resultado = cuadrantes_service.copiar_semana(
                fecha_origen,
                fecha_destino
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Copiar semana",
                str(error)
            )
            return

        self.selector_semana.setDate(
            QDate.fromString(fecha_destino, "yyyy-MM-dd")
        )
        self.cargar_datos()

        QMessageBox.information(
            self,
            "Copiar semana",
            (
                "Semana copiada correctamente.\n\n"
                f"Origen: {resultado['fecha_origen']}\n"
                f"Destino: {resultado['fecha_destino']}\n"
                f"Asignaciones copiadas: {resultado['total_asignaciones']}"
            )
        )

    # ======================================

    def guardar_plantilla(self):

        dialogo = DialogoGuardarPlantilla(
            self,
            self.fecha_inicio_semana()
        )

        if dialogo.exec() != QDialog.Accepted:

            return

        try:

            resultado = cuadrantes_service.crear_plantilla_desde_semana(
                self.fecha_inicio_semana(),
                dialogo.nombre(),
                dialogo.descripcion(),
                dialogo.incluir_repartidores()
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Guardar plantilla",
                str(error)
            )
            return

        self.plantillas = cuadrantes_service.listar_plantillas()

        QMessageBox.information(
            self,
            "Guardar plantilla",
            (
                "Plantilla guardada correctamente.\n\n"
                f"Nombre: {resultado['nombre']}\n"
                f"Asignaciones guardadas: {resultado['total_asignaciones']}"
            )
        )

    # ======================================

    def aplicar_plantilla(self):

        self.plantillas = cuadrantes_service.listar_plantillas()
        dialogo = DialogoAplicarPlantilla(
            self,
            self.plantillas,
            self.fecha_inicio_semana()
        )

        if dialogo.exec() != QDialog.Accepted:

            return

        plantilla_id = dialogo.plantilla_id()
        fecha_destino = dialogo.fecha_destino()

        if plantilla_id is None:

            QMessageBox.warning(
                self,
                "Aplicar plantilla",
                "Selecciona una plantilla."
            )
            return

        try:

            if cuadrantes_service.semana_tiene_datos(fecha_destino):

                if not self.confirmar_sobrescritura_destino(fecha_destino):

                    return

            resultado = cuadrantes_service.aplicar_plantilla(
                plantilla_id,
                fecha_destino
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Aplicar plantilla",
                str(error)
            )
            return

        self.selector_semana.setDate(
            QDate.fromString(fecha_destino, "yyyy-MM-dd")
        )
        self.cargar_datos()

        QMessageBox.information(
            self,
            "Aplicar plantilla",
            (
                "Plantilla aplicada correctamente.\n\n"
                f"Plantilla: {resultado['nombre']}\n"
                f"Destino: {resultado['fecha_destino']}\n"
                f"Asignaciones aplicadas: {resultado['total_asignaciones']}"
            )
        )

    # ======================================

    def pegar(self):

        if not self.portapapeles:

            return

        clave = self.clave_actual()

        if not clave:

            return

        fila = self.tabla.currentRow()
        columna = self.tabla.currentColumn()
        anterior = [
            dict(asignacion)
            for asignacion in self.asignaciones.get(clave, [])
        ]
        nuevo = cuadrantes_service.clonar_asignaciones_turno(anterior)

        for asignacion in self.portapapeles:

            nuevo = cuadrantes_service.agregar_asignacion(
                nuevo,
                asignacion.get("restaurante_id"),
                asignacion.get("repartidor_id")
            )

        propuestas = self.asignaciones_con_cambio(
            clave[0],
            clave[1],
            nuevo
        )

        if not self.validar_asignaciones_propuestas(propuestas):

            return

        self.undo_stack.push(
            CambioCalendario(
                self,
                self.fecha_inicio_semana(),
                clave[0],
                clave[1],
                anterior,
                nuevo,
                fila,
                columna
            )
        )

    # ======================================

    def eliminar(self):

        clave = self.clave_actual()

        if not clave:

            QMessageBox.warning(
                self,
                "Quitar asignacion",
                (
                    "Selecciona una celda del cuadrante para quitar su "
                    "asignacion.\n\n"
                    "Este boton no elimina restaurantes ni repartidores."
                )
            )
            return

        fila = self.tabla.currentRow()
        columna = self.tabla.currentColumn()

        self.aplicar_comando(
            clave[0],
            clave[1],
            None,
            None,
            fila,
            columna,
            limpiar=True
        )

    # ======================================

    def clave_actual(self):

        return self.clave_celda(
            self.tabla.currentRow(),
            self.tabla.currentColumn()
        )

    # ======================================

    def clave_celda(self, fila, columna):

        if fila < 0 or columna < 0:

            return None

        if fila >= len(self.turnos) or columna >= len(DIAS_SEMANA):

            return None

        return (
            DIAS_SEMANA[columna],
            self.turnos[fila][0]
        )

    # ======================================

    def asignaciones_con_cambio(self, dia, turno_id, nuevas):

        propuestas = {
            clave: [
                dict(item)
                for item in elementos
            ]
            for clave, elementos in self.asignaciones.items()
        }

        if nuevas:

            propuestas[(dia, turno_id)] = [
                dict(item)
                for item in nuevas
            ]

        else:

            propuestas.pop((dia, turno_id), None)

        return propuestas

    # ======================================

    def validar_asignaciones_propuestas(self, propuestas):

        try:

            cuadrantes_service.validar_asignaciones_semana(
                propuestas,
                self.fecha_inicio_semana(),
                self.turnos,
                self.restaurantes,
                self.repartidores
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Asignacion no permitida",
                str(error)
            )
            return False

        return True

    # ======================================

    def fila_turno(self, turno_id):

        for fila, turno in enumerate(self.turnos):

            if turno[0] == turno_id:

                return fila

        return None

    # ======================================

class DialogoEditarAsignacion(QDialog):

    def __init__(
        self,
        parent,
        dia,
        turno,
        restaurantes,
        repartidores,
        asignacion=None
    ):
        super().__init__(parent)

        self._vaciar = False
        self.setWindowTitle("Editar asignacion")
        self.setMinimumWidth(420)
        asignacion = asignacion or {}

        layout = QVBoxLayout(self)
        nombre_turno = turno[2] if turno else "Turno"
        horario = cuadrantes_service.texto_horario_turno(turno)
        resumen = QLabel(
            f"{dia.capitalize()} | {nombre_turno}"
            + (f"\n{horario}" if horario else "")
        )
        resumen.setWordWrap(True)
        resumen.setStyleSheet("font-weight:bold;")
        layout.addWidget(resumen)

        layout.addWidget(QLabel("Restaurante"))
        self.selector_restaurante = QComboBox()

        for restaurante in restaurantes:

            self.selector_restaurante.addItem(restaurante[1], restaurante[0])

        layout.addWidget(self.selector_restaurante)

        layout.addWidget(QLabel("Repartidor"))
        self.selector_repartidor = QComboBox()
        self.selector_repartidor.addItem("Sin repartidor", None)

        for repartidor in repartidores:

            self.selector_repartidor.addItem(repartidor[1], repartidor[0])

        layout.addWidget(self.selector_repartidor)
        self.seleccionar_valor(
            self.selector_restaurante,
            asignacion.get("restaurante_id")
        )
        self.seleccionar_valor(
            self.selector_repartidor,
            asignacion.get("repartidor_id")
        )

        botones = QDialogButtonBox()
        guardar = botones.addButton(
            "Guardar cambios",
            QDialogButtonBox.AcceptRole
        )
        vaciar = botones.addButton(
            "Vaciar celda",
            QDialogButtonBox.DestructiveRole
        )
        cancelar = botones.addButton(
            "Cancelar",
            QDialogButtonBox.RejectRole
        )
        guardar.clicked.connect(self.accept)
        vaciar.clicked.connect(self.aceptar_vacio)
        cancelar.clicked.connect(self.reject)
        layout.addWidget(botones)

    def seleccionar_valor(self, combo, valor):

        indice = combo.findData(valor)

        if indice >= 0:

            combo.setCurrentIndex(indice)

    def aceptar_vacio(self):

        self._vaciar = True
        self.accept()

    def vaciar(self):

        return self._vaciar

    def restaurante_id(self):

        return self.selector_restaurante.currentData()

    def repartidor_id(self):

        return self.selector_repartidor.currentData()


class DialogoResumenGeneracion(QDialog):

    def __init__(self, parent, texto):
        super().__init__(parent)

        self.setWindowTitle("Vista previa del cuadrante")
        self.resize(640, 520)

        layout = QVBoxLayout(self)

        resultado = QTextEdit()
        resultado.setReadOnly(True)
        resultado.setPlainText(texto)

        botones = QDialogButtonBox()
        guardar = botones.addButton(
            "Confirmar y guardar",
            QDialogButtonBox.AcceptRole
        )
        cancelar = botones.addButton(
            "Cancelar",
            QDialogButtonBox.RejectRole
        )
        guardar.clicked.connect(self.accept)
        cancelar.clicked.connect(self.reject)

        layout.addWidget(resultado)
        layout.addWidget(botones)


class DialogoCopiarSemana(QDialog):

    def __init__(self, parent, fecha_origen):
        super().__init__(parent)

        self.setWindowTitle("Copiar semana")
        self.resize(360, 160)

        layout = QVBoxLayout(self)

        self.selector_origen = QDateEdit()
        self.selector_origen.setCalendarPopup(True)
        self.selector_origen.setDisplayFormat("yyyy-MM-dd")
        self.selector_origen.setDate(
            QDate.fromString(
                normalizar_fecha_inicio_semana(fecha_origen),
                "yyyy-MM-dd"
            )
        )

        self.selector_destino = QDateEdit()
        self.selector_destino.setCalendarPopup(True)
        self.selector_destino.setDisplayFormat("yyyy-MM-dd")
        self.selector_destino.setDate(
            self.selector_origen.date().addDays(7)
        )

        fila_origen = QHBoxLayout()
        fila_origen.addWidget(QLabel("Semana origen"))
        fila_origen.addWidget(self.selector_origen)

        fila_destino = QHBoxLayout()
        fila_destino.addWidget(QLabel("Semana destino"))
        fila_destino.addWidget(self.selector_destino)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.button(QDialogButtonBox.Ok).setText("Copiar semana")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout.addLayout(fila_origen)
        layout.addLayout(fila_destino)
        layout.addWidget(botones)

    def fecha_origen(self):

        return normalizar_fecha_inicio_semana(
            self.selector_origen.date().toPython()
        )

    def fecha_destino(self):

        return normalizar_fecha_inicio_semana(
            self.selector_destino.date().toPython()
        )


class DialogoGuardarPlantilla(QDialog):

    def __init__(self, parent, fecha_origen):
        super().__init__(parent)

        self.setWindowTitle("Guardar plantilla")
        self.resize(420, 260)

        layout = QVBoxLayout(self)

        fecha = QLabel(
            "Semana origen: "
            + normalizar_fecha_inicio_semana(fecha_origen)
        )
        self.campo_nombre = QLineEdit()
        self.campo_nombre.setPlaceholderText("Nombre de la plantilla")
        self.campo_descripcion = QTextEdit()
        self.campo_descripcion.setPlaceholderText("Descripcion")
        self.campo_descripcion.setFixedHeight(80)
        self.check_repartidores = QCheckBox(
            "Incluir repartidores asignados"
        )
        self.check_repartidores.setChecked(True)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.button(QDialogButtonBox.Ok).setText("Guardar plantilla")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout.addWidget(fecha)
        layout.addWidget(QLabel("Nombre"))
        layout.addWidget(self.campo_nombre)
        layout.addWidget(QLabel("Descripcion"))
        layout.addWidget(self.campo_descripcion)
        layout.addWidget(self.check_repartidores)
        layout.addWidget(botones)

    def nombre(self):

        return self.campo_nombre.text().strip()

    def descripcion(self):

        return self.campo_descripcion.toPlainText().strip()

    def incluir_repartidores(self):

        return self.check_repartidores.isChecked()


class DialogoAplicarPlantilla(QDialog):

    def __init__(self, parent, plantillas, fecha_destino):
        super().__init__(parent)

        self.setWindowTitle("Aplicar plantilla")
        self.resize(420, 180)
        self.plantillas = plantillas

        layout = QVBoxLayout(self)

        self.selector_plantilla = QComboBox()

        for plantilla in plantillas:

            detalle = (
                "con repartidores"
                if plantilla[3]
                else "solo restaurantes/turnos"
            )
            self.selector_plantilla.addItem(
                f"{plantilla[1]} ({detalle})",
                plantilla[0]
            )

        self.selector_destino = QDateEdit()
        self.selector_destino.setCalendarPopup(True)
        self.selector_destino.setDisplayFormat("yyyy-MM-dd")
        self.selector_destino.setDate(
            QDate.fromString(
                normalizar_fecha_inicio_semana(fecha_destino),
                "yyyy-MM-dd"
            )
        )

        fila_destino = QHBoxLayout()
        fila_destino.addWidget(QLabel("Semana destino"))
        fila_destino.addWidget(self.selector_destino)

        botones = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        botones.button(QDialogButtonBox.Ok).setText("Aplicar plantilla")
        botones.button(QDialogButtonBox.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)

        layout.addWidget(QLabel("Plantilla"))
        layout.addWidget(self.selector_plantilla)
        layout.addLayout(fila_destino)
        layout.addWidget(botones)

    def plantilla_id(self):

        return self.selector_plantilla.currentData()

    def fecha_destino(self):

        return normalizar_fecha_inicio_semana(
            self.selector_destino.date().toPython()
        )


class TablaCalendario(QTableWidget):

    def __init__(self, calendario):
        super().__init__()

        self.calendario = calendario

    def dropEvent(self, event):

        origen = self.currentIndex()

        if hasattr(event, "position"):

            posicion = event.position().toPoint()

        else:

            posicion = event.pos()

        destino = self.indexAt(posicion)

        if destino.isValid():

            self.calendario.mover_asignacion(
                origen.row(),
                origen.column(),
                destino.row(),
                destino.column()
            )

            event.accept()
            return

        super().dropEvent(event)


class CambioCalendario(QUndoCommand):

    def __init__(
        self,
        calendario,
        fecha_inicio_semana,
        dia,
        turno_id,
        anterior,
        nuevo,
        fila,
        columna
    ):
        super().__init__("Cambiar turno")

        self.calendario = calendario
        self.fecha_inicio_semana = fecha_inicio_semana
        self.dia = dia
        self.turno_id = turno_id
        self.anterior = anterior
        self.nuevo = nuevo
        self.fila = fila
        self.columna = columna

    def redo(self):

        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.dia,
            self.turno_id,
            self.nuevo
        )
        self.calendario.tabla.setCurrentCell(
            self.fila,
            self.columna
        )

    def undo(self):

        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.dia,
            self.turno_id,
            self.anterior
        )
        self.calendario.tabla.setCurrentCell(
            self.fila,
            self.columna
        )


class MoverCalendario(QUndoCommand):

    def __init__(
        self,
        calendario,
        fecha_inicio_semana,
        origen,
        destino,
        asignacion,
        destino_anterior
    ):
        super().__init__("Mover turno")

        self.calendario = calendario
        self.fecha_inicio_semana = fecha_inicio_semana
        self.origen = origen
        self.destino = destino
        self.asignacion = [
            dict(item)
            for item in asignacion
        ]
        self.destino_anterior = [
            dict(item)
            for item in (destino_anterior or [])
        ]

    def redo(self):

        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.origen[0],
            self.origen[1],
            None
        )
        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.destino[0],
            self.destino[1],
            self.asignacion
        )

    def undo(self):

        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.destino[0],
            self.destino[1],
            self.destino_anterior
        )
        self.calendario.aplicar_asignacion_semana(
            self.fecha_inicio_semana,
            self.origen[0],
            self.origen[1],
            self.asignacion
        )
