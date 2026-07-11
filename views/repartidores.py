from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)

from repositories.repartidores_repository import RepartidoresRepository
from services.descansos import descanso_es_valido
from services.rule_engine import dias_no_disponibles, tiene_dias_consecutivos
from ui.widgets import configure_table
from views.nuevo_repartidor import NuevoRepartidor

repartidores_repository = RepartidoresRepository()


class VistaRepartidores(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # -------------------------
        # Titulo
        # -------------------------

        titulo = QLabel("Gestion de repartidores")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        # -------------------------
        # Barra de botones
        # -------------------------

        barra = QHBoxLayout()

        self.btn_nuevo = QPushButton("Nuevo repartidor")
        self.btn_nuevo.setProperty("variant", "primary")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_actualizar = QPushButton("Actualizar")

        barra.addWidget(self.btn_nuevo)
        barra.addWidget(self.btn_editar)
        barra.addWidget(self.btn_eliminar)
        barra.addWidget(self.btn_actualizar)
        barra.addStretch()

        self.layout.addLayout(barra)

        # -------------------------
        # Tabla
        # -------------------------

        self.tabla = QTableWidget()
        configure_table(self.tabla)

        self.tabla.setColumnCount(7)

        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Horas",
            "Zona",
            "Descanso",
            "Disponibilidad",
            "Doble turno"
        ])

        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.layout.addWidget(self.tabla)

        # -------------------------
        # Eventos
        # -------------------------

        self.btn_actualizar.clicked.connect(self.cargar_tabla)
        self.btn_nuevo.clicked.connect(self.nuevo_repartidor)
        self.btn_editar.clicked.connect(self.editar_repartidor)
        self.btn_eliminar.clicked.connect(self.desactivar_repartidor)

        # -------------------------
        # Cargar datos
        # -------------------------

        self.cargar_tabla()

    # ======================================

    def cargar_tabla(self):

        datos = repartidores_repository.listar_activos()

        self.tabla.setRowCount(len(datos))

        for fila, r in enumerate(datos):

            self.tabla.setItem(
                fila,
                0,
                QTableWidgetItem(str(r[0]))
            )

            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(r[1])
            )

            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem(str(r[2]))
            )

            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(r[3] if r[3] else "")
            )

            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(
                    self.formatear_descanso(r)
                )
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem(
                    self.formatear_disponibilidad(r[11])
                    if len(r) > 11
                    else ""
                )
            )

            self.tabla.setItem(
                fila,
                6,
                QTableWidgetItem("Si" if r[4] else "No")
            )

    # ======================================

    def nuevo_repartidor(self):

        ventana = NuevoRepartidor()

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def editar_repartidor(self):

        id_repartidor = self.id_seleccionado()

        if not id_repartidor:

            QMessageBox.warning(
                self,
                "Error",
                "Selecciona un repartidor."
            )
            return

        repartidor = repartidores_repository.obtener_por_id(id_repartidor)

        if not repartidor:

            QMessageBox.warning(
                self,
                "Error",
                "No se ha encontrado el repartidor."
            )
            return

        ventana = NuevoRepartidor(repartidor)

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def desactivar_repartidor(self):

        id_repartidor = self.id_seleccionado()

        if not id_repartidor:

            QMessageBox.warning(
                self,
                "Error",
                "Selecciona un repartidor."
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Desactivar repartidor",
            "Quieres desactivar este repartidor?"
        )

        if respuesta != QMessageBox.Yes:

            return

        repartidores_repository.desactivar(id_repartidor)
        self.cargar_tabla()

    # ======================================

    def id_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            return None

        item = self.tabla.item(fila, 0)

        if not item:

            return None

        return int(item.text())

    # ======================================

    def formatear_descanso(self, repartidor):

        if not repartidor[9] or not repartidor[10]:

            no_laborables = dias_no_disponibles({
                "disponibilidad": repartidor[11] if len(repartidor) > 11 else {}
            })

            if tiene_dias_consecutivos(no_laborables):

                return "No necesario por disponibilidad semanal"

            return "Pendiente de configurar"

        descanso = f"{repartidor[9]} - {repartidor[10]}"

        if not descanso_es_valido(repartidor[9], repartidor[10]):

            return descanso + " (no valido: corregir manualmente)"

        return descanso

    # ======================================

    def formatear_disponibilidad(self, disponibilidad):

        if not disponibilidad:

            return ""

        etiquetas = []

        for dia, turnos in disponibilidad.items():

            if "comida" in turnos and "noche" in turnos:

                valor = "ambos"

            elif "comida" in turnos:

                valor = "comidas"

            elif "noche" in turnos:

                valor = "cenas"

            else:

                valor = "no"

            etiquetas.append(f"{dia}: {valor}")

        return " | ".join(etiquetas)
