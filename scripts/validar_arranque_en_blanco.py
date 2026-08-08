import sys
import tempfile
from pathlib import Path

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

import database.database as database
from database.database import crear_base_datos
from database.schema import CIUDAD_SIN_CIUDAD
from repositories.ciudades_repository import CiudadesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository


TABLAS_OPERATIVAS_VACIAS = (
    "restaurantes",
    "repartidores",
    "turnos",
    "restaurante_turnos",
    "demanda_restaurante",
    "demanda_zona",
    "demanda_ciudad",
    "calendario_semanal"
)


def ejecutar_validacion():

    ruta_original = database.RUTA_BD
    errores = []

    try:

        with tempfile.TemporaryDirectory() as temporal:

            database.RUTA_BD = Path(temporal) / "delivery.db"
            crear_base_datos()

            visibles = {
                "ciudades": len(CiudadesRepository().listar_activas()),
                "restaurantes": len(RestaurantesRepository().listar_activos()),
                "repartidores": len(RepartidoresRepository().listar_activos()),
                "turnos": len(TurnosRepository().listar_activos())
            }
            conteos = contar_tablas()
            ciudad_tecnica = obtener_ciudad_tecnica()

            for nombre, total in visibles.items():

                if total:

                    errores.append(
                        f"La pantalla de {nombre} debe arrancar vacia."
                    )

            for tabla in TABLAS_OPERATIVAS_VACIAS:

                if conteos[tabla]:

                    errores.append(
                        f"La tabla {tabla} debe arrancar sin datos operativos."
                    )

            if conteos["ciudades"] != 1:

                errores.append(
                    "La base nueva solo debe contener la ciudad tecnica interna."
                )

            if ciudad_tecnica != CIUDAD_SIN_CIUDAD:

                errores.append(
                    "La ciudad tecnica interna debe ser 'Sin ciudad'."
                )

            return {
                "ok": not errores,
                "errores": errores,
                "visibles": visibles,
                "conteos": conteos,
                "ciudad_tecnica": ciudad_tecnica
            }

    finally:

        database.RUTA_BD = ruta_original


def contar_tablas():

    conexion = database.conectar()
    cursor = conexion.cursor()
    conteos = {}

    for tabla in ("ciudades",) + TABLAS_OPERATIVAS_VACIAS:

        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        conteos[tabla] = cursor.fetchone()[0]

    conexion.close()
    return conteos


def obtener_ciudad_tecnica():

    conexion = database.conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM ciudades ORDER BY id")
    fila = cursor.fetchone()
    conexion.close()
    return fila[0] if fila else None


def main():

    resultado = ejecutar_validacion()
    print("Validacion de arranque en blanco")
    print(f"Ciudad tecnica interna: {resultado['ciudad_tecnica']}")
    print(f"Datos visibles: {resultado['visibles']}")
    print(f"Conteos: {resultado['conteos']}")

    if resultado["ok"]:
        print("Resultado: OK")
        return 0

    print("Resultado: ERROR")
    for error in resultado["errores"]:
        print(f"- {error}")
    return 1


if __name__ == "__main__":

    raise SystemExit(main())
