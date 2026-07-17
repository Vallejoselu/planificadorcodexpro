from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget
)

from ui.widgets import PageHeader, create_scroll_area


class VistaGuiaUso(QWidget):

    SECCIONES = (
        (
            "1. Idea general",
            (
                "La aplicacion sirve para preparar una empresa de reparto, "
                "crear repartidores, restaurantes, turnos y demanda, y despues "
                "generar un cuadrante semanal. La app no adivina la empresa: "
                "primero necesita datos claros."
            )
        ),
        (
            "2. Orden recomendado",
            (
                "Empieza por Puesta en marcha. Despues crea ciudades, "
                "restaurantes, turnos, repartidores y demanda. Cuando todo "
                "este correcto, entra en Cuadrantes y pulsa Comprobar "
                "configuracion antes de Generar cuadrante."
            )
        ),
        (
            "3. Empezar de cero",
            (
                "Si hay datos de pruebas o repartidores que no quieres usar, "
                "ve a Puesta en marcha y pulsa Empezar de cero. La app crea "
                "un backup automatico y deja limpios los datos operativos sin "
                "romper la estructura de la base de datos."
            )
        ),
        (
            "4. Repartidores",
            (
                "Aqui defines personas, horas contratadas, disponibilidad, "
                "descansos, ciudad principal, restaurante principal, "
                "restaurantes autorizados y apoyo flexible. Si un repartidor "
                "no esta disponible un dia, no debe asignarse ese dia."
            )
        ),
        (
            "5. Restaurantes y ciudades",
            (
                "Cada restaurante pertenece a una ciudad. Puede tener turnos "
                "propios y demanda propia. La zona se conserva como dato util "
                "para agrupar locales o aplicar preferencias."
            )
        ),
        (
            "6. Turnos",
            (
                "Los turnos globales son turnos generales de la aplicacion. "
                "Los turnos propios de restaurante permiten que cada local "
                "tenga horarios distintos. Para planificacion real, revisa "
                "los turnos propios del restaurante."
            )
        ),
        (
            "7. Demanda",
            (
                "La demanda indica cuantos repartidores hacen falta. La "
                "prioridad es: restaurante, zona, ciudad y defecto. Si una "
                "demanda pide 3 personas, el cuadrante crea 3 plazas. Si no "
                "hay suficientes candidatos, aparecen alertas."
            )
        ),
        (
            "8. Cuadrantes",
            (
                "La vista Semana muestra dias y turnos. La vista Por local "
                "agrupa por restaurante. La vista Por empleado es la mas "
                "parecida a una hoja semanal: cada fila es un repartidor y "
                "cada columna un dia."
            )
        ),
        (
            "9. Colores del cuadrante",
            (
                "LIBRE significa que no trabaja. COMIDA es turno de comida. "
                "CENA es turno de cena. DOBLE es comida y cena. '-' significa "
                "disponible sin turno. Sin repartidor significa plaza pendiente "
                "de cubrir."
            )
        ),
        (
            "10. Alertas",
            (
                "Las alertas indican problemas antes de publicar: turnos sin "
                "cubrir, plazas sin repartidor, horas extra, vacaciones, bajas "
                "o falta de demanda. Una alerta no siempre es un error: a veces "
                "indica que falta terminar la configuracion."
            )
        ),
        (
            "11. Exportaciones",
            (
                "Exportar sirve para sacar el cuadrante a Excel, PDF, CSV, ICS "
                "o integraciones preparadas. Primero guarda o publica el "
                "cuadrante, despues exporta."
            )
        ),
        (
            "12. Configuracion y backups",
            (
                "Configuracion muestra tema, datos locales, backups, email, "
                "webhook e integraciones. Antes de restaurar datos, la app "
                "valida la base y crea una copia de seguridad."
            )
        )
    )

    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(14)

        self.layout.addWidget(
            PageHeader(
                "Guia de uso",
                "Como poner en marcha la aplicacion sin perderse"
            )
        )

        self.contenido = QWidget()
        self.contenido_layout = QVBoxLayout(self.contenido)
        self.contenido_layout.setContentsMargins(0, 0, 0, 0)
        self.contenido_layout.setSpacing(12)

        self.resumen = QLabel(
            "Si estas empezando: ve en orden y no generes cuadrantes hasta "
            "que Puesta en marcha diga que la configuracion esta lista."
        )
        self.resumen.setWordWrap(True)
        self.resumen.setObjectName("guia_operativa")
        self.contenido_layout.addWidget(self.resumen)

        self.tarjetas = []

        for titulo, texto in self.SECCIONES:

            self.tarjetas.append(self.crear_tarjeta(titulo, texto))
            self.contenido_layout.addWidget(self.tarjetas[-1])

        self.contenido_layout.addStretch()
        self.scroll = create_scroll_area(self.contenido)
        self.layout.addWidget(self.scroll)

    def crear_tarjeta(self, titulo, texto):

        tarjeta = QFrame()
        tarjeta.setObjectName("card")
        layout = QVBoxLayout(tarjeta)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        etiqueta_titulo = QLabel(titulo)
        etiqueta_titulo.setObjectName("cardTitle")
        etiqueta_titulo.setWordWrap(True)

        etiqueta_texto = QLabel(texto)
        etiqueta_texto.setWordWrap(True)
        etiqueta_texto.setObjectName("pageSubtitle")

        layout.addWidget(etiqueta_titulo)
        layout.addWidget(etiqueta_texto)
        return tarjeta
