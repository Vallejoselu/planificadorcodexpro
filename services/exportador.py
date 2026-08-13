import csv
import json
from datetime import UTC, datetime, time, timedelta
from html import escape
from pathlib import Path

from database.schema import DIAS_SEMANA
from repositories.calendario_repository import CalendarioRepository
from repositories.historial_repository import HistorialRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository
from services.descansos import descanso_es_valido
from services.delivery_payload import crear_payload_delivery
from services.fechas import normalizar_fecha_inicio_semana
from services.cuadrantes_service import CuadrantesService


calendario_repository = CalendarioRepository()
repartidores_repository = RepartidoresRepository()
restaurantes_repository = RestaurantesRepository()
turnos_repository = TurnosRepository()
historial_repository = HistorialRepository()

PALETA_CUADRANTE_EXCEL = {
    "libre": ("F4B6C2", "9F1239"),
    "doble": ("FDE68A", "111827"),
    "comida": ("D9F0F2", "111827"),
    "cena": ("D7E2F5", "111827"),
    "valle": ("DCFCE7", "14532D"),
    "turno": ("E5E7EB", "111827"),
    "disponible": ("FFFFFF", "6B7280"),
    "pendiente": ("FEF3C7", "92400E")
}


def exportar_excel(ruta, fecha_inicio_semana=None):

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    datos = preparar_datos_exportacion(fecha_inicio_semana)
    libro = Workbook()
    hoja_cuadrante = libro.active
    hoja_cuadrante.title = "Cuadrante semanal"
    datos_cuadrante = preparar_cuadrante_semanal_exportacion(
        fecha_inicio_semana
    )
    _escribir_cuadrante_semanal_excel(hoja_cuadrante, datos_cuadrante)

    _crear_hoja(
        libro,
        "Horarios",
        datos["horarios"],
        ["Dia", "Turno", "Tipo", "Restaurante", "Zona", "Repartidor", "Inicio", "Fin", "Horas"]
    )
    _crear_hoja(
        libro,
        "Horas",
        datos["horas"],
        ["Concepto", "Nombre", "Horas"]
    )
    _crear_hoja(
        libro,
        "Descansos",
        datos["descansos"],
        ["Repartidor", "Horas contrato", "Descanso 1", "Descanso 2"]
    )
    _crear_hoja(
        libro,
        "Totales",
        datos["totales"],
        ["Concepto", "Valor"]
    )

    for hoja in libro.worksheets:

        if hoja.title == "Cuadrante semanal":

            continue

        _aplicar_estilo_hoja_datos(hoja, Font, PatternFill)

    _aplicar_estilo_cuadrante(
        hoja_cuadrante,
        datos_cuadrante,
        Alignment,
        Border,
        Font,
        PatternFill,
        Side
    )

    libro.save(ruta)
    registrar_exportacion("Excel", ruta, fecha_inicio_semana)


