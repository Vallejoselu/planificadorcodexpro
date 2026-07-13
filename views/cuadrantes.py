from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
    QMessageBox,
    QAbstractItemView,
    QDateEdit,
    QDialog,
    QTextEdit,
    QDialogButtonBox
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
        self.restaurantes = []
        self.repartidores = []
        self.asignaciones = {}
        self.celdas_semana = {}
        self.filas_locales = []
        self.portapapeles = None
        self.undo_stack = QUndoStack(self)

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Calendario semanal")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        barra = QHBoxLayout()

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

        self.btn_generar = QPushButton("Generar cuadrante")
        self.btn_generar.setProperty("variant", "primary")
        self.btn_asignar = QPushButton("Asignar")
        self.btn_asignar.setProperty("variant", "primary")
        self.btn_copiar = QPushButton("Copiar")
        self.btn_pegar = QPushButton("Pegar")
        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_deshacer = QPushButton("Deshacer")
        self.btn_rehacer = QPushButton("Rehacer")
        self.btn_actualizar = QPushButton("Actualizar")

        self.selector_vista.addItem("Semana", "semana")
        self.selector_vista.addItem("Por local", "local")

        self.btn_copiar.setShortcut("Ctrl+C")
        self.btn_pegar.setShortcut("Ctrl+V")
        self.btn_eliminar.setShortcut("Del")
        self.btn_deshacer.setShortcut("Ctrl+Z")
        self.btn_rehacer.setShortcut("Ctrl+Y")

        barra.addWidget(QLabel("Semana"))
        barra.addWidget(self.selector_semana)
        barra.addWidget(QLabel("Vista"))
        barra.addWidget(self.selector_vista)
        barra.addWidget(self.estado_semana)
        barra.addWidget(self.btn_generar)
        barra.addWidget(self.selector_restaurante)
        barra.addWidget(self.selector_turno)
        barra.addWidget(self.selector_repartidor)
        barra.addWidget(self.btn_asignar)
        barra.addWidget(self.btn_copiar)
        barra.addWidget(self.btn_pegar)
        barra.addWidget(self.btn_eliminar)
        barra.addWidget(self.btn_deshacer)
        barra.addWidget(self.btn_rehacer)
        barra.addWidget(self.btn_actualizar)
        barra.addStretch()

        self.layout.addLayout(barra)

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

        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.selector_semana.dateChanged.connect(self.cambiar_semana)
        self.selector_vista.currentIndexChanged.connect(self.cambiar_vista)
        self.btn_generar.clicked.connect(self.generar_cuadrante)
        self.btn_asignar.clicked.connect(self.asignar_seleccion)
        self.btn_copiar.clicked.connect(self.copiar)
        self.btn_pegar.clicked.connect(self.pegar)
        self.btn_eliminar.clicked.connect(self.eliminar)
        self.btn_deshacer.clicked.connect(self.undo_stack.undo)
        self.btn_rehacer.clicked.connect(self.undo_stack.redo)

        self.cargar_datos()

    # ======================================

    def cambiar_semana(self):

        self.undo_stack.clear()
        self.cargar_tabla()

    # ======================================

    def cambiar_vista(self):

        vista_local = self.selector_vista.currentData() == "local"
        self.tabla.setVisible(not vista_local)
        self.tabla_locales.setVisible(vista_local)

    # ======================================

    def fecha_inicio_semana(self):

        return normalizar_fecha_inicio_semana(
            self.selector_semana.date().toPython()
        )

    # ======================================

    def generar_cuadrante(self):

        try:

            generacion = cuadrantes_service.generar_cuadrante(
                self.contexto_cuadrante(),
                self.fecha_inicio_semana()
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "No se puede generar el cuadrante",
                (
                    f"{error}\n\n"
                    "Revisa que existan repartidores, restaurantes, "
                    "turnos y demanda configurada para esta semana."
                )
            )
            return

        resultado = generacion["resultado"]
        asignaciones = generacion["asignaciones"]

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

    def contexto_cuadrante(self):

        return {
            "ciudades": self.ciudades,
            "turnos": self.turnos,
            "restaurantes": self.restaurantes,
            "restaurante_turnos": self.restaurante_turnos,
            "demandas_restaurante": self.demandas_restaurante,
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
        self.repartidores = contexto["repartidores"]

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
            self.repartidores
        )
        self.asignaciones = estado["asignaciones"]
        self.celdas_semana = estado["celdas_semana"]
        self.filas_locales = estado["filas_locales"]
        self.estado_semana.setText(estado["estado_texto"])

        self.pintar_tabla()
        self.pintar_tabla_locales()
        self.cambiar_vista()

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

                self.tabla.setItem(fila, columna, item)

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

    def fila_turno(self, turno_id):

        for fila, turno in enumerate(self.turnos):

            if turno[0] == turno_id:

                return fila

        return None

    # ======================================

class DialogoResumenGeneracion(QDialog):

    def __init__(self, parent, texto):
        super().__init__(parent)

        self.setWindowTitle("Revisar cuadrante generado")
        self.resize(640, 520)

        layout = QVBoxLayout(self)

        resultado = QTextEdit()
        resultado.setReadOnly(True)
        resultado.setPlainText(texto)

        botones = QDialogButtonBox()
        guardar = botones.addButton(
            "Guardar cuadrante",
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
