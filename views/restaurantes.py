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

from services.restaurantes_service import RestaurantesService
from ui.widgets import configure_table
from views.nuevo_restaurante import NuevoRestaurante

restaurantes_service = RestaurantesService()


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
        self.btn_importar = QPushButton("Importar")
        self.btn_editar = QPushButton("Editar")
        self.btn_eliminar = QPushButton("Desactivar")
        self.btn_eliminar.setProperty("variant", "danger")
        self.btn_eliminar.setToolTip(
            "Desactiva el restaurante para nuevas planificaciones. "
            "No borra cuadrantes anteriores."
        )
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

        self.tabla.setColumnCount(10)

        self.tabla.setHorizontalHeaderLabels([
            "ID",
            "Nombre",
            "Ciudad",
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
        self.btn_importar.clicked.connect(self.importar_restaurantes)
        self.btn_editar.clicked.connect(self.editar_restaurante)
        self.btn_eliminar.clicked.connect(self.eliminar_restaurante)
        self.tabla.doubleClicked.connect(self.editar_restaurante)

        # -------------------------
        # Cargar datos
        # -------------------------

        self.cargar_tabla()

    # ======================================

    def cargar_tabla(self):

        datos = restaurantes_service.listar_tabla()

        self.tabla.setRowCount(len(datos))

        for fila, item_tabla in enumerate(datos):

            r = item_tabla["restaurante"]

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
                QTableWidgetItem(r[10] if len(r) > 10 and r[10] else "")
            )

            self.tabla.setItem(
                fila,
                3,
                QTableWidgetItem(r[3] if r[3] else "")
            )

            self.tabla.setItem(
                fila,
                4,
                QTableWidgetItem(r[2] if r[2] else "")
            )

            self.tabla.setItem(
                fila,
                5,
                QTableWidgetItem(r[4] if r[4] else "")
            )

            self.tabla.setItem(
                fila,
                6,
                QTableWidgetItem("Si" if r[6] else "No")
            )

            self.tabla.setItem(
                fila,
                7,
                QTableWidgetItem(r[7] if r[7] else "")
            )

            self.tabla.setItem(
                fila,
                8,
                QTableWidgetItem(r[8] if r[8] else "")
            )

            self.tabla.setItem(
                fila,
                9,
                QTableWidgetItem(item_tabla["repartidores_fijos_texto"])
            )

    # ======================================

    def restaurante_seleccionado(self):

        fila = self.tabla.currentRow()

        if fila < 0:

            QMessageBox.warning(
                self,
                "Restaurantes",
                "Selecciona un restaurante de la tabla para continuar."
            )
            return None

        return int(self.tabla.item(fila, 0).text())

    # ======================================

    def nuevo_restaurante(self):

        ventana = NuevoRestaurante()

        if ventana.exec():

            self.cargar_tabla()

    # ======================================

    def importar_restaurantes(self):

        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar restaurantes",
            "",
            "Datos (*.csv *.xlsx *.xlsm)"
        )

        if not ruta:

            return

        try:

            resultado = restaurantes_service.importar_desde_archivo(ruta)

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Importar restaurantes",
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
            "Importar restaurantes",
            (
                f"Leidos: {resultado['leidos']}\n"
                f"Creados: {resultado['creados']}\n"
                f"Actualizados: {resultado['actualizados']}\n"
                f"Errores: {errores}"
                f"{detalle_errores}"
            )
        )

    # ======================================

    def editar_restaurante(self):

        id_restaurante = self.restaurante_seleccionado()

        if not id_restaurante:

            return

        restaurante = restaurantes_service.obtener_por_id(id_restaurante)
        repartidores_fijos = (
            restaurantes_service.obtener_repartidores_fijos(id_restaurante)
        )

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
            "Desactivar restaurante",
            (
                "Quieres desactivar el restaurante seleccionado?\n\n"
                "No aparecera en nuevas planificaciones, pero se conservaran "
                "sus datos y cuadrantes anteriores."
            )
        )

        if respuesta == QMessageBox.Yes:

            restaurantes_service.desactivar(id_restaurante)

            self.cargar_tabla()