def exportar_csv(ruta, fecha_inicio_semana=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    datos = preparar_datos_exportacion(fecha_inicio_semana)

    with open(ruta, "w", newline="", encoding="utf-8-sig") as archivo:

        escritor = csv.writer(archivo, delimiter=";")

        _escribir_bloque_csv(
            escritor,
            "Horarios",
            ["Dia", "Turno", "Tipo", "Restaurante", "Zona", "Repartidor", "Inicio", "Fin", "Horas"],
            datos["horarios"]
        )
        _escribir_bloque_csv(
            escritor,
            "Horas",
            ["Concepto", "Nombre", "Horas"],
            datos["horas"]
        )
        _escribir_bloque_csv(
            escritor,
            "Descansos",
            ["Repartidor", "Horas contrato", "Descanso 1", "Descanso 2"],
            datos["descansos"]
        )
        _escribir_bloque_csv(
            escritor,
            "Totales",
            ["Concepto", "Valor"],
            datos["totales"]
        )

    registrar_exportacion("CSV", ruta, fecha_inicio_semana)


def exportar_ics(ruta, fecha_inicio_semana=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    datos = preparar_datos_exportacion(fecha_inicio_semana)
    contenido = crear_calendario_ics(datos)

    with open(ruta, "w", newline="", encoding="utf-8") as archivo:

        archivo.write(contenido)

    registrar_exportacion("ICS", ruta, fecha_inicio_semana)


def exportar_delivery_json(ruta, fecha_inicio_semana=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    datos = preparar_datos_exportacion(fecha_inicio_semana)
    payload = crear_payload_delivery(datos)

    with open(ruta, "w", encoding="utf-8") as archivo:

        json.dump(payload, archivo, ensure_ascii=False, indent=2)

    registrar_exportacion("Delivery JSON", ruta, fecha_inicio_semana)


def exportar_pdf(ruta, fecha_inicio_semana=None):

    from PySide6.QtGui import QPageSize, QPdfWriter, QTextDocument

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    documento = QTextDocument()
    documento.setHtml(_crear_html(preparar_datos_exportacion(fecha_inicio_semana)))

    escritor = QPdfWriter(ruta)
    escritor.setPageSize(QPageSize(QPageSize.A4))
    escritor.setResolution(96)

    documento.print_(escritor)
    registrar_exportacion("PDF", ruta, fecha_inicio_semana)


def registrar_exportacion(formato, ruta, fecha_inicio_semana):

    historial_repository.registrar(
        "Exportar",
        "exportacion",
        f"{formato}: {ruta}",
        fecha_inicio_semana
    )


def preparar_datos_exportacion(fecha_inicio_semana=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )

    turnos = {
        turno[0]: turno
        for turno in turnos_repository.listar_todos()
    }
    restaurantes = {
        restaurante[0]: restaurante
        for restaurante in restaurantes_repository.listar_todos()
    }

    horarios = _preparar_horarios(
        turnos,
        restaurantes,
        fecha_inicio_semana
    )
    horas = _preparar_horas(horarios)
    descansos = _preparar_descansos()
    totales = _preparar_totales(horarios, descansos)

    return {
        "horarios": horarios,
        "horas": horas,
        "descansos": descansos,
        "totales": totales,
        "fecha_inicio_semana": fecha_inicio_semana
    }


def preparar_cuadrante_semanal_exportacion(fecha_inicio_semana=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )
    servicio = CuadrantesService(
        calendario_repository=calendario_repository,
        repartidores_repository=repartidores_repository,
        restaurantes_repository=restaurantes_repository,
        turnos_repository=turnos_repository
    )
    calendario = calendario_repository.listar_semana(fecha_inicio_semana)
    asignaciones = servicio.agrupar_calendario(calendario)
    turnos = turnos_repository.listar_todos()
    restaurantes = restaurantes_repository.listar_todos()
    repartidores = repartidores_repository.listar_activos()
    filas = servicio.construir_filas_repartidores(
        asignaciones,
        turnos,
        restaurantes,
        repartidores,
        fecha_inicio_semana
    )

    return {
        "fecha_inicio_semana": fecha_inicio_semana,
        "dias": _dias_exportacion(fecha_inicio_semana),
        "filas": filas
    }


def _dias_exportacion(fecha_inicio_semana):

    inicio = datetime.strptime(fecha_inicio_semana, "%Y-%m-%d").date()

    return [
        {
            "dia": dia,
            "fecha": inicio + timedelta(days=indice),
            "cabecera": (
                f"{dia.capitalize()}\n"
                f"{(inicio + timedelta(days=indice)).strftime('%d/%m')}"
            )
        }
        for indice, dia in enumerate(DIAS_SEMANA)
    ]


def _escribir_cuadrante_semanal_excel(hoja, datos):

    hoja.append(["Planificador Delivery Pro"])
    hoja.append([f"Cuadrante semanal desde {datos['fecha_inicio_semana']}"])
    hoja.append([])
    hoja.append(
        ["Empleado", "Contrato"]
        + [dia["cabecera"] for dia in datos["dias"]]
        + ["Total", "Horas comp."]
    )

    for fila in datos["filas"]:

        hoja.append(
            [
                fila["nombre"],
                fila["contrato"],
                *[
                    fila["celdas"].get(dia["dia"], {}).get("texto", "-")
                    for dia in datos["dias"]
                ],
                _formatear_horas_excel(fila.get("total_horas", 0)),
                _formatear_horas_excel(fila.get("complementarias", 0))
            ]
        )

    hoja.append([])
    hoja.append(["Leyenda"])

    for estado, etiqueta in (
        ("libre", "LIBRE: dia no laborable, descanso, vacaciones o baja"),
        ("comida", "COMIDA: turno de comida"),
        ("cena", "CENA: turno de cena"),
        ("valle", "VALLE: horas valle"),
        ("doble", "DOBLE: comida y cena el mismo dia"),
        ("pendiente", "PENDIENTE: plaza sin repartidor")
    ):

        hoja.append([etiqueta])
        hoja.cell(hoja.max_row, 1).value = etiqueta
        hoja.cell(hoja.max_row, 2).value = estado


def _aplicar_estilo_cuadrante(
    hoja,
    datos,
    Alignment,
    Border,
    Font,
    PatternFill,
    Side
):

    max_columna = 11
    borde = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB")
    )
    hoja.merge_cells(start_row=1, start_column=1, end_row=1, end_column=max_columna)
    hoja.merge_cells(start_row=2, start_column=1, end_row=2, end_column=max_columna)
    hoja.freeze_panes = "C5"
    hoja.sheet_view.showGridLines = False

    hoja["A1"].font = Font(bold=True, size=16, color="FFFFFF")
    hoja["A1"].fill = PatternFill("solid", fgColor="164E63")
    hoja["A1"].alignment = Alignment(horizontal="center")
    hoja["A2"].font = Font(bold=True, color="164E63")
    hoja["A2"].alignment = Alignment(horizontal="center")

    for celda in hoja[4]:

        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill("solid", fgColor="164E63")
        celda.alignment = Alignment(
            horizontal="center",
            vertical="center",
            wrap_text=True
        )
        celda.border = borde

    inicio_filas = 5
    fin_filas = inicio_filas + len(datos["filas"]) - 1

    for indice_fila, fila in enumerate(datos["filas"], start=inicio_filas):

        for columna in (1, 2):

            celda = hoja.cell(indice_fila, columna)
            celda.font = Font(bold=True if columna == 1 else False)
            celda.fill = PatternFill("solid", fgColor="F3F4F6")
            celda.alignment = Alignment(vertical="center", wrap_text=True)
            celda.border = borde

        for indice_dia, dia in enumerate(datos["dias"], start=3):

            info = fila["celdas"].get(dia["dia"], {})
            estado = info.get("estado", "disponible")
            fondo, texto = PALETA_CUADRANTE_EXCEL.get(
                estado,
                PALETA_CUADRANTE_EXCEL["disponible"]
            )
            celda = hoja.cell(indice_fila, indice_dia)
            celda.fill = PatternFill("solid", fgColor=fondo)
            celda.font = Font(
                bold=estado in ("libre", "doble"),
                color=texto
            )
            celda.alignment = Alignment(
                horizontal="center",
                vertical="center",
                wrap_text=True
            )
            celda.border = borde

        for columna in (10, 11):

            celda = hoja.cell(indice_fila, columna)
            celda.fill = PatternFill(
                "solid",
                fgColor=(
                    "FEF3C7"
                    if columna == 11 and fila.get("complementarias", 0)
                    else "F9FAFB"
                )
            )
            celda.font = Font(
                bold=bool(columna == 11 and fila.get("complementarias", 0))
            )
            celda.alignment = Alignment(horizontal="center", vertical="center")
            celda.border = borde

        hoja.row_dimensions[indice_fila].height = 58

    if fin_filas >= inicio_filas:

        hoja.auto_filter.ref = f"A4:K{fin_filas}"

    fila_leyenda = 6 + len(datos["filas"])
    hoja.cell(fila_leyenda, 1).font = Font(bold=True, color="164E63")

    for fila_excel in range(fila_leyenda + 1, hoja.max_row + 1):

        estado = hoja.cell(fila_excel, 2).value
        fondo, texto = PALETA_CUADRANTE_EXCEL.get(
            estado,
            PALETA_CUADRANTE_EXCEL["disponible"]
        )
        hoja.cell(fila_excel, 1).fill = PatternFill("solid", fgColor=fondo)
        hoja.cell(fila_excel, 1).font = Font(color=texto)
        hoja.cell(fila_excel, 2).value = ""

    hoja.column_dimensions["A"].width = 24
    hoja.column_dimensions["B"].width = 12

    for columna in ("C", "D", "E", "F", "G", "H", "I"):

        hoja.column_dimensions[columna].width = 20

    hoja.column_dimensions["J"].width = 12
    hoja.column_dimensions["K"].width = 14


def _aplicar_estilo_hoja_datos(hoja, Font, PatternFill):

    for celda in hoja[1]:

        celda.font = Font(bold=True)
        celda.fill = PatternFill("solid", fgColor="D9EAF7")

    for columna in hoja.columns:

        ancho = max(len(str(celda.value or "")) for celda in columna)
        hoja.column_dimensions[columna[0].column_letter].width = ancho + 2


def _formatear_horas_excel(valor):

    try:

        numero = float(valor or 0)

    except (TypeError, ValueError):

        numero = 0

    if numero.is_integer():

        return f"{int(numero)} h"

    return f"{numero:.1f} h"


def _preparar_horarios(turnos, restaurantes, fecha_inicio_semana):

    filas = []

    for asignacion in calendario_repository.listar_semana(fecha_inicio_semana):

        dia = asignacion[1]
        turno_id = asignacion[2]
        restaurante_id = asignacion[6]
        repartidor = asignacion[10] if len(asignacion) > 10 else ""
        turno = turnos.get(turno_id)
        restaurante = restaurantes.get(restaurante_id)

        if not turno or not restaurante:

            continue

        filas.append([
            dia,
            turno[2],
            turno[1],
            restaurante[1],
            restaurante[3] or "",
            repartidor or "",
            turno[3],
            turno[4],
            float(turno[6] or 0)
        ])

    filas.sort(key=lambda fila: (
        DIAS_SEMANA.index(fila[0]),
        fila[1],
        fila[3]
    ))

    return filas


def _preparar_horas(horarios):

    por_restaurante = {}
    por_turno = {}
    por_repartidor = {}

    for fila in horarios:

        restaurante = fila[3]
        turno = fila[1]
        repartidor = fila[5]
        horas = float(fila[8] or 0)

        por_restaurante[restaurante] = por_restaurante.get(restaurante, 0) + horas
        por_turno[turno] = por_turno.get(turno, 0) + horas

        if repartidor:

            por_repartidor[repartidor] = por_repartidor.get(repartidor, 0) + horas

    filas = []

    for restaurante, horas in sorted(por_restaurante.items()):

        filas.append(["Restaurante", restaurante, _formatear_numero(horas)])

    for turno, horas in sorted(por_turno.items()):

        filas.append(["Turno", turno, _formatear_numero(horas)])

    for repartidor, horas in sorted(por_repartidor.items()):

        filas.append(["Repartidor asignado", repartidor, _formatear_numero(horas)])

    for repartidor in repartidores_repository.listar_activos():

        filas.append([
            "Contrato repartidor",
            repartidor[1],
            repartidor[2]
        ])

    return filas


def _preparar_descansos():

    filas = []

    for repartidor in repartidores_repository.listar_activos():

        filas.append([
            repartidor[1],
            repartidor[2],
            _formatear_descanso_exportacion(repartidor, 9),
            _formatear_descanso_exportacion(repartidor, 10)
        ])

    return filas


def _formatear_descanso_exportacion(repartidor, posicion):

    if not repartidor[9] or not repartidor[10]:

        return repartidor[posicion] or ""

    if descanso_es_valido(repartidor[9], repartidor[10]):

        return repartidor[posicion]

    return f"{repartidor[posicion]} (no valido)"


def _preparar_totales(horarios, descansos):

    repartidores = repartidores_repository.listar_activos()
    total_horas = sum(float(fila[8] or 0) for fila in horarios)
    total_contratadas = sum(int(repartidor[2] or 0) for repartidor in repartidores)
    restaurantes = {
        fila[3]
        for fila in horarios
    }
    turnos = {
        fila[1]
        for fila in horarios
    }

    return [
        ["Total horarios", len(horarios)],
        ["Total horas planificadas", _formatear_numero(total_horas)],
        ["Total horas contratadas", total_contratadas],
        ["Total restaurantes", len(restaurantes)],
        ["Total tipos de turno", len(turnos)],
        ["Total repartidores", len(repartidores)],
        ["Total repartidores con descanso", len(descansos)]
    ]


def _crear_hoja(libro, nombre, filas, cabeceras):

    hoja = libro.create_sheet(nombre)
    _escribir_hoja(hoja, filas, cabeceras)


def _escribir_hoja(hoja, filas, cabeceras):

    hoja.append(cabeceras)

    for fila in filas:

        hoja.append(fila)


def _escribir_bloque_csv(escritor, titulo, cabeceras, filas):

    escritor.writerow([titulo])
    escritor.writerow(cabeceras)
    escritor.writerows(filas)
    escritor.writerow([])


def _crear_html(datos):

    partes = [
        "<html><body>",
        "<h1>Planificador Delivery Pro</h1>"
    ]

    bloques = [
        (
            "Horarios",
            ["Dia", "Turno", "Tipo", "Restaurante", "Zona", "Repartidor", "Inicio", "Fin", "Horas"],
            datos["horarios"]
        ),
        (
            "Horas",
            ["Concepto", "Nombre", "Horas"],
            datos["horas"]
        ),
        (
            "Descansos",
            ["Repartidor", "Horas contrato", "Descanso 1", "Descanso 2"],
            datos["descansos"]
        ),
        (
            "Totales",
            ["Concepto", "Valor"],
            datos["totales"]
        )
    ]

    for titulo, cabeceras, filas in bloques:

        partes.append(f"<h2>{titulo}</h2>")
        partes.append("<table border='1' cellspacing='0' cellpadding='4' width='100%'>")
        partes.append("<tr>")

        for cabecera in cabeceras:

            partes.append(f"<th>{escape(str(cabecera))}</th>")

        partes.append("</tr>")

        for fila in filas:

            partes.append("<tr>")

            for valor in fila:

                partes.append(f"<td>{escape(str(valor))}</td>")

            partes.append("</tr>")

        partes.append("</table>")

    partes.append("</body></html>")

    return "".join(partes)


def crear_calendario_ics(datos):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        datos.get("fecha_inicio_semana")
    )
    eventos = []

    for indice, fila in enumerate(datos.get("horarios", []), start=1):

        evento = _crear_evento_ics(fila, fecha_inicio_semana, indice)

        if evento:

            eventos.extend(evento)

    lineas = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Planificador Delivery Pro//ES",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Planificador Delivery Pro"
    ]
    lineas.extend(eventos)
    lineas.append("END:VCALENDAR")

    return "\r\n".join(_plegar_linea(linea) for linea in lineas) + "\r\n"


