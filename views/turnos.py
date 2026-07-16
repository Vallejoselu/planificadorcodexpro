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

from services.turnos_service import TurnosService
from ui.widgets import configure_table
from views.nuevo_turno import NuevoTurno

turnos_service = TurnosService()


class VistaTurnos(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # -------------------------
        # Titulo
        # -------------------------

        titulo = QLabel("Gestion de turnos")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        # -------------------------
        # Barra de botones
        # -------------------------

        barra = QHBoxLayout()

        self.btn_nuevo = QPushButton("Nuevo turno")
        self.btn_nuevo.setProperty("variant", "primary")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_eliminar.setToolTip(
            "Desactiva el turno para nuevas planificaciones. "
            "No borra cuadrantes anteriores."
        )
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

        self.tabla.setColumnCount(8)

        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Tipo",
            "Nombre",
            "Inicio",
            "Fin",
            "Color",
            "Duracion",
            "Activo"
        ])

        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )

        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setSelectionMode(QTableWidget.SingleSelection)

        self.layout.addWidget(self.tabla)

        # -------------------------
        # Eventos
        # -------------------------

        self.btn_actualizar.clicked.connect(self.cargar_tabla)
        self.btn_nuevo.clicked.connect(self.nuevo_turno)
        self.btn_editar.clicked.connect(self.editar_turno)
        self.btn_eliminar.clicked.connect(self.eliminar_turno)
        self.tabla.doubleClicked.connect(self.editar_turno)

        # -------------------------
        # Cargar datos
        # -------------------------

        self.cargar_tabla()

    # ======================================

    def cargar_tabla(self):

        datos = turnos_service.listar_todos()

        self.tabla.setRowCount(len(datos))

        for fila, turno in enumerate(datos):

            self.tabla.setItem(
                fila,
                0,
                QTableWidgetItem(str(turno[0]))
            )

            self.tabla.setItem(
                fila,
                1,
                QTableWidgetItem(turno[1])
            )

            self.tabla.setItem(
                fila,
                2,
                QTableWidgetItem(turno[2])
            )

            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(turno[3])
            )

            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(turno[4])
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem(turno[5])
            )

            self.tabla.setItem(
                fila,
                6,
                QTableWidgetItem(str(turno[6]))
            )

            self.tabla.setItem(
                fila,
                7,
                QTableWidgetItem("Si" if turno[7] else "No")
            )

    # ======================================

    def turno_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Turnos",
                "Selecciona un turno de la tabla para continuar."
            )
            return None

        return int(self.tabla.item(fila, 0).text())

    # ======================================

    def nuevo_turno(self):

        ventana = NuevoTurno()

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def editar_turno(self):

        id_turno = self.turno_seleccionado()

        if not id_turno:

            return

        turno = turnos_service.obtener_por_id(id_turno)

        ventana = NuevoTurno(turno)

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def eliminar_turno(self):

        id_turno = self.turno_seleccionado()

        if not id_turno:

            return

        respuesta = QMessageBox.question(
            self,
            "Desactivar turno",
            (
                "Quieres desactivar el turno seleccionado?\n\n"
                "No aparecera en nuevas planificaciones, pero se conservaran "
                "sus cuadrantes anteriores."
            )
        )

        if respuesta == QMessageBox.Yes:

            turnos_service.desactivar(id_turno)

            self.cargar_tabla()
