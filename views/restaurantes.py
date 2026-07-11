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

from database.database import (
    eliminar_restaurante,
    obtener_repartidores,
    obtener_repartidores_fijos,
    obtener_restaurante,
    obtener_restaurantes
)
from ui.widgets import configure_table
from views.nuevo_restaurante import NuevoRestaurante


class VistaRestaurantes(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        # -------------------------
        # Titulo
        # -------------------------

        titulo = QLabel("Gestion de restaurantes")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        # -------------------------
        # Barra de botones
        # -------------------------

        barra = QHBoxLayout()

        self.btn_nuevo = QPushButton("Nuevo restaurante")
        self.btn_nuevo.setProperty("variant", "primary")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Eliminar")
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

        self.tabla.setColumnCount(9)

        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Zona",
            "Direccion",
            "Telefono",
            "Activo",
            "Horario comida",
            "Horario cena",
            "Repartidores fijos"
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
        self.btn_nuevo.clicked.connect(self.nuevo_restaurante)
        self.btn_editar.clicked.connect(self.editar_restaurante)
        self.btn_eliminar.clicked.connect(self.eliminar_restaurante)
        self.tabla.doubleClicked.connect(self.editar_restaurante)

        # -------------------------
        # Cargar datos
        # -------------------------

        self.cargar_tabla()

    # ======================================

    def cargar_tabla(self):

        datos = obtener_restaurantes()
        nombres_repartidores = self.obtener_nombres_repartidores()

        self.tabla.setRowCount(len(datos))

        for fila, r in enumerate(datos):

            repartidores_fijos = obtener_repartidores_fijos(r[0])

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
                QTableWidgetItem(r[3] if r[3] else "")
            )

            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(r[2] if r[2] else "")
            )

            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(r[4] if r[4] else "")
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem("Si" if r[6] else "No")
            )

            self.tabla.setItem(
                fila,
                6,
                QTableWidgetItem(r[7] if r[7] else "")
            )

            self.tabla.setItem(
                fila,
                7,
                QTableWidgetItem(r[8] if r[8] else "")
            )

            self.tabla.setItem(
                fila,
                8,
                QTableWidgetItem(
                    ", ".join([
                        nombres_repartidores.get(id_repartidor, "")
                        for id_repartidor in repartidores_fijos
                    ])
                )
            )

    # ======================================

    def obtener_nombres_repartidores(self):

        nombres = {}

        for repartidor in obtener_repartidores():

            nombres[repartidor[0]] = repartidor[1]

        return nombres

    # ======================================

    def restaurante_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Error",
                "Selecciona un restaurante."
            )
            return None

        return int(self.tabla.item(fila, 0).text())

    # ======================================

    def nuevo_restaurante(self):

        ventana = NuevoRestaurante()

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def editar_restaurante(self):

        id_restaurante = self.restaurante_seleccionado()

        if not id_restaurante:

            return

        restaurante = obtener_restaurante(id_restaurante)
        repartidores_fijos = obtener_repartidores_fijos(id_restaurante)

        ventana = NuevoRestaurante(
            restaurante,
            repartidores_fijos
        )

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def eliminar_restaurante(self):

        id_restaurante = self.restaurante_seleccionado()

        if not id_restaurante:

            return

        respuesta = QMessageBox.question(
            self,
            "Eliminar restaurante",
            "Quieres eliminar el restaurante seleccionado?"
        )

        if respuesta == QMessageBox.Yes:

            eliminar_restaurante(id_restaurante)

            self.cargar_tabla()