def _crear_evento_ics(fila, fecha_inicio_semana, indice):

    inicio = _datetime_evento(fecha_inicio_semana, fila[0], fila[6])
    fin = _datetime_evento(fecha_inicio_semana, fila[0], fila[7])

    if not inicio or not fin:

        return None

    if fin <= inicio:

        fin += timedelta(days=1)

    repartidor = fila[5] or "Sin repartidor"
    resumen = f"{fila[1]} - {fila[3]}"
    descripcion = (
        f"Tipo: {fila[2]}\n"
        f"Repartidor: {repartidor}\n"
        f"Zona: {fila[4] or ''}\n"
        f"Horas: {fila[8]}"
    )

    return [
        "BEGIN:VEVENT",
        f"UID:{_valor_ics(f'planificador-{fecha_inicio_semana}-{indice}@planificador-delivery-pro')}",
        f"DTSTAMP:{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        f"DTSTART:{_formatear_datetime_ics(inicio)}",
        f"DTEND:{_formatear_datetime_ics(fin)}",
        f"SUMMARY:{_valor_ics(resumen)}",
        f"LOCATION:{_valor_ics(fila[3])}",
        f"DESCRIPTION:{_valor_ics(descripcion)}",
        "END:VEVENT"
    ]


def _datetime_evento(fecha_inicio_semana, dia, hora):

    if dia not in DIAS_SEMANA:

        return None

    hora = _parsear_hora(hora)

    if hora is None:

        return None

    fecha = (
        datetime.strptime(fecha_inicio_semana, "%Y-%m-%d").date()
        + timedelta(days=DIAS_SEMANA.index(dia))
    )

    return datetime.combine(fecha, hora)


