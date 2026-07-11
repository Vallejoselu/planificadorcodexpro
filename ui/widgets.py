from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget
)


class PageHeader(QWidget):

    def __init__(self, title, subtitle=""):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 12)
        layout.setSpacing(4)

        self.title = QLabel(title)
        self.title.setObjectName("pageTitle")

        layout.addWidget(self.title)

        if subtitle:

            self.subtitle = QLabel(subtitle)
            self.subtitle.setObjectName("pageSubtitle")
            layout.addWidget(self.subtitle)


class CardWidget(QFrame):

    def __init__(self, title, value="Sin datos"):
        super().__init__()

        self.setObjectName("card")
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        self.title = QLabel(title)
        self.title.setObjectName("cardTitle")

        self.value = QLabel(str(value))
        self.value.setObjectName("cardValue")

        layout.addWidget(self.title)
        layout.addWidget(self.value)
        layout.addStretch()

    def set_value(self, value):

        self.value.setText(str(value))


class EmptyState(QFrame):

    def __init__(self, text):
        super().__init__()

        self.setObjectName("card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setObjectName("pageSubtitle")

        layout.addWidget(label)


def make_button(text, variant="secondary"):

    button = QPushButton(text)
    button.setProperty("variant", variant)
    return button


def configure_table(table):

    if isinstance(table, QTableWidget):

        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.verticalHeader().setDefaultSectionSize(38)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
