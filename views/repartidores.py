from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QFileDialog,
    QMessageBox,
)

from services.repartidores_service import RepartidoresService
from ui.widgets import configure_table
from views.nuevo_repartidor import NuevoRepartidor

repartidores_service = RepartidoresService()


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
        self.btn_importar = QPushButton("Importar")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_actualizar = QPushButton("Actualizar")

        barra.addWidget(self.btn_nuevo)
        barra.addWidget(self.btn_importar)
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
        self.btn_importar.clicked.connect(self.importar_repartidores)
        self.btn_editar.clicked.connect(self.editar_repartidor)
        self.btn_eliminar.clicked.connect(self.desactivar_repartidor)

        # -------------------------
        # Cargar datos
        # -------------------------

        self.cargar_tabla()

    # ======================================

    def cargar_tabla(self):

        datos = repartidores_service.listar_activos()

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
                    repartidores_service.formatear_descanso(r)
                )
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem(
                    repartidores_service.formatear_disponibilidad(r[11])
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

    def importar_repartidores(self):

        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar repartidores",
            "",
            "Datos (*.csv *.xlsx *.xlsm)"
        )

        if not ruta:

            return

        try:

            resultado = repartidores_service.importar_desde_archivo(ruta)

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Importar repartidores",
                str(error)
            )
            return

        self.cargar_tabla()
        errores = len(resultado["errores"])
        detalle_errores = ""

        if errores:

            detalle_errores = "\n\nErrores:\n" + "\n".join(
                f"Fila {error['fila']}: {error['error']}"
                for error in resultado["errores"][:5]
            )

        QMessageBox.information(
            self,
            "Importar repartidores",
            (
                f"Leidos: {resultado['leidos']}\n"
                f"Creados: {resultado['creados']}\n"
                f"Actualizados: {resultado['actualizados']}\n"
                f"Errores: {errores}"
                f"{detalle_errores}"
            )
        )

    # ======================================

    def editar_repartidor(self):

        id_repartidor = self.id_seleccionado()

        if not id_repartidor:

            QMessageBox.warning(
                self,
                "Editar repartidor",
                "Selecciona un repartidor de la tabla para editarlo."
            )
            return

        repartidor = repartidores_service.obtener_por_id(id_repartidor)

        if not repartidor:

            QMessageBox.warning(
                self,
                "Editar repartidor",
                (
                    "No se ha encontrado el repartidor seleccionado. "
                    "Actualiza la lista e intentalo de nuevo."
                )
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
                "Desactivar repartidor",
                "Selecciona un repartidor de la tabla para desactivarlo."
            )
            return

        respuesta = QMessageBox.question(
            self,
            "Desactivar repartidor",
            (
                "Quieres desactivar este repartidor?\n\n"
                "No aparecera en nuevas planificaciones, pero se conservaran "
                "sus cuadrantes anteriores."
            )
        )

        if respuesta != QMessageBox.Yes:

            return

        repartidores_service.desactivar(id_repartidor)
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
