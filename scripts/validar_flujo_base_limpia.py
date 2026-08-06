import sys
import tempfile
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import database.database as database
from database.database import crear_base_datos
from services.cuadrantes_service import CuadrantesService
from services.datos_iniciales import DatosInicialesService


SEMANA_VALIDACION = "2026-08-03"


def ejecutar_validacion():

    ruta_original = database.RUTA_BD
    errores = []

    try:

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"
            crear_base_datos()

            resumen_datos = DatosInicialesService().crear_datos_minimos()
            if resumen_datos["repartidores_creados"] != 0:
                errores.append(
                    "Los datos minimos no deben crear repartidores demo."
                )

            ana = crear_repartidor_real(
                "Ana",
                {
                    "lunes": "No disponible",
                    "martes": "No disponible",
                    "miercoles": "Ambos",
                    "jueves": "Ambos",
                    "viernes": "Ambos",
                    "sabado": "Ambos",
                    "domingo": "Ambos"
                },
                resumen_datos
            )
            luis = crear_repartidor_real(
                "Luis",
                {
                    "lunes": "Ambos",
                    "martes": "Ambos",
                    "miercoles": "No disponible",
                    "jueves": "No disponible",
                    "viernes": "Ambos",
                    "sabado": "Ambos",
                    "domingo": "Ambos"
                },
                resumen_datos
            )

            servicio = CuadrantesService()
            contexto = servicio.obtener_contexto()
            precomprobacion = servicio.precomprobar_generacion(
                contexto,
                SEMANA_VALIDACION
            )
            if not precomprobacion["puede_generar"]:
                errores.extend(precomprobacion["errores"])

            generacion = servicio.generar_cuadrante(contexto, SEMANA_VALIDACION)
            resumen_generacion = servicio.resumen_generacion(
                generacion["resultado"]
            )
            servicio.guardar_cuadrante(
                SEMANA_VALIDACION,
                generacion["asignaciones"]
            )
            calendario = database.obtener_calendario_semanal(SEMANA_VALIDACION)

            if resumen_generacion["asignaciones_generadas"] != 14:
                errores.append("El cuadrante debe generar 14 plazas semanales.")
            if resumen_generacion["asignaciones_sin_repartidor"] != 0:
                errores.append(
                    "El cuadrante no debe dejar plazas sin repartidor."
                )
            if len(calendario) != 14:
                errores.append(
                    "El calendario guardado debe conservar 14 asignaciones."
                )

            errores.extend(
                validar_libranzas(
                    calendario,
                    {
                        ana: {"lunes", "martes"},
                        luis: {"miercoles", "jueves"}
                    }
                )
            )

            return {
                "ok": not errores,
                "errores": errores,
                "semana": SEMANA_VALIDACION,
                "asignaciones": resumen_generacion["asignaciones_generadas"],
                "cubiertas": resumen_generacion["asignaciones_con_repartidor"],
                "pendientes": resumen_generacion["asignaciones_sin_repartidor"],
                "calendario_guardado": len(calendario)
            }

    finally:

        database.RUTA_BD = ruta_original


def crear_repartidor_real(nombre, disponibilidad, resumen_datos):

    return database.insertar_repartidor(
        nombre,
        30,
        "Zona principal",
        1,
        1,
        70,
        70,
        50,
        disponibilidad=disponibilidad,
        ciudad_principal_id=resumen_datos["ciudad_id"],
        restaurante_principal_id=resumen_datos["restaurante_id"],
        ciudades_autorizadas=[resumen_datos["ciudad_id"]],
        restaurantes_autorizados=[resumen_datos["restaurante_id"]]
    )


def validar_libranzas(calendario, libranzas_por_repartidor):

    errores = []
    for fila in calendario:

        dia = fila[1]
        repartidor_id = fila[9]
        dias_libres = libranzas_por_repartidor.get(repartidor_id, set())
        if dia in dias_libres:
            errores.append(
                f"Repartidor {repartidor_id} asignado en dia libre {dia}."
            )

    return errores


def main():

    resultado = ejecutar_validacion()
    print("Validacion de flujo desde base limpia")
    print(f"Semana: {resultado['semana']}")
    print(f"Asignaciones generadas: {resultado['asignaciones']}")
    print(f"Cubiertas: {resultado['cubiertas']}")
    print(f"Pendientes: {resultado['pendientes']}")
    print(f"Guardadas en calendario: {resultado['calendario_guardado']}")

    if resultado["ok"]:
        print("Resultado: OK")
        return 0

    print("Resultado: ERROR")
    for error in resultado["errores"]:
        print(f"- {error}")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
