import sys
import tempfile
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import database.database as database
from database.database import crear_base_datos
from repositories.restaurantes_repository import RestaurantesRepository
from services.cuadrantes_service import CuadrantesService


SEMANA_VALIDACION = "2026-08-03"
ZONA_VALIDACION = "Santiago Centro"
DIAS = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo"
)


def ejecutar_validacion():

    ruta_original = database.RUTA_BD
    errores = []

    try:

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"
            crear_base_datos()

            turno_comida = database.insertar_turno(
                "Comida",
                "Comida",
                "13:00",
                "16:00",
                "#2563EB",
                3
            )
            turno_cena = database.insertar_turno(
                "Cena",
                "Cena",
                "20:00",
                "23:30",
                "#7C3AED",
                3.5
            )

            database.guardar_demanda_zona(
                demandas_semana(turno_comida, turno_cena)
            )

            crear_repartidor_zona("Repartidor 1", "lunes", "martes")
            crear_repartidor_zona("Repartidor 2", "martes", "miercoles")
            crear_repartidor_zona("Repartidor 3", "jueves", "viernes")
            crear_repartidor_zona("Repartidor 4", "miercoles", "jueves")

            servicio = CuadrantesService()
            contexto = servicio.obtener_contexto()
            precomprobacion = servicio.precomprobar_generacion(
                contexto,
                SEMANA_VALIDACION
            )

            if not precomprobacion["puede_generar"]:
                errores.extend(precomprobacion["errores"])

            if "cobertura general" not in precomprobacion["texto"]:
                errores.append(
                    "La precomprobacion debe explicar la cobertura general."
                )

            if RestaurantesRepository().listar_activos():
                errores.append(
                    "La validacion debe empezar sin restaurantes activos."
                )

            generacion = servicio.generar_cuadrante(contexto, SEMANA_VALIDACION)
            resumen = servicio.resumen_generacion(generacion["resultado"])
            servicio.guardar_cuadrante(
                SEMANA_VALIDACION,
                generacion["asignaciones"]
            )

            calendario = database.obtener_calendario_semanal(SEMANA_VALIDACION)
            restaurantes_activos = RestaurantesRepository().listar_activos()

            if resumen["asignaciones_generadas"] != 14:
                errores.append("Debe generar 14 plazas por demanda de zona.")

            if resumen["asignaciones_sin_repartidor"] != 0:
                errores.append(
                    "La cobertura por zona no debe dejar plazas sin repartidor."
                )

            if len(calendario) != 14:
                errores.append(
                    "El calendario guardado debe conservar 14 asignaciones."
                )

            if restaurantes_activos:
                errores.append(
                    "Guardar cobertura general no debe crear restaurantes "
                    "activos visibles."
                )

            return {
                "ok": not errores,
                "errores": errores,
                "semana": SEMANA_VALIDACION,
                "zona": ZONA_VALIDACION,
                "asignaciones": resumen["asignaciones_generadas"],
                "cubiertas": resumen["asignaciones_con_repartidor"],
                "pendientes": resumen["asignaciones_sin_repartidor"],
                "calendario_guardado": len(calendario),
                "restaurantes_activos": len(restaurantes_activos)
            }

    finally:

        database.RUTA_BD = ruta_original


def demandas_semana(turno_comida, turno_cena):

    demandas = []

    for dia in DIAS:

        demandas.append({
            "zona": ZONA_VALIDACION,
            "turno_id": turno_comida,
            "dia_semana": dia,
            "repartidores_necesarios": 1
        })
        demandas.append({
            "zona": ZONA_VALIDACION,
            "turno_id": turno_cena,
            "dia_semana": dia,
            "repartidores_necesarios": 1
        })

    return demandas


def crear_repartidor_zona(nombre, descanso_inicio, descanso_fin):

    return database.insertar_repartidor(
        nombre,
        40,
        ZONA_VALIDACION,
        1,
        1,
        70,
        70,
        50,
        descanso_inicio=descanso_inicio,
        descanso_fin=descanso_fin,
        disponibilidad={
            dia: disponibilidad_para_dia(dia, descanso_inicio, descanso_fin)
            for dia in DIAS
        },
        apoyo_flexible=1,
        max_horas_diarias=10,
        max_dias_consecutivos=5
    )


def disponibilidad_para_dia(dia, descanso_inicio, descanso_fin):

    if dia in (descanso_inicio, descanso_fin):

        return "No disponible"

    return "Ambos"


def main():

    resultado = ejecutar_validacion()
    print("Validacion de flujo por zona general")
    print(f"Semana: {resultado['semana']}")
    print(f"Zona: {resultado['zona']}")
    print(f"Asignaciones generadas: {resultado['asignaciones']}")
    print(f"Cubiertas: {resultado['cubiertas']}")
    print(f"Pendientes: {resultado['pendientes']}")
    print(f"Guardadas en calendario: {resultado['calendario_guardado']}")
    print(f"Restaurantes activos visibles: {resultado['restaurantes_activos']}")

    if resultado["ok"]:
        print("Resultado: OK")
        return 0

    print("Resultado: ERROR")
    for error in resultado["errores"]:
        print(f"- {error}")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
