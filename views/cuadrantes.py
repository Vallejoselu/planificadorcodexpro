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
from repositories.calendario_repository import CalendarioRepository
from repositories.ciudades_repository import CiudadesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository
from services.planning_engine import PlanningEngine
from services.fechas import normalizar_fecha_inicio_semana
from ui.widgets import configure_table


calendario_repository = CalendarioRepository()
ciudades_repository = CiudadesRepository()
repartidores_repository = RepartidoresRepository()
restaurantes_repository = RestaurantesRepository()
turnos_repository = TurnosRepository()


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

        if not self.repartidores:

            QMessageBox.warning(
                self,
                "Generar cuadrante",
                "No hay repartidores activos."
            )
            return

        if not self.restaurantes:

            QMessageBox.warning(
                self,
                "Generar cuadrante",
                "No hay restaurantes activos."
            )
            return

        if not self.turnos and not self.restaurante_turnos:

            QMessageBox.warning(
                self,
                "Generar cuadrante",
                "No hay turnos activos."
            )
            return

        resultado, asignaciones = self.generar_resultado_cuadrante()

        if not self.mostrar_resumen_generacion(resultado):

            return

        if self.hay_asignaciones_guardadas():

            if not self.confirmar_sobrescritura():

                return

        self.guardar_asignaciones_generadas(asignaciones)
        self.cargar_datos()

        QMessageBox.information(
            self,
            "Generar cuadrante",
            "Cuadrante guardado correctamente."
        )

    # ======================================

    def generar_resultado_cuadrante(self):

        if self.hay_demanda_multiciudad():

            resultado = PlanningEngine().generar_multiciudad(
                self.repartidores,
                self.ciudades,
                self.restaurantes,
                self.restaurante_turnos,
                self.demandas_restaurante,
                fecha_inicio=self.fecha_inicio_semana()
            )

            return (
                resultado,
                self.convertir_resultado_multiciudad_a_asignaciones(
                    resultado
                )
            )

        turnos_engine, mapa_turnos = self.preparar_turnos_engine()
        fecha_inicio = self.fecha_inicio_semana()
        resultado = PlanningEngine().generar(
            self.repartidores,
            self.restaurantes,
            turnos_engine,
            fecha_inicio=fecha_inicio
        )

        return (
            resultado,
            self.convertir_resultado_a_asignaciones(
                resultado,
                mapa_turnos
            )
        )

    # ======================================

    def hay_demanda_multiciudad(self):

        return any(
            demanda[6]
            for demanda in self.demandas_restaurante
        )

    # ======================================

    def preparar_turnos_engine(self):

        turnos_engine = []
        mapa_turnos = {}

        for turno in self.turnos:

            clave = self.clave_turno_engine(turno)

            if clave in mapa_turnos:

                continue

            mapa_turnos[clave] = turno[0]
            turnos_engine.append({
                "nombre": clave,
                "horas": float(turno[6] or 0),
                "hora_inicio": turno[3],
                "hora_fin": turno[4]
            })

        return turnos_engine, mapa_turnos

    # ======================================

    def clave_turno_engine(self, turno):

        texto = f"{turno[1]} {turno[2]}".lower()

        if "comida" in texto:

            return "comida"

        if "cena" in texto or "noche" in texto:

            return "noche"

        return str(turno[2]).strip().lower().replace(" ", "_")

    # ======================================

    def convertir_resultado_a_asignaciones(self, resultado, mapa_turnos):

        asignaciones = {}

        for dia, turnos_dia in resultado.get("horario", {}).items():

            for nombre_turno, elementos in turnos_dia.items():

                turno_id = mapa_turnos.get(nombre_turno)

                if turno_id is None:

                    continue

                clave = (dia, turno_id)

                for elemento in elementos:

                    asignacion = {
                        "restaurante_id": elemento["restaurante_id"],
                        "repartidor_id": elemento.get("repartidor_id")
                    }

                    if asignacion not in asignaciones.setdefault(clave, []):

                        asignaciones[clave].append(asignacion)

        return asignaciones

    # ======================================

    def convertir_resultado_multiciudad_a_asignaciones(self, resultado):

        asignaciones = {}

        for dia, turnos_dia in resultado.get("horario", {}).items():

            for elementos in turnos_dia.values():

                for elemento in elementos:

                    turno_restaurante_id = elemento.get(
                        "turno_restaurante_id"
                    )

                    if not turno_restaurante_id:

                        continue

                    clave = (
                        dia,
                        ("restaurante_turno", turno_restaurante_id)
                    )
                    asignacion = {
                        "restaurante_id": elemento["restaurante_id"],
                        "repartidor_id": elemento.get("repartidor_id")
                    }

                    if asignacion not in asignaciones.setdefault(clave, []):

                        asignaciones[clave].append(asignacion)

        return asignaciones

    # ======================================

    def mostrar_resumen_generacion(self, resultado):

        dialogo = DialogoResumenGeneracion(
            self,
            self.texto_resumen_generacion(resultado)
        )

        return dialogo.exec() == QDialog.Accepted

    # ======================================

    def texto_resumen_generacion(self, resultado):

        resumen = resultado.get("resumen", [])
        incidencias = resultado.get("incidencias", [])
        sin_cubrir = [
            incidencia
            for incidencia in incidencias
            if (
                incidencia.get("motivo") == "No hay repartidor disponible"
                or incidencia.get("regla") == "minimo de repartidores por turno"
            )
        ]
        turnos_cubiertos = sum(
            len(asignaciones)
            for turnos_dia in resultado.get("horario", {}).values()
            for asignaciones in turnos_dia.values()
        )
        horas_totales = sum(
            item.get("horas", 0)
            for item in resumen
        )
        repartidores_asignados = [
            item
            for item in resumen
            if item.get("horas", 0) > 0
        ]

        lineas = [
            "Resumen del cuadrante",
            "",
            f"Repartidores asignados: {len(repartidores_asignados)}",
            f"Turnos cubiertos: {turnos_cubiertos}",
            f"Turnos sin cubrir: {len(sin_cubrir)}",
            f"Horas totales: {horas_totales:g}",
            "",
            "Repartidores"
        ]

        if repartidores_asignados:

            for item in repartidores_asignados:

                lineas.append(
                    f"- {item['nombre']}: {item['horas']:g} h"
                )

        else:

            lineas.append("- Ninguno")

        lineas.extend([
            "",
            "Turnos sin cubrir"
        ])

        if sin_cubrir:

            for incidencia in sin_cubrir:

                lineas.append(
                    "- "
                    + self.texto_incidencia(incidencia)
                )

        else:

            lineas.append("- Ninguno")

        lineas.extend([
            "",
            "Incidencias"
        ])

        if incidencias:

            for incidencia in incidencias:

                lineas.append(
                    "- "
                    + self.texto_incidencia(incidencia)
                )

        else:

            lineas.append("- Ninguna")

        return "\n".join(lineas)

    # ======================================

    def texto_incidencia(self, incidencia):

        datos = [
            incidencia.get("dia"),
            incidencia.get("turno"),
            incidencia.get("restaurante")
        ]
        cabecera = " / ".join([
            dato
            for dato in datos
            if dato
        ])
        motivo = incidencia.get("motivo", "Incidencia")

        if cabecera:

            return f"{cabecera}: {motivo}"

        return motivo

    # ======================================

    def hay_asignaciones_guardadas(self):

        return calendario_repository.semana_tiene_datos(
            self.fecha_inicio_semana()
        )

    # ======================================

    def confirmar_sobrescritura(self):

        mensaje = QMessageBox(self)
        mensaje.setWindowTitle("Sobrescribir")
        mensaje.setText(
            "Ya existen horarios para esa semana."
        )
        mensaje.setInformativeText(
            "Quieres sobrescribirlos?"
        )
        boton_sobrescribir = mensaje.addButton(
            "Sobrescribir",
            QMessageBox.AcceptRole
        )
        mensaje.addButton(
            "Cancelar",
            QMessageBox.RejectRole
        )
        mensaje.exec()

        return mensaje.clickedButton() == boton_sobrescribir

    # ======================================

    def guardar_asignaciones_generadas(self, asignaciones):

        asignaciones = self.resolver_turnos_asignaciones(asignaciones)
        calendario_repository.reemplazar_semana(
            self.fecha_inicio_semana(),
            asignaciones
        )

    # ======================================

    def resolver_turnos_asignaciones(self, asignaciones):

        resueltas = {}

        for (dia, turno_ref), elementos in (asignaciones or {}).items():

            turno_id = turno_ref

            if (
                isinstance(turno_ref, tuple)
                and turno_ref[0] == "restaurante_turno"
            ):

                turno_id = turnos_repository.obtener_o_crear_para_restaurante(
                    turno_ref[1]
                )

            resueltas[(dia, turno_id)] = elementos

        return resueltas

    # ======================================

    def cargar_datos(self):

        self.ciudades = [
            ciudad
            for ciudad in ciudades_repository.listar_activas()
            if ciudad[2]
        ]
        self.turnos = turnos_repository.listar_activos()
        self.restaurantes = restaurantes_repository.listar_activos()
        self.restaurante_turnos = []
        self.demandas_restaurante = []

        for restaurante in self.restaurantes:

            self.restaurante_turnos.extend([
                turno
                for turno in restaurantes_repository.listar_turnos(
                    restaurante[0]
                )
                if turno[7]
            ])
            self.demandas_restaurante.extend([
                demanda
                for demanda in restaurantes_repository.listar_demanda(
                    restaurante[0]
                )
                if demanda[6]
            ])

        self.repartidores = repartidores_repository.listar_activos()

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

        self.asignaciones = {}
        self.tabla.clearContents()
        self.tabla.setRowCount(len(self.turnos))

        self.tabla.setVerticalHeaderLabels([
            turno[2]
            for turno in self.turnos
        ])

        calendario = calendario_repository.listar_semana(
            self.fecha_inicio_semana()
        )

        if calendario:

            self.estado_semana.setText("")

        else:

            self.estado_semana.setText(
                "Sin datos guardados para esta semana."
            )

        for asignacion in calendario:

            dia = asignacion[1]
            turno_id = asignacion[2]
            restaurante_id = asignacion[6]
            repartidor_id = asignacion[9] if len(asignacion) > 9 else None

            self.asignaciones.setdefault((dia, turno_id), []).append({
                "restaurante_id": restaurante_id,
                "repartidor_id": repartidor_id
            })

        self.pintar_tabla()
        self.pintar_tabla_locales()
        self.cambiar_vista()

    # ======================================

    def pintar_tabla(self):

        for fila, turno in enumerate(self.turnos):

            for columna, dia in enumerate(DIAS_SEMANA):

                asignaciones = self.asignaciones.get((dia, turno[0]), [])

                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignCenter)

                if asignaciones:

                    textos = []
                    primer_restaurante = None

                    for asignacion in asignaciones:

                        restaurante = self.buscar_restaurante(
                            asignacion["restaurante_id"]
                        )

                        if not restaurante:

                            continue

                        if primer_restaurante is None:

                            primer_restaurante = restaurante

                        repartidor = self.buscar_repartidor(
                            asignacion.get("repartidor_id")
                        )
                        etiqueta_repartidor = (
                            f" - {repartidor[1]}"
                            if repartidor
                            else ""
                        )
                        textos.append(
                            f"{restaurante[1]}{etiqueta_repartidor}"
                        )

                    if textos:

                        item.setText("\n".join(textos))

                    if primer_restaurante:

                        item.setBackground(
                            QBrush(
                                QColor(
                                    self.color_restaurante(
                                        primer_restaurante[0]
                                    )
                                )
                            )
                        )
                        item.setForeground(
                            QBrush(
                                QColor(
                                    self.color_turno(turno)
                                )
                            )
                        )

                self.tabla.setItem(fila, columna, item)

    # ======================================

    def pintar_tabla_locales(self):

        self.tabla_locales.clearContents()
        self.tabla_locales.setRowCount(len(self.restaurantes))

        for fila, restaurante in enumerate(self.restaurantes):

            self.tabla_locales.setItem(
                fila,
                0,
                QTableWidgetItem(restaurante[1])
            )

            for columna, dia in enumerate(DIAS_SEMANA, start=1):

                item = QTableWidgetItem(
                    self.texto_local_dia(restaurante[0], dia)
                )
                item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
                self.tabla_locales.setItem(fila, columna, item)

    # ======================================

    def texto_local_dia(self, restaurante_id, dia):

        lineas = []

        for turno in self.turnos:

            for asignacion in self.asignaciones.get((dia, turno[0]), []):

                if asignacion["restaurante_id"] != restaurante_id:

                    continue

                repartidor = self.buscar_repartidor(
                    asignacion.get("repartidor_id")
                )
                texto = turno[2]

                if repartidor:

                    texto += f" - {repartidor[1]}"

                lineas.append(texto)

        return "\n".join(lineas)

    # ======================================

    def asignar_seleccion(self):

        fila = self.tabla.currentRow()
        columna = self.tabla.currentColumn()

        if fila < 0 or columna < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Selecciona una celda."
            )
            return

        if self.selector_restaurante.currentData() is None:

            QMessageBox.warning(
                self,
                "Error",
                "Crea un restaurante activo."
            )
            return

        if self.selector_turno.currentData() is None:

            QMessageBox.warning(
                self,
                "Error",
                "Crea un turno activo."
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

        anterior = [
            dict(asignacion)
            for asignacion in self.asignaciones.get((dia, turno_id), [])
        ]

        nuevo = [
            dict(asignacion)
            for asignacion in anterior
        ]

        if limpiar:

            nuevo = []

        elif restaurante_id:

            asignacion = {
                "restaurante_id": restaurante_id,
                "repartidor_id": repartidor_id
            }

            if asignacion not in nuevo:

                nuevo.append(asignacion)

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

            self.asignaciones[(dia, turno_id)] = [
                dict(asignacion)
                for asignacion in asignaciones
            ]
            calendario_repository.eliminar_turno(
                dia,
                turno_id,
                fecha_inicio_semana=fecha_inicio_semana
            )

            for asignacion in asignaciones:

                calendario_repository.guardar_turno(
                    dia,
                    turno_id,
                    asignacion["restaurante_id"],
                    asignacion.get("repartidor_id"),
                    fecha_inicio_semana
                )

        else:

            self.asignaciones.pop((dia, turno_id), None)
            calendario_repository.eliminar_turno(
                dia,
                turno_id,
                fecha_inicio_semana=fecha_inicio_semana
            )

        self.pintar_tabla()

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
        nuevo = [
            dict(asignacion)
            for asignacion in anterior
        ]

        for asignacion in self.portapapeles:

            if asignacion not in nuevo:

                nuevo.append(dict(asignacion))

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

    def buscar_restaurante(self, restaurante_id):

        for restaurante in self.restaurantes:

            if restaurante[0] == restaurante_id:

                return restaurante

        return None

    # ======================================

    def buscar_repartidor(self, repartidor_id):

        for repartidor in self.repartidores:

            if repartidor[0] == repartidor_id:

                return repartidor

        return None

    # ======================================

    def color_restaurante(self, restaurante_id):

        colores = [
            "#FFE599",
            "#B6D7A8",
            "#A4C2F4",
            "#D5A6BD",
            "#F9CB9C",
            "#B4A7D6",
            "#76A5AF"
        ]

        return colores[restaurante_id % len(colores)]

    # ======================================

    def color_turno(self, turno):

        colores = {
            "Comida": "#0B5394",
            "Cena": "#674EA7",
            "Turno partido": "#38761D",
            "Personalizado": "#990000"
        }

        return turno[5] or colores.get(turno[1], "#333333")


class DialogoResumenGeneracion(QDialog):

    def __init__(self, parent, texto):
        super().__init__(parent)

        self.setWindowTitle("Resumen del cuadrante")
        self.resize(640, 520)

        layout = QVBoxLayout(self)

        resultado = QTextEdit()
        resultado.setReadOnly(True)
        resultado.setPlainText(texto)

        botones = QDialogButtonBox()
        guardar = botones.addButton(
            "Guardar",
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
