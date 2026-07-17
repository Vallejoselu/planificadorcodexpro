from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget
)

from database.schema import DIAS_SEMANA
from repositories.calendario_repository import CalendarioRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository
from ui.widgets import CardWidget, PageHeader, make_button


calendario_repository = CalendarioRepository()
repartidores_repository = RepartidoresRepository()
restaurantes_repository = RestaurantesRepository()
turnos_repository = TurnosRepository()


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

        self.guia_operativa = QLabel(
            "Orden recomendado: 1) Repartidores, 2) Restaurantes, "
            "3) Turnos, 4) Demanda, 5) Generar cuadrante."
        )
        self.guia_operativa.setWordWrap(True)
        self.guia_operativa.setObjectName("guia_operativa")
        self.guia_operativa.setStyleSheet("""
            padding:10px 12px;
            border:1px solid #CBD5E1;
            border-radius:6px;
            background:#F8FAFC;
            color:#1E293B;
        """)
        self.layout.addWidget(self.guia_operativa)

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
            ("Puesta en marcha", "puesta_marcha"),
            ("Nuevo repartidor", "repartidores"),
            ("Nuevo restaurante", "restaurantes"),
            ("Nuevo turno", "turnos"),
            ("Generar cuadrante", "cuadrantes")
        ]

        for texto, pagina in botones:

            boton = make_button(
                texto,
                (
                    "primary"
                    if pagina in ("puesta_marcha", "cuadrantes")
                    else "secondary"
                )
            )
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

        repartidores = repartidores_repository.listar_activos()
        restaurantes = restaurantes_repository.listar_activos()
        turnos = turnos_repository.listar_activos()
        calendario = calendario_repository.listar_semana()

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
        pendientes = []

        if sin_cubrir:

            alertas += 1

        if not repartidores:

            alertas += 1
            pendientes.append("crear repartidores")

        if not restaurantes:

            pendientes.append("crear restaurantes")

        if not turnos:

            pendientes.append("crear turnos")

        self.cards["repartidores"].set_value(len(repartidores))
        self.cards["restaurantes"].set_value(len(restaurantes))
        self.cards["turnos"].set_value(len(turnos))
        self.cards["sin_cubrir"].set_value(sin_cubrir)
        self.cards["horas"].set_value(horas)
        self.cards["alertas"].set_value(alertas if alertas else "Sin datos")

        if pendientes:

            self.guia_operativa.setText(
                "Antes de generar un cuadrante falta: "
                + ", ".join(pendientes)
                + ". Orden recomendado: Repartidores, Restaurantes, "
                "Turnos, Demanda y Generar cuadrante."
            )

        else:

            self.guia_operativa.setText(
                "Base preparada. Revisa la demanda de cada restaurante "
                "antes de generar el cuadrante."
            )

    # ======================================

    def ir_a(self, pagina):

        if self.ventana:

            self.ventana.mostrar_pagina(pagina)
