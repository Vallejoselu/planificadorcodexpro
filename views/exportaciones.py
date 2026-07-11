from PySide6.QtWidgets import (
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget
)
from PySide6.QtCore import QDate

from database.database import normalizar_fecha_inicio_semana
from services.exportador import (
    exportar_csv,
    exportar_excel,
    exportar_pdf,
    normalizar_ruta
)


class VistaExportaciones(QWidget):

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)

        titulo = QLabel("Exportar calendario semanal")
        titulo.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.layout.addWidget(titulo)

        barra = QHBoxLayout()

        self.selector_semana = QDateEdit()
        self.selector_semana.setCalendarPopup(True)
        self.selector_semana.setDisplayFormat("yyyy-MM-dd")
        hoy = QDate.currentDate()
        self.selector_semana.setDate(
            hoy.addDays(1 - hoy.dayOfWeek())
        )
        self.btn_excel = QPushButton("Excel")
        self.btn_excel.setProperty("variant", "primary")
        self.btn_pdf = QPushButton("PDF")
        self.btn_csv = QPushButton("CSV")

        barra.addWidget(QLabel("Semana"))
        barra.addWidget(self.selector_semana)
        barra.addWidget(self.btn_excel)
        barra.addWidget(self.btn_pdf)
        barra.addWidget(self.btn_csv)
        barra.addStretch()

        self.layout.addLayout(barra)

        texto = QLabel(
            "Cada exportacion incluye horarios, horas, descansos y totales."
        )
        texto.setStyleSheet("font-size:16px;")

        self.layout.addWidget(texto)
        self.layout.addStretch()

        self.btn_excel.clicked.connect(self.exportar_excel)
        self.btn_pdf.clicked.connect(self.exportar_pdf)
        self.btn_csv.clicked.connect(self.exportar_csv)

    # ======================================

    def exportar_excel(self):

        self.exportar(
            "Excel",
            ".xlsx",
            "Excel (*.xlsx)",
            exportar_excel
        )

    # ======================================

    def exportar_pdf(self):

        self.exportar(
            "PDF",
            ".pdf",
            "PDF (*.pdf)",
            exportar_pdf
        )

    # ======================================

    def exportar_csv(self):

        self.exportar(
            "CSV",
            ".csv",
            "CSV (*.csv)",
            exportar_csv
        )

    # ======================================

    def exportar(self, nombre, extension, filtro, funcion):

        fecha_inicio_semana = normalizar_fecha_inicio_semana(
            self.selector_semana.date().toPython()
        )

        ruta, _ = QFileDialog.getSaveFileName(
            self,
            f"Exportar {nombre}",
            f"calendario_{fecha_inicio_semana}{extension}",
            filtro
        )

        if not ruta:

            return

        ruta = normalizar_ruta(ruta, extension)

        try:

            funcion(ruta, fecha_inicio_semana)

        except Exception as error:

            QMessageBox.critical(
                self,
                "Error",
                str(error)
            )
            return

        QMessageBox.information(
            self,
            "Exportacion completada",
            f"Archivo creado:\n{ruta}"
        )
