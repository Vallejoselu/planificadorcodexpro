import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from database.schema import DIAS_SEMANA
from models.integracion import ConfiguracionIntegracion
from repositories.ciudades_repository import CiudadesRepository
from repositories.demandas_ciudad_repository import DemandasCiudadRepository
from repositories.demandas_zona_repository import DemandasZonaRepository
from repositories.integraciones_repository import IntegracionesRepository
from services.sincronizacion import ServicioSincronizacion
from repositories.turnos_repository import TurnosRepository
from services.actualizaciones import ServicioActualizaciones
from services.datos_locales import (
    crear_backup,
    diagnosticar_datos,
    exportar_base,
    importar_base,
    informacion_almacenamiento,
    listar_backups,
    reparar_datos,
    validar_restauracion
)
from services.email_resumen import normalizar_destinatarios
from services.integraciones.registro import guardar_configuracion as guardar_integracion
from ui.theme_manager import ThemeManager
from ui.widgets import PageHeader, configure_table, make_button


ciudades_repository = CiudadesRepository()
demandas_ciudad_repository = DemandasCiudadRepository()
demandas_zona_repository = DemandasZonaRepository()
integraciones_repository = IntegracionesRepository()
sincronizacion_service = ServicioSincronizacion()
turnos_repository = TurnosRepository()


