import unicodedata
from datetime import date, datetime

from services.constraints import DIAS


TURNOS_DISPONIBILIDAD = {
    "comida": ("comida",),
    "cena": ("noche",),
    "noche": ("noche",),
    "turno partido": ("comida", "noche")
}


def esta_disponible_dia(repartidor, dia):

    disponibilidad = repartidor.get("disponibilidad") or {}

    if not disponibilidad:

        return True

    if isinstance(disponibilidad, (list, tuple, set)):

        return dia in disponibilidad

    valor = disponibilidad.get(dia)

    if isinstance(valor, str):

        return valor.strip().lower() != "no disponible"

    return bool(valor)


def esta_disponible(repartidor, dia, turno):

    disponibilidad = repartidor.get("disponibilidad") or {}

    if not disponibilidad:

        return True

    if isinstance(disponibilidad, (list, tuple, set)):

        return dia in disponibilidad

    valor = disponibilidad.get(dia)

    if valor is None:

        return False

    if isinstance(valor, bool):

        return valor

    if isinstance(valor, str):

        valor_normalizado = valor.strip().lower()

        if valor_normalizado == "no disponible":

            return False

        requeridos = claves_disponibilidad_turno(turno)

        if turno is None or not requeridos or valor_normalizado == "ambos":

            return True

        if valor_normalizado == "comidas":

            return "comida" in requeridos

        if valor_normalizado == "cenas":

            return "noche" in requeridos or "cena" in requeridos

        return False

    if turno is None:

        return bool(valor)

    requeridos = claves_disponibilidad_turno(turno)

    if not requeridos:

        return True

    valores = set(valor)
    valores_normalizados = {
        normalizar_texto(elemento)
        for elemento in valores
    }
    nombre = nombre_turno_disponibilidad(turno)

    return (
        nombre in valores
        or normalizar_texto(nombre) in valores_normalizados
        or any(clave in valores_normalizados for clave in requeridos)
    )


def claves_disponibilidad_turno(turno):

    if turno is None:

        return ()

    texto = normalizar_texto_turno(turno)

    for clave, valores in TURNOS_DISPONIBILIDAD.items():

        if clave in texto:

            return valores

    nombre = nombre_turno_disponibilidad(turno)

    return (normalizar_texto(nombre),) if nombre else ()


def normalizar_texto_turno(turno):

    if isinstance(turno, dict):

        return normalizar_texto(
            f"{turno.get('tipo', '')} {turno.get('nombre', '')}"
        )

    return normalizar_texto(turno)


def nombre_turno_disponibilidad(turno):

    if turno is None:

        return None

    if isinstance(turno, dict):

        return turno.get("nombre")

    return turno


def categoria_turno(turno):

    nombre = nombre_turno_disponibilidad(turno)

    if not nombre:

        return None

    texto = normalizar_texto(nombre)

    if "comida" in texto:

        return "comida"

    if "cena" in texto or "noche" in texto:

        return "noche"

    return texto


def turno_tiene_horario(turno):

    return bool(turno and turno.get("hora_inicio") and turno.get("hora_fin"))


def intervalo_turno(dia, turno):

    if not turno_tiene_horario(turno):

        return None

    if dia not in DIAS:

        return None

    inicio = minutos_hora(turno.get("hora_inicio"))
    fin = minutos_hora(turno.get("hora_fin"))

    if inicio is None or fin is None:

        return None

    base = DIAS.index(dia) * 24 * 60

    if turno.get("cruza_medianoche") or fin <= inicio:

        fin += 24 * 60

    return base + inicio, base + fin


def intervalos_solapados(inicio_a, fin_a, inicio_b, fin_b):

    inicio_a = minutos_hora(inicio_a)
    fin_a = minutos_hora(fin_a)
    inicio_b = minutos_hora(inicio_b)
    fin_b = minutos_hora(fin_b)

    if None in (inicio_a, fin_a, inicio_b, fin_b):

        return False

    if fin_a <= inicio_a:

        fin_a += 24 * 60

    if fin_b <= inicio_b:

        fin_b += 24 * 60

    return inicio_a < fin_b and inicio_b < fin_a


def minutos_hora(valor):

    try:

        hora, minuto = str(valor).split(":")[:2]
        return int(hora) * 60 + int(minuto)

    except (TypeError, ValueError):

        return None


def parsear_fecha(valor):

    if isinstance(valor, date):

        return valor

    if isinstance(valor, datetime):

        return valor.date()

    if not valor:

        return None

    try:

        return datetime.strptime(str(valor), "%Y-%m-%d").date()

    except ValueError:

        return None


def normalizar_texto(texto):

    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFD", texto)

    return "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
