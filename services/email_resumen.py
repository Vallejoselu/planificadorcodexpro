import smtplib
from email.message import EmailMessage
from pathlib import Path

from services.credenciales import GestorCredencialesIntegracion
from services.exportador import preparar_datos_exportacion
from services.fechas import normalizar_fecha_inicio_semana


def preparar_resumen_email(fecha_inicio_semana=None, datos=None):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(fecha_inicio_semana)
    datos = datos or preparar_datos_exportacion(fecha_inicio_semana)
    horarios = datos.get("horarios", [])
    totales = {
        str(fila[0]): fila[1]
        for fila in datos.get("totales", [])
    }
    asunto = f"Cuadrante semanal {fecha_inicio_semana}"
    lineas = [
        f"Cuadrante semanal: {fecha_inicio_semana}",
        "",
        "Resumen",
        f"- Turnos planificados: {totales.get('Total horarios', len(horarios))}",
        f"- Horas planificadas: {totales.get('Total horas planificadas', 0)}",
        f"- Restaurantes: {totales.get('Total restaurantes', 0)}",
        f"- Repartidores: {totales.get('Total repartidores', 0)}",
        "",
        "Detalle"
    ]

    if not horarios:

        lineas.append("- No hay turnos planificados.")

    for fila in horarios:

        repartidor = fila[5] or "Sin repartidor"
        lineas.append(
            "- "
            f"{str(fila[0]).capitalize()} {fila[6]}-{fila[7]} | "
            f"{fila[1]} | {fila[3]} | {repartidor}"
        )

    return {
        "asunto": asunto,
        "cuerpo": "\n".join(lineas),
        "fecha_inicio_semana": fecha_inicio_semana,
        "total_turnos": len(horarios)
    }


def crear_mensaje_resumen(
    destinatarios,
    remitente,
    fecha_inicio_semana=None,
    datos=None
):

    destinatarios = normalizar_destinatarios(destinatarios)
    remitente = str(remitente or "").strip()

    if not remitente:

        raise ValueError("El remitente es obligatorio.")

    resumen = preparar_resumen_email(fecha_inicio_semana, datos)
    mensaje = EmailMessage()
    mensaje["Subject"] = resumen["asunto"]
    mensaje["From"] = remitente
    mensaje["To"] = ", ".join(destinatarios)
    mensaje.set_content(resumen["cuerpo"])

    return mensaje


def exportar_resumen_email(
    ruta,
    destinatarios,
    remitente,
    fecha_inicio_semana=None,
    datos=None
):

    mensaje = crear_mensaje_resumen(
        destinatarios,
        remitente,
        fecha_inicio_semana,
        datos
    )
    ruta = Path(ruta)
    ruta.write_text(mensaje.as_string(), encoding="utf-8")

    return str(ruta)


def enviar_resumen_email(
    destinatarios,
    configuracion_smtp,
    referencia_credenciales,
    fecha_inicio_semana=None,
    datos=None,
    gestor_credenciales=None,
    smtp_factory=None
):

    configuracion_smtp = dict(configuracion_smtp or {})
    gestor_credenciales = gestor_credenciales or GestorCredencialesIntegracion()
    credenciales = gestor_credenciales.obtener(referencia_credenciales)

    if not credenciales:

        raise ValueError("No hay credenciales disponibles para enviar email.")

    host = str(configuracion_smtp.get("host") or "").strip()
    puerto = int(configuracion_smtp.get("puerto") or 587)
    remitente = str(
        configuracion_smtp.get("remitente")
        or credenciales.get("usuario")
        or ""
    ).strip()
    usuario = str(credenciales.get("usuario") or remitente).strip()
    clave = str(
        credenciales.get("clave")
        or credenciales.get("password")
        or ""
    )

    if not host:

        raise ValueError("El servidor SMTP es obligatorio.")

    if not usuario or not clave:

        raise ValueError("La referencia de credenciales no contiene usuario y clave.")

    mensaje = crear_mensaje_resumen(
        destinatarios,
        remitente,
        fecha_inicio_semana,
        datos
    )
    smtp_factory = smtp_factory or smtplib.SMTP

    with smtp_factory(host, puerto, timeout=30) as smtp:

        if configuracion_smtp.get("tls", True):

            smtp.starttls()

        smtp.login(usuario, clave)
        smtp.send_message(mensaje)

    return {
        "enviado": True,
        "destinatarios": normalizar_destinatarios(destinatarios),
        "asunto": mensaje["Subject"]
    }


def normalizar_destinatarios(destinatarios):

    if isinstance(destinatarios, str):

        destinatarios = [
            destino.strip()
            for destino in destinatarios.replace(";", ",").split(",")
        ]

    destinos = [
        str(destino or "").strip()
        for destino in (destinatarios or [])
        if str(destino or "").strip()
    ]

    if not destinos:

        raise ValueError("Debe indicarse al menos un destinatario.")

    for destino in destinos:

        if "@" not in destino:

            raise ValueError(f"Destinatario no valido: {destino}.")

    return destinos