def _parsear_hora(valor):

    valor = str(valor or "").strip()

    if not valor:

        return None

    for formato in ("%H:%M", "%H:%M:%S"):

        try:

            return datetime.strptime(valor, formato).time()

        except ValueError:

            continue

    return None


def _formatear_datetime_ics(valor):

    if isinstance(valor, time):

        raise TypeError("Se esperaba fecha y hora completas.")

    return valor.strftime("%Y%m%dT%H%M%S")


def _valor_ics(valor):

    texto = str(valor or "")
    texto = texto.replace("\\", "\\\\")
    texto = texto.replace(";", "\\;")
    texto = texto.replace(",", "\\,")
    texto = texto.replace("\r\n", "\\n")
    texto = texto.replace("\n", "\\n")

    return texto


def _plegar_linea(linea):

    partes = []
    restante = str(linea)

    while len(restante) > 75:

        partes.append(restante[:75])
        restante = " " + restante[75:]

    partes.append(restante)

    return "\r\n".join(partes)


def _formatear_numero(valor):

    if float(valor).is_integer():

        return int(valor)

    return round(valor, 2)


def normalizar_ruta(ruta, extension):

    ruta = Path(ruta)

    if ruta.suffix.lower() != extension:

        ruta = ruta.with_suffix(extension)

    return str(ruta)
