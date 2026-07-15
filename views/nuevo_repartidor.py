from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QWidget
)

from PySide6.QtCore import Qt

from database.schema import (
    DIAS_INICIO_DESCANSO,
    DIAS_SEMANA,
    HORAS_CONTRATO,
    OPCIONES_DISPONIBILIDAD
)
from repositories.ciudades_repository import CiudadesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from services.repartidores_service import RepartidoresService
from ui.widgets import create_scroll_area, fit_dialog_to_screen


DESCANSO_NO_NECESARIO_TEXTO = "No necesario por disponibilidad semanal"
ciudades_repository = CiudadesRepository()
repartidores_repository = RepartidoresRepository()
restaurantes_repository = RestaurantesRepository()
repartidores_service = RepartidoresService(repartidores_repository)


class NuevoRepartidor(QDialog):

    def __init__(self, repartidor=None):
        super().__init__()

        self.repartidor = repartidor
        self.setWindowTitle(
            "Editar repartidor"
            if self.repartidor
            else "Nuevo repartidor"
        )
        layout = QVBoxLayout(self)

        contenedor_formulario = QWidget()
        formulario = QFormLayout(contenedor_formulario)

        self.nombre = QLineEdit()

        self.horas = QComboBox()
        self.horas.addItems([
            str(horas)
            for horas in HORAS_CONTRATO
        ])
        self.horas.setCurrentText("30")

        self.ciudad_principal = QComboBox()
        self.restaurante_principal = QComboBox()
        self.ciudades_autorizadas = QListWidget()
        self.ciudades_autorizadas.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        self.ciudades_autorizadas.setMaximumHeight(90)
        self.restaurantes_autorizados = QListWidget()
        self.restaurantes_autorizados.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        self.restaurantes_autorizados.setMaximumHeight(90)
        self.cargar_ubicaciones()

        self.zona = QComboBox()
        self.zona.addItems([
            "Ronda",
            "Grela",
            "Outeiro",
            "Milladoiro"
        ])

        self.descanso_inicio = QComboBox()
        self.descanso_inicio.addItem(DESCANSO_NO_NECESARIO_TEXTO)
        self.descanso_inicio.addItems(DIAS_INICIO_DESCANSO)

        self.descanso_fin = QLineEdit()
        self.descanso_fin.setReadOnly(True)
        self.actualizar_descanso_fin()
        self.dias_no_laborables = QLabel("")
        self.explicacion_descanso = QLabel("")

        self.disponibilidad = {}

        for dia in DIAS_SEMANA:

            selector = QComboBox()
            selector.addItems(OPCIONES_DISPONIBILIDAD)
            selector.setCurrentText("Ambos")

            self.disponibilidad[dia] = selector

        self.doble = QCheckBox()
        self.doble.setChecked(True)

        self.hasta1 = QCheckBox()
        self.hasta1.setChecked(True)

        self.apoyo_flexible = QCheckBox()

        self.permite_horas_complementarias = QCheckBox()
        self.permite_horas_complementarias.stateChanged.connect(
            self.actualizar_estado_horas_complementarias
        )

        self.horas_complementarias = QSpinBox()
        self.horas_complementarias.setRange(0, 40)
        self.horas_complementarias.setEnabled(False)

        self.max_horas_diarias = QSpinBox()
        self.max_horas_diarias.setRange(1, 24)
        self.max_horas_diarias.setValue(10)

        self.max_dias_consecutivos = QSpinBox()
        self.max_dias_consecutivos.setRange(1, 7)
        self.max_dias_consecutivos.setValue(5)

        self.prio_comida = QSpinBox()
        self.prio_comida.setRange(0, 100)
        self.prio_comida.setValue(50)

        self.prio_noche = QSpinBox()
        self.prio_noche.setRange(0, 100)
        self.prio_noche.setValue(50)

        self.prio_grela = QSpinBox()
        self.prio_grela.setRange(0, 100)
        self.prio_grela.setValue(50)

        self.obs = QTextEdit()
        self.obs.setMaximumHeight(90)

        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Horas", self.horas)
        formulario.addRow(
            "Permitir horas complementarias",
            self.permite_horas_complementarias
        )
        formulario.addRow(
            "Limite horas complementarias",
            self.horas_complementarias
        )
        formulario.addRow("Max horas diarias", self.max_horas_diarias)
        formulario.addRow("Max dias consecutivos", self.max_dias_consecutivos)
        formulario.addRow("Ciudad principal", self.ciudad_principal)
        formulario.addRow("Restaurante principal", self.restaurante_principal)
        formulario.addRow("Ciudades autorizadas", self.ciudades_autorizadas)
        formulario.addRow("Restaurantes autorizados", self.restaurantes_autorizados)
        formulario.addRow("Apoyo flexible", self.apoyo_flexible)
        formulario.addRow("Zona", self.zona)
        formulario.addRow("Dias no laborables fijos", self.dias_no_laborables)
        formulario.addRow("Descanso adicional", self.descanso_inicio)
        formulario.addRow("Fin descanso adicional", self.descanso_fin)
        formulario.addRow("", self.explicacion_descanso)

        for dia in DIAS_SEMANA:

            formulario.addRow(
                f"Disponibilidad {dia}",
                self.disponibilidad[dia]
            )

        formulario.addRow("Doble turno", self.doble)
        formulario.addRow("Puede hasta la 1", self.hasta1)
        formulario.addRow("Prioridad comida", self.prio_comida)
        formulario.addRow("Prioridad noche", self.prio_noche)
        formulario.addRow("Prioridad Grela", self.prio_grela)
        formulario.addRow("Observaciones", self.obs)

        layout.addWidget(create_scroll_area(contenedor_formulario), 1)

        self.boton = QPushButton(
            "Guardar"
            if self.repartidor
            else "Crear"
        )
        self.boton.setProperty("variant", "primary")

        layout.addWidget(self.boton)

        self.boton.clicked.connect(self.guardar)
        self.descanso_inicio.currentTextChanged.connect(
            self.actualizar_descanso_fin
        )

        for selector in self.disponibilidad.values():

            selector.currentTextChanged.connect(
                self.actualizar_estado_descanso
            )

        if self.repartidor:

            self.cargar_repartidor()

        else:

            self.actualizar_estado_descanso()

        fit_dialog_to_screen(self, 650, 620, min_width=520, min_height=420)

    def cargar_ubicaciones(self):

        self.ciudad_principal.clear()
        self.ciudad_principal.addItem("Sin ciudad principal", None)
        self.ciudades_autorizadas.clear()

        for ciudad in ciudades_repository.listar_activas():

            self.ciudad_principal.addItem(ciudad[1], ciudad[0])
            item = QListWidgetItem(ciudad[1])
            item.setData(Qt.UserRole, ciudad[0])
            self.ciudades_autorizadas.addItem(item)

        self.restaurante_principal.clear()
        self.restaurante_principal.addItem("Sin restaurante principal", None)
        self.restaurantes_autorizados.clear()

        for restaurante in restaurantes_repository.listar_activos():

            self.restaurante_principal.addItem(restaurante[1], restaurante[0])
            item = QListWidgetItem(restaurante[1])
            item.setData(Qt.UserRole, restaurante[0])
            self.restaurantes_autorizados.addItem(item)

    def actualizar_descanso_fin(self):

        if self.descanso_inicio.currentText() == DESCANSO_NO_NECESARIO_TEXTO:

            self.descanso_fin.setText("")
            return

        self.descanso_fin.setText(
            repartidores_service.siguiente_descanso_valido(
                self.descanso_inicio.currentText()
            )
        )

    def actualizar_estado_descanso(self):

        estado = repartidores_service.estado_descanso_disponibilidad(
            self.obtener_disponibilidad()
        )
        self.dias_no_laborables.setText(
            estado["texto_dias_no_laborables"]
        )

        if estado["descanso_cubierto"]:

            self.descanso_inicio.setCurrentText(
                DESCANSO_NO_NECESARIO_TEXTO
            )

        else:

            if self.descanso_inicio.currentText() == DESCANSO_NO_NECESARIO_TEXTO:

                self.descanso_inicio.setCurrentText("lunes")

        self.explicacion_descanso.setText(estado["explicacion"])

        self.actualizar_descanso_fin()

    def cargar_repartidor(self):

        self.nombre.setText(self.repartidor["nombre"])
        self.horas.setCurrentText(str(self.repartidor["horas"]))
        self.zona.setCurrentText(self.repartidor["zona"] or "")
        self.doble.setChecked(bool(self.repartidor["doble_turno"]))
        self.hasta1.setChecked(bool(self.repartidor["puede_hasta_la_una"]))
        self.prio_comida.setValue(self.repartidor["prioridad_comida"])
        self.prio_noche.setValue(self.repartidor["prioridad_noche"])
        self.prio_grela.setValue(self.repartidor["prioridad_grela"])
        self.obs.setPlainText(self.repartidor["observaciones"])
        self.apoyo_flexible.setChecked(
            bool(self.repartidor.get("apoyo_flexible"))
        )
        self.horas_complementarias.setValue(
            int(self.repartidor.get("horas_complementarias") or 0)
        )
        self.permite_horas_complementarias.setChecked(
            self.horas_complementarias.value() > 0
        )
        self.actualizar_estado_horas_complementarias()
        self.max_horas_diarias.setValue(
            int(self.repartidor.get("max_horas_diarias") or 10)
        )
        self.max_dias_consecutivos.setValue(
            int(self.repartidor.get("max_dias_consecutivos") or 5)
        )
        self.seleccionar_combo(
            self.ciudad_principal,
            self.repartidor.get("ciudad_principal_id")
        )
        self.seleccionar_combo(
            self.restaurante_principal,
            self.repartidor.get("restaurante_principal_id")
        )
        self.seleccionar_lista(
            self.ciudades_autorizadas,
            self.repartidor.get("ciudades_autorizadas", [])
        )
        self.seleccionar_lista(
            self.restaurantes_autorizados,
            self.repartidor.get("restaurantes_autorizados", [])
        )

        for dia, turnos in self.repartidor["disponibilidad"].items():

            if dia not in self.disponibilidad:

                continue

            if "comida" in turnos and "noche" in turnos:

                opcion = "Ambos"

            elif "comida" in turnos:

                opcion = "Comidas"

            elif "noche" in turnos:

                opcion = "Cenas"

            else:

                opcion = "No disponible"

            self.disponibilidad[dia].setCurrentText(opcion)

        self.actualizar_estado_descanso()

        if not repartidores_service.descanso_cubierto_por_disponibilidad(
            self.obtener_disponibilidad()
        ):

            self.descanso_inicio.setCurrentText(
                self.repartidor["descanso_inicio"] or "lunes"
            )
            self.descanso_fin.setText(
                self.repartidor["descanso_fin"]
                or repartidores_service.siguiente_descanso_valido(
                    self.descanso_inicio.currentText()
                )
            )

    def guardar(self):

        if self.nombre.text().strip() == "":

            QMessageBox.warning(
                self,
                "Error",
                "Introduce un nombre."
            )
            return

        try:

            disponibilidad = self.obtener_disponibilidad()
            descanso_inicio = self.descanso_inicio.currentText()
            descanso_fin = self.descanso_fin.text()

            if descanso_inicio == DESCANSO_NO_NECESARIO_TEXTO:

                repartidores_service.validar_descanso_no_necesario(
                    disponibilidad
                )

                descanso_inicio = None
                descanso_fin = None

            funcion = (
                repartidores_repository.actualizar
                if self.repartidor
                else repartidores_repository.crear
            )
            argumentos = []

            if self.repartidor:

                argumentos.append(self.repartidor["id"])

            funcion(

                *argumentos,

                self.nombre.text(),

                int(self.horas.currentText()),

                self.zona.currentText(),

                int(self.doble.isChecked()),

                int(self.hasta1.isChecked()),

                self.prio_comida.value(),

                self.prio_noche.value(),

                self.prio_grela.value(),

                self.obs.toPlainText(),

                descanso_inicio=descanso_inicio,

                descanso_fin=descanso_fin,

                disponibilidad=disponibilidad,
                ciudad_principal_id=self.ciudad_principal.currentData(),
                restaurante_principal_id=(
                    self.restaurante_principal.currentData()
                ),
                apoyo_flexible=int(self.apoyo_flexible.isChecked()),
                horas_complementarias=(
                    self.horas_complementarias.value()
                    if self.permite_horas_complementarias.isChecked()
                    else 0
                ),
                max_horas_diarias=self.max_horas_diarias.value(),
                max_dias_consecutivos=self.max_dias_consecutivos.value(),
                ciudades_autorizadas=self.obtener_ids_seleccionados(
                    self.ciudades_autorizadas
                ),
                restaurantes_autorizados=self.obtener_ids_seleccionados(
                    self.restaurantes_autorizados
                )

            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Error",
                str(error)
            )
            return

        self.accept()

    def actualizar_estado_horas_complementarias(self, *_):

        self.horas_complementarias.setEnabled(
            self.permite_horas_complementarias.isChecked()
        )

    def seleccionar_combo(self, combo, valor):

        indice = combo.findData(valor)

        if indice >= 0:

            combo.setCurrentIndex(indice)

    def seleccionar_lista(self, lista, valores):

        valores = set(valores or [])

        for indice in range(lista.count()):

            item = lista.item(indice)
            item.setSelected(item.data(Qt.UserRole) in valores)

    def obtener_ids_seleccionados(self, lista):

        return [
            item.data(Qt.UserRole)
            for item in lista.selectedItems()
        ]

    def obtener_disponibilidad(self):

        disponibilidad = {}

        for dia, selector in self.disponibilidad.items():

            disponibilidad[dia] = selector.currentText()

        return disponibilidad
