from datetime import datetime

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QTextEdit,
    QPushButton,
    QMessageBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QSpinBox
)

from PySide6.QtCore import Qt

from repositories.ciudades_repository import CiudadesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository


ciudades_repository = CiudadesRepository()
repartidores_repository = RepartidoresRepository()
restaurantes_repository = RestaurantesRepository()


class NuevoRestaurante(QDialog):

    def __init__(self, restaurante=None, repartidores_fijos=None):
        super().__init__()

        self.restaurante = restaurante
        self.repartidores_fijos = repartidores_fijos or []
        self.turnos_propios = []
        self.demandas = []

        self.setWindowTitle(
            "Editar restaurante"
            if self.restaurante
            else "Nuevo restaurante"
        )
        self.resize(520, 620)

        layout = QVBoxLayout(self)

        formulario = QFormLayout()

        self.nombre = QLineEdit()
        self.direccion = QLineEdit()

        self.ciudad = QComboBox()
        self.cargar_ciudades()

        self.zona = QComboBox()
        self.zona.addItems([
            "Ronda",
            "Grela",
            "Outeiro",
            "Milladoiro"
        ])

        self.telefono = QLineEdit()

        self.activo = QCheckBox()
        self.activo.setChecked(True)

        self.horario_comida = QLineEdit()
        self.horario_comida.setPlaceholderText("13:00 - 16:00")

        self.horario_cena = QLineEdit()
        self.horario_cena.setPlaceholderText("20:00 - 23:30")

        self.repartidores = QListWidget()
        self.repartidores.setSelectionMode(
            QAbstractItemView.MultiSelection
        )

        self.cargar_repartidores()

        self.obs = QTextEdit()

        self.turno_nombre = QLineEdit()
        self.turno_inicio = QLineEdit()
        self.turno_inicio.setPlaceholderText("13:00")
        self.turno_fin = QLineEdit()
        self.turno_fin.setPlaceholderText("16:00")
        self.turno_cruza = QCheckBox()
        self.turno_duracion = QSpinBox()
        self.turno_duracion.setRange(1, 24)
        self.turno_duracion.setValue(3)
        self.btn_agregar_turno = QPushButton("Agregar turno propio")
        self.tabla_turnos = QTableWidget()
        self.tabla_turnos.setColumnCount(5)
        self.tabla_turnos.setHorizontalHeaderLabels([
            "Nombre",
            "Inicio",
            "Fin",
            "Cruza medianoche",
            "Horas"
        ])

        self.demanda_turno = QComboBox()
        self.demanda_dia = QComboBox()
        self.demanda_dia.addItems([
            "",
            "lunes",
            "martes",
            "miercoles",
            "jueves",
            "viernes",
            "sabado",
            "domingo"
        ])
        self.demanda_fecha = QLineEdit()
        self.demanda_fecha.setPlaceholderText("YYYY-MM-DD")
        self.demanda_repartidores = QSpinBox()
        self.demanda_repartidores.setRange(0, 200)
        self.demanda_repartidores.setValue(1)
        self.btn_agregar_demanda = QPushButton("Agregar demanda")
        self.btn_eliminar_demanda = QPushButton("Eliminar demanda")
        self.tabla_demanda = QTableWidget()
        self.tabla_demanda.setColumnCount(4)
        self.tabla_demanda.setHorizontalHeaderLabels([
            "Turno",
            "Dia",
            "Fecha",
            "Repartidores"
        ])

        formulario.addRow("Nombre", self.nombre)
        formulario.addRow("Ciudad", self.ciudad)
        formulario.addRow("Zona", self.zona)
        formulario.addRow("Direccion", self.direccion)
        formulario.addRow("Telefono", self.telefono)
        formulario.addRow("Activo", self.activo)
        formulario.addRow("Horario comida", self.horario_comida)
        formulario.addRow("Horario cena", self.horario_cena)
        formulario.addRow("Repartidores fijos", self.repartidores)
        formulario.addRow("Turno propio", self.turno_nombre)
        formulario.addRow("Inicio turno", self.turno_inicio)
        formulario.addRow("Fin turno", self.turno_fin)
        formulario.addRow("Cruza medianoche", self.turno_cruza)
        formulario.addRow("Duracion turno", self.turno_duracion)
        formulario.addRow("", self.btn_agregar_turno)
        formulario.addRow("Turnos propios", self.tabla_turnos)
        formulario.addRow("Demanda turno", self.demanda_turno)
        formulario.addRow("Demanda dia", self.demanda_dia)
        formulario.addRow("Demanda fecha", self.demanda_fecha)
        formulario.addRow("Repartidores necesarios", self.demanda_repartidores)
        formulario.addRow("", self.btn_agregar_demanda)
        formulario.addRow("", self.btn_eliminar_demanda)
        formulario.addRow("Demandas", self.tabla_demanda)
        formulario.addRow("Observaciones", self.obs)

        layout.addLayout(formulario)

        self.boton = QPushButton("Guardar")
        self.boton.setProperty("variant", "primary")

        layout.addWidget(self.boton)

        self.boton.clicked.connect(self.guardar)
        self.btn_agregar_turno.clicked.connect(self.agregar_turno)
        self.btn_agregar_demanda.clicked.connect(self.agregar_demanda)
        self.btn_eliminar_demanda.clicked.connect(self.eliminar_demanda)

        if self.restaurante:

            self.cargar_restaurante()
            self.cargar_turnos_demanda()

    def cargar_ciudades(self):

        self.ciudad.clear()

        for ciudad in ciudades_repository.listar_activas():

            self.ciudad.addItem(ciudad[1], ciudad[0])

    def cargar_repartidores(self):

        for repartidor in repartidores_repository.listar_activos():

            item = QListWidgetItem(repartidor[1])
            item.setData(Qt.UserRole, repartidor[0])
            self.repartidores.addItem(item)

            if repartidor[0] in self.repartidores_fijos:

                item.setSelected(True)

    def cargar_restaurante(self):

        self.nombre.setText(self.restaurante[1])
        if len(self.restaurante) > 9 and self.restaurante[9]:

            indice = self.ciudad.findData(self.restaurante[9])

            if indice >= 0:

                self.ciudad.setCurrentIndex(indice)

        self.direccion.setText(
            self.restaurante[2]
            if self.restaurante[2]
            else ""
        )
        self.zona.setCurrentText(
            self.restaurante[3]
            if self.restaurante[3]
            else "Ronda"
        )
        self.telefono.setText(
            self.restaurante[4]
            if self.restaurante[4]
            else ""
        )
        self.activo.setChecked(bool(self.restaurante[6]))
        self.horario_comida.setText(
            self.restaurante[7]
            if self.restaurante[7]
            else ""
        )
        self.horario_cena.setText(
            self.restaurante[8]
            if self.restaurante[8]
            else ""
        )

    def cargar_turnos_demanda(self):

        self.turnos_propios = [
            {
                "id": turno[0],
                "nombre": turno[2],
                "hora_inicio": turno[3],
                "hora_fin": turno[4],
                "cruza_medianoche": turno[5],
                "duracion": turno[6],
                "activo": turno[7]
            }
            for turno in restaurantes_repository.listar_turnos(
                self.restaurante[0]
            )
            if turno[7]
        ]
        self.demandas = [
            {
                "id": demanda[0],
                "turno_restaurante_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            }
            for demanda in restaurantes_repository.listar_demanda(
                self.restaurante[0]
            )
            if demanda[6]
        ]
        self.refrescar_turnos()
        self.refrescar_demanda()

    def agregar_turno(self):

        if not self.turno_nombre.text().strip():

            QMessageBox.warning(
                self,
                "Error",
                "Introduce nombre del turno."
            )
            return

        self.turnos_propios.append({
            "nombre": self.turno_nombre.text().strip(),
            "hora_inicio": self.turno_inicio.text().strip(),
            "hora_fin": self.turno_fin.text().strip(),
            "cruza_medianoche": int(self.turno_cruza.isChecked()),
            "duracion": float(self.turno_duracion.value()),
            "activo": 1
        })
        self.refrescar_turnos()

    def refrescar_turnos(self):

        self.tabla_turnos.setRowCount(len(self.turnos_propios))
        self.demanda_turno.clear()

        for fila, turno in enumerate(self.turnos_propios):

            self.tabla_turnos.setItem(fila, 0, QTableWidgetItem(turno["nombre"]))
            self.tabla_turnos.setItem(fila, 1, QTableWidgetItem(turno["hora_inicio"]))
            self.tabla_turnos.setItem(fila, 2, QTableWidgetItem(turno["hora_fin"]))
            self.tabla_turnos.setItem(
                fila,
                3,
                QTableWidgetItem("Si" if turno.get("cruza_medianoche") else "No")
            )
            self.tabla_turnos.setItem(
                fila,
                4,
                QTableWidgetItem(str(turno["duracion"]))
            )
            self.demanda_turno.addItem(turno["nombre"], fila)

    def agregar_demanda(self):

        if not self.turnos_propios:

            QMessageBox.warning(
                self,
                "Error",
                "Crea primero un turno propio."
            )
            return

        indice_turno = self.demanda_turno.currentData()
        fecha = self.demanda_fecha.text().strip()
        dia_semana = self.demanda_dia.currentText()

        if bool(fecha) == bool(dia_semana):

            QMessageBox.warning(
                self,
                "Demanda",
                "Configura una fecha concreta o un dia de semana, solo uno."
            )
            return

        if fecha:

            try:

                datetime.strptime(fecha, "%Y-%m-%d")

            except ValueError:

                QMessageBox.warning(
                    self,
                    "Demanda",
                    "La fecha debe tener formato YYYY-MM-DD."
                )
                return

        if self.demanda_duplicada(indice_turno, fecha, dia_semana):

            QMessageBox.warning(
                self,
                "Demanda",
                "Ya existe una demanda para ese turno y periodo."
            )
            return

        self.demandas.append({
            "indice_turno": indice_turno,
            "turno_restaurante_id": self.turnos_propios[indice_turno].get("id"),
            "fecha": fecha,
            "dia_semana": dia_semana,
            "repartidores_necesarios": self.demanda_repartidores.value(),
            "activo": 1
        })
        self.refrescar_demanda()

    def demanda_duplicada(self, indice_turno, fecha, dia_semana):

        turno_id = self.turnos_propios[indice_turno].get("id")
        periodo = fecha or dia_semana
        tipo_periodo = "fecha" if fecha else "dia"

        for demanda in self.demandas:

            mismo_turno = (
                demanda.get("turno_restaurante_id") == turno_id
                if turno_id
                else demanda.get("indice_turno") == indice_turno
            )

            if not mismo_turno:

                continue

            if tipo_periodo == "fecha" and demanda.get("fecha") == periodo:

                return True

            if tipo_periodo == "dia" and demanda.get("dia_semana") == periodo:

                return True

        return False

    def eliminar_demanda(self):

        fila = self.tabla_demanda.currentRow()

        if fila < 0 or fila >= len(self.demandas):

            QMessageBox.warning(
                self,
                "Demanda",
                "Selecciona una demanda para eliminarla."
            )
            return

        self.demandas.pop(fila)
        self.refrescar_demanda()

    def refrescar_demanda(self):

        self.tabla_demanda.setRowCount(len(self.demandas))

        for fila, demanda in enumerate(self.demandas):

            turno = self.nombre_turno_demanda(demanda)
            self.tabla_demanda.setItem(fila, 0, QTableWidgetItem(turno))
            self.tabla_demanda.setItem(
                fila,
                1,
                QTableWidgetItem(demanda.get("dia_semana") or "")
            )
            self.tabla_demanda.setItem(
                fila,
                2,
                QTableWidgetItem(demanda.get("fecha") or "")
            )
            self.tabla_demanda.setItem(
                fila,
                3,
                QTableWidgetItem(str(demanda["repartidores_necesarios"]))
            )

    def nombre_turno_demanda(self, demanda):

        turno_id = demanda.get("turno_restaurante_id")

        for indice, turno in enumerate(self.turnos_propios):

            if turno_id and turno.get("id") == turno_id:

                return turno["nombre"]

            if demanda.get("indice_turno") == indice:

                return turno["nombre"]

        return ""

    def obtener_repartidores_fijos(self):

        repartidores = []

        for item in self.repartidores.selectedItems():

            repartidores.append(item.data(Qt.UserRole))

        return repartidores

    def guardar(self):

        if self.nombre.text().strip() == "":

            QMessageBox.warning(
                self,
                "Error",
                "Introduce un nombre."
            )
            return

        if self.restaurante:

            restaurantes_repository.actualizar(
                self.restaurante[0],
                self.nombre.text(),
                self.direccion.text(),
                self.zona.currentText(),
                self.telefono.text(),
                int(self.activo.isChecked()),
                self.horario_comida.text(),
                self.horario_cena.text(),
                self.obtener_repartidores_fijos(),
                self.ciudad.currentData()
            )
            restaurante_id = self.restaurante[0]

        else:

            restaurante_id = restaurantes_repository.crear(

                self.nombre.text(),

                self.direccion.text(),

                self.zona.currentText(),

                self.telefono.text(),

                50,

                self.obs.toPlainText(),

                int(self.activo.isChecked()),

                self.horario_comida.text(),

                self.horario_cena.text(),

                self.obtener_repartidores_fijos(),

                self.ciudad.currentData()

            )

        self.guardar_configuracion_operativa(restaurante_id)
        self.accept()

    def guardar_configuracion_operativa(self, restaurante_id):

        restaurantes_repository.guardar_turnos(
            restaurante_id,
            self.turnos_propios
        )
        turnos_guardados = restaurantes_repository.listar_turnos(
            restaurante_id
        )
        ids_por_nombre = {
            turno[2]: turno[0]
            for turno in turnos_guardados
        }
        demandas = []

        for demanda in self.demandas:

            turno_id = demanda.get("turno_restaurante_id")

            if not turno_id:

                nombre = self.nombre_turno_demanda(demanda)
                turno_id = ids_por_nombre.get(nombre)

            if not turno_id:

                continue

            demandas.append({
                "id": demanda.get("id"),
                "turno_restaurante_id": turno_id,
                "fecha": demanda.get("fecha"),
                "dia_semana": demanda.get("dia_semana"),
                "repartidores_necesarios": demanda["repartidores_necesarios"],
                "activo": demanda.get("activo", 1)
            })

        restaurantes_repository.guardar_demanda(restaurante_id, demandas)
