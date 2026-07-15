from datetime import UTC, datetime

from services.fechas import normalizar_fecha_inicio_semana


ESQUEMA_DELIVERY = "planificador.delivery.v1"


def crear_payload_delivery(datos):

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        datos.get("fecha_inicio_semana")
    )

    return {
        "schema": ESQUEMA_DELIVERY,
        "fecha_inicio_semana": fecha_inicio_semana,
        "generado_en": datetime.now(UTC).isoformat(),
        "turnos": [
            normalizar_turno_delivery(fila)
            for fila in datos.get("horarios", [])
        ],
        "totales": {
            str(fila[0]): fila[1]
            for fila in datos.get("totales", [])
        }
    }


def normalizar_turno_delivery(fila):

    return {
        "dia": fila[0],
        "turno": fila[1],
        "tipo": fila[2],
        "restaurante": fila[3],
        "zona": fila[4] or "",
        "repartidor": fila[5] or "",
        "hora_inicio": fila[6],
        "hora_fin": fila[7],
        "horas": float(fila[8] or 0)
    }


def crear_webhook_simulado(url, datos):

    url = str(url or "").strip()

    if not url:

        raise ValueError("Configura la URL del webhook generico.")

    return {
        "simulado": True,
        "metodo": "POST",
        "url": url,
        "headers": {
            "Content-Type": "application/json"
        },
        "payload": crear_payload_delivery(datos)
    }