class VistaConfiguracion(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)
        self.ciudades_demanda_ciudad = []
        self.demandas_ciudad = []
        self.demandas_zona = []
        self.turnos_demanda_ciudad = []
        self.turnos_demanda_zona = []

        self.layout.addWidget(
            PageHeader(
                "Configuracion",
                "Tema visual e integraciones preparadas"
            )
        )

        self.panel_tema = QFrame()
        self.panel_tema.setObjectName("card")
        tema_layout = QFormLayout(self.panel_tema)
        tema_layout.setContentsMargins(16, 16, 16, 16)

        self.selector_tema = QComboBox()
        self.selector_tema.addItem("Tema claro", "light")
        self.selector_tema.addItem("Tema oscuro", "dark")
        self.selector_tema.setCurrentIndex(
            self.selector_tema.findData(ThemeManager.current_theme())
        )
        tema_layout.addRow("Tema", self.selector_tema)

        self.layout.addWidget(self.panel_tema)

        self.panel_actualizaciones = QFrame()
        self.panel_actualizaciones.setObjectName("card")
        actualizaciones_layout = QHBoxLayout(self.panel_actualizaciones)
        actualizaciones_layout.setContentsMargins(16, 16, 16, 16)

        self.estado_actualizaciones = QLabel(
            "Actualizaciones preparadas. Servidor pendiente de configurar."
        )
        self.btn_comprobar_actualizaciones = make_button(
            "Comprobar actualizaciones",
            "secondary"
        )

        actualizaciones_layout.addWidget(self.estado_actualizaciones, 1)
        actualizaciones_layout.addWidget(self.btn_comprobar_actualizaciones)

        self.layout.addWidget(self.panel_actualizaciones)

        self.crear_panel_datos_locales()
        self.crear_panel_email()
        self.crear_panel_delivery_generico()
        self.crear_panel_demanda_zona()
        self.crear_panel_demanda_ciudad()

        barra = QHBoxLayout()
        self.btn_actualizar = make_button("Actualizar", "secondary")
        barra.addWidget(self.btn_actualizar)
        barra.addStretch()
        self.layout.addLayout(barra)

        self.tabla_integraciones = QTableWidget()
        self.tabla_eventos = QTableWidget()
        self.tabla_sincronizaciones = QTableWidget()
        configure_table(self.tabla_integraciones)
        configure_table(self.tabla_eventos)
        configure_table(self.tabla_sincronizaciones)

        self.layout.addWidget(QLabel("Integraciones preparadas"))
        self.layout.addWidget(self.tabla_integraciones)
        self.layout.addWidget(QLabel("Sincronizaciones recientes"))
        self.layout.addWidget(self.tabla_sincronizaciones)
        self.layout.addWidget(QLabel("Eventos de integracion"))
        self.layout.addWidget(self.tabla_eventos)

        self.btn_actualizar.clicked.connect(self.cargar_datos)
        self.selector_tema.currentIndexChanged.connect(self.cambiar_tema)
        self.btn_comprobar_actualizaciones.clicked.connect(
            self.comprobar_actualizaciones
        )
        self.btn_backup_datos.clicked.connect(self.crear_backup_datos)
        self.btn_exportar_datos.clicked.connect(self.exportar_datos)
        self.btn_diagnosticar_datos.clicked.connect(self.diagnosticar_datos)
        self.btn_reparar_datos.clicked.connect(self.reparar_datos)
        self.btn_importar_datos.clicked.connect(self.importar_datos)
        self.btn_guardar_email.clicked.connect(
            self.guardar_configuracion_email
        )
        self.btn_guardar_delivery_generico.clicked.connect(
            self.guardar_configuracion_delivery_generico
        )
        self.btn_agregar_demanda_zona.clicked.connect(
            self.agregar_demanda_zona
        )
        self.btn_eliminar_demanda_zona.clicked.connect(
            self.eliminar_demanda_zona
        )
        self.btn_guardar_demanda_zona.clicked.connect(
            self.guardar_demanda_zona
        )
        self.btn_agregar_demanda_ciudad.clicked.connect(
            self.agregar_demanda_ciudad
        )
        self.btn_eliminar_demanda_ciudad.clicked.connect(
            self.eliminar_demanda_ciudad
        )
        self.btn_guardar_demanda_ciudad.clicked.connect(
            self.guardar_demanda_ciudad
        )

        self.cargar_datos()

    # ======================================

    def crear_panel_datos_locales(self):

        self.panel_datos_locales = QFrame()
        self.panel_datos_locales.setObjectName("card")
        layout = QVBoxLayout(self.panel_datos_locales)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Datos locales y copias de seguridad"))

        self.estado_datos_locales = QLabel()
        self.estado_datos_locales.setWordWrap(True)
        layout.addWidget(self.estado_datos_locales)

        acciones = QHBoxLayout()
        self.btn_backup_datos = make_button("Crear backup", "secondary")
        self.btn_exportar_datos = make_button("Exportar datos", "secondary")
        self.btn_diagnosticar_datos = make_button("Diagnosticar", "secondary")
        self.btn_reparar_datos = make_button("Reparar", "secondary")
        self.btn_importar_datos = make_button("Importar o restaurar", "danger")

        acciones.addWidget(self.btn_backup_datos)
        acciones.addWidget(self.btn_exportar_datos)
        acciones.addWidget(self.btn_diagnosticar_datos)
        acciones.addWidget(self.btn_reparar_datos)
        acciones.addWidget(self.btn_importar_datos)
        acciones.addStretch()
        layout.addLayout(acciones)

        self.estado_diagnostico_datos = QLabel("Diagnostico pendiente.")
        self.estado_diagnostico_datos.setWordWrap(True)
        layout.addWidget(self.estado_diagnostico_datos)

        layout.addWidget(QLabel("Backups recientes"))
        self.tabla_backups = QTableWidget()
        configure_table(self.tabla_backups)
        self.tabla_backups.setColumnCount(3)
        self.tabla_backups.setHorizontalHeaderLabels([
            "Archivo",
            "Fecha",
            "Tamano"
        ])
        layout.addWidget(self.tabla_backups)

        self.layout.addWidget(self.panel_datos_locales)

    # ======================================

    def crear_panel_email(self):

        self.panel_email = QFrame()
        self.panel_email.setObjectName("card")
        layout = QVBoxLayout(self.panel_email)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Email"))

        formulario = QFormLayout()
        self.campo_email_host = QLineEdit()
        self.campo_email_host.setPlaceholderText("smtp.ejemplo.com")
        self.campo_email_puerto = QSpinBox()
        self.campo_email_puerto.setRange(1, 65535)
        self.campo_email_puerto.setValue(587)
        self.selector_email_tls = QComboBox()
        self.selector_email_tls.addItem("TLS activado", True)
        self.selector_email_tls.addItem("TLS desactivado", False)
        self.campo_email_remitente = QLineEdit()
        self.campo_email_remitente.setPlaceholderText("planificador@empresa.com")
        self.campo_email_destinatarios = QLineEdit()
        self.campo_email_destinatarios.setPlaceholderText(
            "responsable@empresa.com; tienda@empresa.com"
        )
        self.campo_email_credenciales = QLineEdit()
        self.campo_email_credenciales.setPlaceholderText(
            "env:SMTP_PASSWORD o local://email/principal"
        )

        formulario.addRow("Servidor SMTP", self.campo_email_host)
        formulario.addRow("Puerto", self.campo_email_puerto)
        formulario.addRow("Seguridad", self.selector_email_tls)
        formulario.addRow("Remitente", self.campo_email_remitente)
        formulario.addRow("Destinatarios", self.campo_email_destinatarios)
        formulario.addRow("Credenciales", self.campo_email_credenciales)
        layout.addLayout(formulario)

        acciones = QHBoxLayout()
        self.btn_guardar_email = make_button(
            "Guardar configuracion de email",
            "primary"
        )
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar_email)
        layout.addLayout(acciones)

        self.layout.addWidget(self.panel_email)

    # ======================================

    def crear_panel_delivery_generico(self):

        self.panel_delivery_generico = QFrame()
        self.panel_delivery_generico.setObjectName("card")
        layout = QVBoxLayout(self.panel_delivery_generico)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Delivery generico"))

        formulario = QFormLayout()
        self.campo_delivery_webhook = QLineEdit()
        self.campo_delivery_webhook.setPlaceholderText(
            "https://proveedor.example/webhook"
        )
        self.selector_delivery_modo = QComboBox()
        self.selector_delivery_modo.addItem("Simulado, no enviar", True)
        self.selector_delivery_modo.addItem("Preparado para envio futuro", False)
        self.campo_delivery_credenciales = QLineEdit()
        self.campo_delivery_credenciales.setPlaceholderText(
            "Opcional: env:VARIABLE o local://api_generica/principal"
        )

        formulario.addRow("Webhook", self.campo_delivery_webhook)
        formulario.addRow("Modo", self.selector_delivery_modo)
        formulario.addRow("Credenciales", self.campo_delivery_credenciales)
        layout.addLayout(formulario)

        acciones = QHBoxLayout()
        self.btn_guardar_delivery_generico = make_button(
            "Guardar webhook generico",
            "primary"
        )
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar_delivery_generico)
        layout.addLayout(acciones)

        self.layout.addWidget(self.panel_delivery_generico)

    # ======================================

    def crear_panel_demanda_zona(self):

        self.panel_demanda_zona = QFrame()
        self.panel_demanda_zona.setObjectName("card")
        layout = QVBoxLayout(self.panel_demanda_zona)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Demanda por zona y turno"))

        formulario = QHBoxLayout()

        self.selector_zona_demanda = QComboBox()
        self.selector_zona_demanda.setEditable(True)

        self.selector_turno_demanda = QComboBox()

        self.selector_dia_demanda = QComboBox()
        self.selector_dia_demanda.addItem("", "")

        for dia in DIAS_SEMANA:

            self.selector_dia_demanda.addItem(dia, dia)

        self.campo_fecha_demanda = QLineEdit()
        self.campo_fecha_demanda.setPlaceholderText("YYYY-MM-DD")

        self.campo_repartidores_demanda = QSpinBox()
        self.campo_repartidores_demanda.setRange(0, 200)
        self.campo_repartidores_demanda.setValue(1)

        formulario.addWidget(QLabel("Zona"))
        formulario.addWidget(self.selector_zona_demanda)
        formulario.addWidget(QLabel("Turno"))
        formulario.addWidget(self.selector_turno_demanda)
        formulario.addWidget(QLabel("Dia"))
        formulario.addWidget(self.selector_dia_demanda)
        formulario.addWidget(QLabel("Fecha"))
        formulario.addWidget(self.campo_fecha_demanda)
        formulario.addWidget(QLabel("Repartidores"))
        formulario.addWidget(self.campo_repartidores_demanda)

        layout.addLayout(formulario)

        acciones = QHBoxLayout()
        self.btn_agregar_demanda_zona = make_button(
            "Agregar demanda",
            "secondary"
        )
        self.btn_eliminar_demanda_zona = make_button(
            "Eliminar demanda",
            "secondary"
        )
        self.btn_guardar_demanda_zona = make_button(
            "Guardar demanda por zona",
            "primary"
        )
        acciones.addWidget(self.btn_agregar_demanda_zona)
        acciones.addWidget(self.btn_eliminar_demanda_zona)
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar_demanda_zona)
        layout.addLayout(acciones)

        self.tabla_demanda_zona = QTableWidget()
        configure_table(self.tabla_demanda_zona)
        layout.addWidget(self.tabla_demanda_zona)

        self.layout.addWidget(self.panel_demanda_zona)

    # ======================================

    def crear_panel_demanda_ciudad(self):

        self.panel_demanda_ciudad = QFrame()
        self.panel_demanda_ciudad.setObjectName("card")
        layout = QVBoxLayout(self.panel_demanda_ciudad)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Demanda por ciudad y turno"))

        formulario = QHBoxLayout()

        self.selector_ciudad_demanda = QComboBox()
        self.selector_turno_demanda_ciudad = QComboBox()

        self.selector_dia_demanda_ciudad = QComboBox()
        self.selector_dia_demanda_ciudad.addItem("", "")

        for dia in DIAS_SEMANA:

            self.selector_dia_demanda_ciudad.addItem(dia, dia)

        self.campo_fecha_demanda_ciudad = QLineEdit()
        self.campo_fecha_demanda_ciudad.setPlaceholderText("YYYY-MM-DD")

        self.campo_repartidores_demanda_ciudad = QSpinBox()
        self.campo_repartidores_demanda_ciudad.setRange(0, 200)
        self.campo_repartidores_demanda_ciudad.setValue(1)

        formulario.addWidget(QLabel("Ciudad"))
        formulario.addWidget(self.selector_ciudad_demanda)
        formulario.addWidget(QLabel("Turno"))
        formulario.addWidget(self.selector_turno_demanda_ciudad)
        formulario.addWidget(QLabel("Dia"))
        formulario.addWidget(self.selector_dia_demanda_ciudad)
        formulario.addWidget(QLabel("Fecha"))
        formulario.addWidget(self.campo_fecha_demanda_ciudad)
        formulario.addWidget(QLabel("Repartidores"))
        formulario.addWidget(self.campo_repartidores_demanda_ciudad)

        layout.addLayout(formulario)

        acciones = QHBoxLayout()
        self.btn_agregar_demanda_ciudad = make_button(
            "Agregar demanda",
            "secondary"
        )
        self.btn_eliminar_demanda_ciudad = make_button(
            "Eliminar demanda",
            "secondary"
        )
        self.btn_guardar_demanda_ciudad = make_button(
            "Guardar demanda por ciudad",
            "primary"
        )
        acciones.addWidget(self.btn_agregar_demanda_ciudad)
        acciones.addWidget(self.btn_eliminar_demanda_ciudad)
        acciones.addStretch()
        acciones.addWidget(self.btn_guardar_demanda_ciudad)
        layout.addLayout(acciones)

        self.tabla_demanda_ciudad = QTableWidget()
        configure_table(self.tabla_demanda_ciudad)
        layout.addWidget(self.tabla_demanda_ciudad)

        self.layout.addWidget(self.panel_demanda_ciudad)

    # ======================================

    def cargar_datos(self):

        self.cargar_estado_datos_locales()
        self.cargar_configuracion_email()
        self.cargar_configuracion_delivery_generico()
        self.cargar_demanda_zona()
        self.cargar_demanda_ciudad()
        self.cargar_integraciones()
        self.cargar_sincronizaciones()
        self.cargar_eventos()

    # ======================================

    def cargar_estado_datos_locales(self):

        info = informacion_almacenamiento()
        tamano_mb = info["tamano_bytes"] / (1024 * 1024)
        texto = (
            f"Base de datos: {info['ruta_bd']}\n"
            f"Carpeta de backups: {info['carpeta_backups']}\n"
            f"Estado: {'existe' if info['existe'] else 'pendiente de crear'} "
            f"({tamano_mb:.2f} MB)"
        )
        self.estado_datos_locales.setText(texto)
        self.cargar_backups_recientes()

    # ======================================

    def cargar_backups_recientes(self):

        backups = listar_backups(limite=5)
        self.tabla_backups.setRowCount(len(backups))

        for fila, backup in enumerate(backups):

            valores = [
                backup["nombre"],
                backup["modificado"].strftime("%Y-%m-%d %H:%M"),
                f"{backup['tamano_bytes'] / (1024 * 1024):.2f} MB"
            ]

            for columna, valor in enumerate(valores):

                item = QTableWidgetItem(str(valor))
                item.setToolTip(str(backup["ruta"]))
                self.tabla_backups.setItem(fila, columna, item)

        self.tabla_backups.resizeColumnsToContents()

    # ======================================

    def diagnosticar_datos(self):

        try:

            diagnostico = diagnosticar_datos()

        except ValueError as error:

            QMessageBox.warning(self, "Diagnostico de datos", str(error))
            return

        self.estado_diagnostico_datos.setText(
            self.texto_diagnostico_datos(diagnostico)
        )
        QMessageBox.information(
            self,
            "Diagnostico de datos",
            self.texto_diagnostico_datos(diagnostico)
        )

    # ======================================

    def reparar_datos(self):

        respuesta = QMessageBox.question(
            self,
            "Reparar datos",
            "Se creara un backup automatico y se aplicaran reparaciones "
            "seguras sobre la base local. Quieres continuar?"
        )

        if respuesta != QMessageBox.Yes:

            return

        try:

            diagnostico = reparar_datos()

        except ValueError as error:

            QMessageBox.warning(self, "Reparar datos", str(error))
            return

        self.cargar_datos()
        mensaje = self.texto_diagnostico_datos(diagnostico)

        if diagnostico.get("respaldo"):

            mensaje += f"\n\nBackup previo:\n{diagnostico['respaldo']}"

        QMessageBox.information(self, "Reparar datos", mensaje)

    # ======================================

    def texto_diagnostico_datos(self, diagnostico):

        secciones = [diagnostico.get("resumen", "Diagnostico completado.")]

        if diagnostico.get("errores"):

            secciones.append("Errores:\n- " + "\n- ".join(diagnostico["errores"]))

        if diagnostico.get("advertencias"):

            secciones.append(
                "Advertencias:\n- " + "\n- ".join(diagnostico["advertencias"])
            )

        if diagnostico.get("acciones"):

            secciones.append(
                "Acciones:\n- " + "\n- ".join(diagnostico["acciones"])
            )

        if diagnostico.get("info"):

            secciones.append("Info:\n- " + "\n- ".join(diagnostico["info"]))

        return "\n\n".join(secciones)

    # ======================================

    def crear_backup_datos(self):

        try:

            ruta = crear_backup()

        except ValueError as error:

            QMessageBox.warning(self, "Backup", str(error))
            return

        self.cargar_estado_datos_locales()
        QMessageBox.information(
            self,
            "Backup",
            f"Copia creada correctamente:\n{ruta}"
        )
        self.cargar_backups_recientes()

    # ======================================

    def exportar_datos(self):

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Exportar datos",
            "delivery-export.db",
            "Base SQLite (*.db);;Todos los archivos (*)"
        )

        if not ruta:

            return

        try:

            destino = exportar_base(ruta)

        except ValueError as error:

            QMessageBox.warning(self, "Exportar datos", str(error))
            return

        QMessageBox.information(
            self,
            "Exportar datos",
            f"Datos exportados correctamente:\n{destino}"
        )

    # ======================================

    def importar_datos(self):

        ruta, _ = QFileDialog.getOpenFileName(
            self,
            "Importar o restaurar datos",
            "",
            "Base SQLite (*.db);;Todos los archivos (*)"
        )

        if not ruta:

            return

        try:

            validacion = validar_restauracion(ruta)

        except ValueError as error:

            QMessageBox.warning(self, "Importar o restaurar", str(error))
            return

        respuesta = QMessageBox.question(
            self,
            "Importar o restaurar",
            "Se reemplazara la base de datos local actual. "
            "Antes se creara una copia de seguridad automatica. "
            f"Validacion: {validacion['resumen']} "
            "Quieres continuar?"
        )

        if respuesta != QMessageBox.Yes:

            return

        try:

            resultado = importar_base(ruta)

        except ValueError as error:

            QMessageBox.warning(self, "Importar o restaurar", str(error))
            return

        self.cargar_datos()
        mensaje = (
            f"Datos restaurados desde:\n{resultado['origen']}\n\n"
            f"Base activa:\n{resultado['ruta_bd']}"
        )

        if resultado.get("respaldo"):

            mensaje += f"\n\nBackup previo:\n{resultado['respaldo']}"

        QMessageBox.information(self, "Importar o restaurar", mensaje)

    # ======================================

    def cambiar_tema(self):

        ThemeManager.set_theme(self.selector_tema.currentData())

    # ======================================

    def comprobar_actualizaciones(self):

        servicio = ServicioActualizaciones()
        resultado = servicio.comprobar()
        mensaje = servicio.mensaje_para_usuario(resultado)
        self.estado_actualizaciones.setText(mensaje)

        if resultado.correcto:

            QMessageBox.information(
                self,
                "Actualizaciones",
                mensaje
            )

        else:

            QMessageBox.warning(
                self,
                "Actualizaciones",
                mensaje
            )

    # ======================================

    def cargar_configuracion_email(self):

        datos = integraciones_repository.obtener_configuracion("email")

        if not datos:

            self.campo_email_host.clear()
            self.campo_email_puerto.setValue(587)
            self.selector_email_tls.setCurrentIndex(0)
            self.campo_email_remitente.clear()
            self.campo_email_destinatarios.clear()
            self.campo_email_credenciales.clear()
            return

        opciones = self.decodificar_opciones_integracion(datos[5])
        self.campo_email_host.setText(opciones.get("smtp_host") or datos[3] or "")
        self.campo_email_puerto.setValue(int(opciones.get("smtp_puerto") or 587))
        indice_tls = self.selector_email_tls.findData(
            bool(opciones.get("smtp_tls", True))
        )
        self.selector_email_tls.setCurrentIndex(max(0, indice_tls))
        self.campo_email_remitente.setText(opciones.get("remitente", ""))
        self.campo_email_destinatarios.setText(
            opciones.get("destinatarios", "")
        )
        self.campo_email_credenciales.setText(datos[4] or "")

    # ======================================

    def guardar_configuracion_email(self):

        opciones = {
            "smtp_host": self.campo_email_host.text().strip(),
            "smtp_puerto": self.campo_email_puerto.value(),
            "smtp_tls": bool(self.selector_email_tls.currentData()),
            "remitente": self.campo_email_remitente.text().strip(),
            "destinatarios": self.campo_email_destinatarios.text().strip()
        }

        try:

            if opciones["destinatarios"]:

                normalizar_destinatarios(opciones["destinatarios"])

            guardar_integracion(
                ConfiguracionIntegracion(
                    proveedor="email",
                    nombre="Email",
                    activo=bool(
                        opciones["smtp_host"]
                        and opciones["remitente"]
                        and self.campo_email_credenciales.text().strip()
                    ),
                    base_url=opciones["smtp_host"],
                    credenciales_referencia=(
                        self.campo_email_credenciales.text().strip()
                    ),
                    opciones=opciones
                )
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Email",
                str(error)
            )
            return

        self.cargar_integraciones()
        QMessageBox.information(
            self,
            "Email",
            "Configuracion de email guardada."
        )

    # ======================================

    def cargar_configuracion_delivery_generico(self):

        datos = integraciones_repository.obtener_configuracion("api_generica")

        if not datos:

            self.campo_delivery_webhook.clear()
            self.selector_delivery_modo.setCurrentIndex(0)
            self.campo_delivery_credenciales.clear()
            return

        opciones = self.decodificar_opciones_integracion(datos[5])
        self.campo_delivery_webhook.setText(
            opciones.get("webhook_url") or datos[3] or ""
        )
        indice_modo = self.selector_delivery_modo.findData(
            bool(opciones.get("simulado", True))
        )
        self.selector_delivery_modo.setCurrentIndex(max(0, indice_modo))
        self.campo_delivery_credenciales.setText(datos[4] or "")

    # ======================================

    def guardar_configuracion_delivery_generico(self):

        webhook_url = self.campo_delivery_webhook.text().strip()
        credenciales = self.campo_delivery_credenciales.text().strip()
        opciones = {
            "webhook_url": webhook_url,
            "simulado": bool(self.selector_delivery_modo.currentData()),
            "schema": "planificador.delivery.v1"
        }

        try:

            self.validar_url_webhook(webhook_url)
            guardar_integracion(
                ConfiguracionIntegracion(
                    proveedor="api_generica",
                    nombre="API generica",
                    activo=bool(webhook_url),
                    base_url=webhook_url,
                    credenciales_referencia=credenciales,
                    opciones=opciones
                )
            )

        except ValueError as error:

            QMessageBox.warning(
                self,
                "Delivery generico",
                str(error)
            )
            return

        self.cargar_integraciones()
        QMessageBox.information(
            self,
            "Delivery generico",
            "Webhook generico guardado."
        )

    # ======================================

    def validar_url_webhook(self, url):

        if not url:

            return

        if not (
            url.startswith("https://")
            or url.startswith("http://")
        ):

            raise ValueError(
                "El webhook generico debe empezar por http:// o https://."
            )

    # ======================================

    def decodificar_opciones_integracion(self, opciones):

        if not opciones:

            return {}

        try:

            return json.loads(opciones)

        except json.JSONDecodeError:

            return {}

    # ======================================

    def cargar_demanda_zona(self):

        self.turnos_demanda_zona = turnos_repository.listar_activos()
        self.demandas_zona = [
            {
                "id": demanda[0],
                "zona": demanda[1],
                "turno_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            }
            for demanda in demandas_zona_repository.listar()
            if demanda[6]
        ]

        zonas = set(demandas_zona_repository.listar_zonas())
        zonas.update(demanda["zona"] for demanda in self.demandas_zona)

        texto_actual = self.selector_zona_demanda.currentText()
        self.selector_zona_demanda.clear()

        for zona in sorted(zonas):

            self.selector_zona_demanda.addItem(zona, zona)

        if texto_actual:

            self.selector_zona_demanda.setCurrentText(texto_actual)

        turno_actual = self.selector_turno_demanda.currentData()
        self.selector_turno_demanda.clear()

        for turno in self.turnos_demanda_zona:

            self.selector_turno_demanda.addItem(turno[2], turno[0])

        indice_turno = self.selector_turno_demanda.findData(turno_actual)

        if indice_turno >= 0:

            self.selector_turno_demanda.setCurrentIndex(indice_turno)

        self.refrescar_tabla_demanda_zona()

    # ======================================

    def agregar_demanda_zona(self):

        zona = self.selector_zona_demanda.currentText().strip()
        turno_id = self.selector_turno_demanda.currentData()
        dia_semana = self.selector_dia_demanda.currentData() or None
        fecha = self.campo_fecha_demanda.text().strip() or None

        if not zona:

            QMessageBox.warning(self, "Demanda por zona", "Introduce una zona.")
            return

        if not turno_id:

            QMessageBox.warning(self, "Demanda por zona", "Selecciona un turno.")
            return

        if bool(fecha) == bool(dia_semana):

            QMessageBox.warning(
                self,
                "Demanda por zona",
                "Configura una fecha concreta o un dia de semana, solo uno."
            )
            return

        clave = (
            zona.casefold(),
            int(turno_id),
            "fecha" if fecha else "dia",
            fecha or dia_semana
        )

        for demanda in self.demandas_zona:

            clave_existente = (
                demanda["zona"].casefold(),
                int(demanda["turno_id"]),
                "fecha" if demanda.get("fecha") else "dia",
                demanda.get("fecha") or demanda.get("dia_semana")
            )

            if clave == clave_existente:

                QMessageBox.warning(
                    self,
                    "Demanda por zona",
                    "Ya existe demanda para esa zona, turno y periodo."
                )
                return

        self.demandas_zona.append({
            "zona": zona,
            "turno_id": int(turno_id),
            "fecha": fecha,
            "dia_semana": dia_semana,
            "repartidores_necesarios": self.campo_repartidores_demanda.value(),
            "activo": 1
        })
        self.refrescar_tabla_demanda_zona()

    # ======================================

    def eliminar_demanda_zona(self):

        fila = self.tabla_demanda_zona.currentRow()

        if fila < 0 or fila >= len(self.demandas_zona):

            QMessageBox.warning(
                self,
                "Demanda por zona",
                "Selecciona una demanda."
            )
            return

        del self.demandas_zona[fila]
        self.refrescar_tabla_demanda_zona()

    # ======================================

    def guardar_demanda_zona(self):

        try:

            demandas_zona_repository.guardar(self.demandas_zona)

        except ValueError as error:

            QMessageBox.warning(self, "Demanda por zona", str(error))
            return

        self.cargar_demanda_zona()
        QMessageBox.information(
            self,
            "Demanda por zona",
            "Demanda por zona guardada."
        )

    # ======================================

    def refrescar_tabla_demanda_zona(self):

        nombres_turno = {
            turno[0]: turno[2]
            for turno in self.turnos_demanda_zona
        }

        self.tabla_demanda_zona.setColumnCount(5)
        self.tabla_demanda_zona.setHorizontalHeaderLabels([
            "Zona",
            "Turno",
            "Dia",
            "Fecha",
            "Repartidores"
        ])
        self.tabla_demanda_zona.setRowCount(len(self.demandas_zona))

        for fila, demanda in enumerate(self.demandas_zona):

            valores = [
                demanda["zona"],
                nombres_turno.get(demanda["turno_id"], demanda["turno_id"]),
                demanda.get("dia_semana") or "",
                demanda.get("fecha") or "",
                demanda["repartidores_necesarios"]
            ]
            self.pintar_fila(self.tabla_demanda_zona, fila, valores)

        self.tabla_demanda_zona.resizeColumnsToContents()

    # ======================================

    def cargar_demanda_ciudad(self):

        self.ciudades_demanda_ciudad = ciudades_repository.listar_activas()
        self.turnos_demanda_ciudad = turnos_repository.listar_activos()
        self.demandas_ciudad = [
            {
                "id": demanda[0],
                "ciudad_id": demanda[1],
                "ciudad": demanda[2],
                "turno_id": demanda[3],
                "fecha": demanda[4],
                "dia_semana": demanda[5],
                "repartidores_necesarios": demanda[6],
                "activo": demanda[7]
            }
            for demanda in demandas_ciudad_repository.listar()
            if demanda[7]
        ]

        ciudad_actual = self.selector_ciudad_demanda.currentData()
        self.selector_ciudad_demanda.clear()

        for ciudad in self.ciudades_demanda_ciudad:

            self.selector_ciudad_demanda.addItem(ciudad[1], ciudad[0])

        indice_ciudad = self.selector_ciudad_demanda.findData(ciudad_actual)

        if indice_ciudad >= 0:

            self.selector_ciudad_demanda.setCurrentIndex(indice_ciudad)

        turno_actual = self.selector_turno_demanda_ciudad.currentData()
        self.selector_turno_demanda_ciudad.clear()

        for turno in self.turnos_demanda_ciudad:

            self.selector_turno_demanda_ciudad.addItem(turno[2], turno[0])

        indice_turno = self.selector_turno_demanda_ciudad.findData(
            turno_actual
        )

        if indice_turno >= 0:

            self.selector_turno_demanda_ciudad.setCurrentIndex(indice_turno)

        self.refrescar_tabla_demanda_ciudad()

    # ======================================

    def agregar_demanda_ciudad(self):

        ciudad_id = self.selector_ciudad_demanda.currentData()
        ciudad = self.selector_ciudad_demanda.currentText()
        turno_id = self.selector_turno_demanda_ciudad.currentData()
        dia_semana = self.selector_dia_demanda_ciudad.currentData() or None
        fecha = self.campo_fecha_demanda_ciudad.text().strip() or None

        if not ciudad_id:

            QMessageBox.warning(
                self,
                "Demanda por ciudad",
                "Selecciona una ciudad."
            )
            return

        if not turno_id:

            QMessageBox.warning(
                self,
                "Demanda por ciudad",
                "Selecciona un turno."
            )
            return

        if bool(fecha) == bool(dia_semana):

            QMessageBox.warning(
                self,
                "Demanda por ciudad",
                "Configura una fecha concreta o un dia de semana, solo uno."
            )
            return

        clave = (
            int(ciudad_id),
            int(turno_id),
            "fecha" if fecha else "dia",
            fecha or dia_semana
        )

        for demanda in self.demandas_ciudad:

            clave_existente = (
                int(demanda["ciudad_id"]),
                int(demanda["turno_id"]),
                "fecha" if demanda.get("fecha") else "dia",
                demanda.get("fecha") or demanda.get("dia_semana")
            )

            if clave == clave_existente:

                QMessageBox.warning(
                    self,
                    "Demanda por ciudad",
                    "Ya existe demanda para esa ciudad, turno y periodo."
                )
                return

        self.demandas_ciudad.append({
            "ciudad_id": int(ciudad_id),
            "ciudad": ciudad,
            "turno_id": int(turno_id),
            "fecha": fecha,
            "dia_semana": dia_semana,
            "repartidores_necesarios": (
                self.campo_repartidores_demanda_ciudad.value()
            ),
            "activo": 1
        })
        self.refrescar_tabla_demanda_ciudad()

    # ======================================

    def eliminar_demanda_ciudad(self):

        fila = self.tabla_demanda_ciudad.currentRow()

        if fila < 0 or fila >= len(self.demandas_ciudad):

            QMessageBox.warning(
                self,
                "Demanda por ciudad",
                "Selecciona una demanda."
            )
            return

        del self.demandas_ciudad[fila]
        self.refrescar_tabla_demanda_ciudad()

    # ======================================

    def guardar_demanda_ciudad(self):

        try:

            demandas_ciudad_repository.guardar(self.demandas_ciudad)

        except ValueError as error:

            QMessageBox.warning(self, "Demanda por ciudad", str(error))
            return

        self.cargar_demanda_ciudad()
        QMessageBox.information(
            self,
            "Demanda por ciudad",
            "Demanda por ciudad guardada."
        )

    # ======================================

    def refrescar_tabla_demanda_ciudad(self):

        nombres_turno = {
            turno[0]: turno[2]
            for turno in self.turnos_demanda_ciudad
        }

        self.tabla_demanda_ciudad.setColumnCount(5)
        self.tabla_demanda_ciudad.setHorizontalHeaderLabels([
            "Ciudad",
            "Turno",
            "Dia",
            "Fecha",
            "Repartidores"
        ])
        self.tabla_demanda_ciudad.setRowCount(len(self.demandas_ciudad))

        for fila, demanda in enumerate(self.demandas_ciudad):

            valores = [
                demanda.get("ciudad", demanda["ciudad_id"]),
                nombres_turno.get(demanda["turno_id"], demanda["turno_id"]),
                demanda.get("dia_semana") or "",
                demanda.get("fecha") or "",
                demanda["repartidores_necesarios"]
            ]
            self.pintar_fila(self.tabla_demanda_ciudad, fila, valores)

        self.tabla_demanda_ciudad.resizeColumnsToContents()

    # ======================================

    def cargar_integraciones(self):

        datos = integraciones_repository.listar_configuraciones()

        self.tabla_integraciones.setColumnCount(7)
        self.tabla_integraciones.setHorizontalHeaderLabels([
            "Proveedor",
            "Nombre",
            "Activo",
            "Base URL",
            "Credenciales",
            "Opciones",
            "Actualizado"
        ])
        self.tabla_integraciones.setRowCount(len(datos))

        for fila, integracion in enumerate(datos):

            valores = [
                integracion[0],
                integracion[1],
                "Si" if integracion[2] else "No",
                integracion[3] or "",
                integracion[4] or "",
                integracion[5] or "",
                integracion[6] or ""
            ]

            self.pintar_fila(self.tabla_integraciones, fila, valores)

        self.tabla_integraciones.resizeColumnsToContents()

    # ======================================

    def cargar_eventos(self):

        datos = integraciones_repository.listar_eventos()

        self.tabla_eventos.setColumnCount(5)
        self.tabla_eventos.setHorizontalHeaderLabels([
            "Proveedor",
            "Tipo",
            "Estado",
            "Mensaje",
            "Fecha"
        ])
        self.tabla_eventos.setRowCount(len(datos))

        for fila, evento in enumerate(datos):

            self.pintar_fila(self.tabla_eventos, fila, evento)

        self.tabla_eventos.resizeColumnsToContents()

    # ======================================

    def cargar_sincronizaciones(self):

        datos = sincronizacion_service.listar(limite=50)

        self.tabla_sincronizaciones.setColumnCount(8)
        self.tabla_sincronizaciones.setHorizontalHeaderLabels([
            "Proveedor",
            "Accion",
            "Estado",
            "Intentos",
            "Max",
            "Proximo intento",
            "Error",
            "Actualizado"
        ])
        self.tabla_sincronizaciones.setRowCount(len(datos))

        for fila, sincronizacion in enumerate(datos):

            valores = [
                sincronizacion[1],
                sincronizacion[2],
                sincronizacion[3],
                sincronizacion[7],
                sincronizacion[8],
                sincronizacion[9] or "",
                sincronizacion[6] or "",
                sincronizacion[11] or ""
            ]

            self.pintar_fila(self.tabla_sincronizaciones, fila, valores)

        self.tabla_sincronizaciones.resizeColumnsToContents()

    # ======================================

    def pintar_fila(self, tabla, fila, valores):

        for columna, valor in enumerate(valores):

            item = QTableWidgetItem(str(valor))
            item.setTextAlignment(Qt.AlignCenter)
            tabla.setItem(fila, columna, item)
