from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QVBoxLayout,
    QWidget
)

from database.database import (
    DIAS_SEMANA,
    obtener_calendario_semanal,
    obtener_repartidores,
    obtener_restaurantes,
    obtener_turnos
)
from ui.widgets import CardWidget, PageHeader, make_button


class VistaInicio(QWidget):

    def __init__(self, ventana=None):
        super().__init__()

        self.ventana = ventana
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(24, 22, 24, 22)
        self.layout.setSpacing(18)

        self.layout.addWidget(
            PageHeader(
                "Inicio",
                "Resumen operativo de Planificador Delivery Pro"
            )
        )

        self.grid = QGridLayout()
        self.grid.setSpacing(14)

        self.cards = {
            "repartidores": CardWidget("Repartidores activos"),
            "restaurantes": CardWidget("Restaurantes activos"),
            "turnos": CardWidget("Turnos creados"),
            "sin_cubrir": CardWidget("Turnos sin cubrir"),
            "horas": CardWidget("Horas asignadas"),
            "alertas": CardWidget("Alertas importantes")
        }

        posiciones = [
            ("repartidores", 0, 0),
            ("restaurantes", 0, 1),
            ("turnos", 0, 2),
            ("sin_cubrir", 1, 0),
            ("horas", 1, 1),
            ("alertas", 1, 2)
        ]

        for clave, fila, columna in posiciones:

            self.grid.addWidget(self.cards[clave], fila, columna)

        self.layout.addLayout(self.grid)

        acciones = QHBoxLayout()
        acciones.setSpacing(10)

        botones = [
            ("Nuevo repartidor", "repartidores"),
            ("Nuevo restaurante", "restaurantes"),
            ("Nuevo turno", "turnos"),
            ("Generar cuadrante", "cuadrantes")
        ]

        for texto, pagina in botones:

            boton = make_button(texto, "primary" if pagina == "cuadrantes" else "secondary")
            boton.clicked.connect(
                lambda checked=False, destino=pagina: self.ir_a(destino)
            )
            acciones.addWidget(boton)

        acciones.addStretch()
        self.layout.addLayout(acciones)
        self.layout.addStretch()

        self.cargar_datos()

    # ======================================

    def cargar_datos(self):

        repartidores = obtener_repartidores()
        restaurantes = [
            restaurante
            for restaurante in obtener_restaurantes()
            if restaurante[6]
        ]
        turnos = [
            turno
            for turno in obtener_turnos()
            if turno[7]
        ]
        calendario = obtener_calendario_semanal()

        turnos_cubiertos = {
            (
                asignacion[1],
                asignacion[2],
                asignacion[6]
            )
            for asignacion in calendario
        }
        sin_cubrir = max(
            0,
            len(DIAS_SEMANA) * len(turnos) * len(restaurantes)
            - len(turnos_cubiertos)
        )
        duraciones = {
            turno[0]: float(turno[6] or 0)
            for turno in turnos
        }
        horas = sum(
            duraciones.get(asignacion[2], 0)
            for asignacion in calendario
        )
        alertas = 0

        if sin_cubrir:

            alertas += 1

        if not repartidores:

            alertas += 1

        self.cards["repartidores"].set_value(len(repartidores))
        self.cards["restaurantes"].set_value(len(restaurantes))
        self.cards["turnos"].set_value(len(turnos))
        self.cards["sin_cubrir"].set_value(sin_cubrir)
        self.cards["horas"].set_value(horas)
        self.cards["alertas"].set_value(alertas if alertas else "Sin datos")

    # ======================================

    def ir_a(self, pagina):

        if self.ventana:

            self.ventana.mostrar_pagina(pagina)
