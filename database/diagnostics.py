from datetime import datetime

from database.connection import conectar
from database.migrations import crear_base_datos
from database.schema import (
    CIUDAD_SIN_CIUDAD,
    DESCANSOS_VALIDOS,
    DIAS_SEMANA,
    HORAS_CONTRATO,
    SCHEMA_VERSION_ACTUAL
)


INDICES_ESPERADOS = {
    "idx_calendario_semana_lookup",
    "idx_calendario_semana_unico",
    "idx_bajas_repartidor_activa",
    "idx_demanda_zona_dia_unico",
    "idx_demanda_zona_fecha_unica",
    "idx_demanda_zona_lookup",
    "idx_demanda_restaurante_dia_unico",
    "idx_demanda_restaurante_fecha_unica",
    "idx_demanda_restaurante_lookup",
    "idx_descansos_repartidor_activo",
    "idx_disponibilidad_repartidor",
    "idx_restaurante_repartidores_restaurante",
    "idx_restaurante_turnos_restaurante",
    "idx_restaurantes_ciudad_id",
    "idx_turnos_turno_restaurante_unico",
    "idx_vacaciones_repartidor_activo"
}


def diagnosticar_base_datos(ruta_bd=None):

    conexion = conectar(ruta_bd)

    try:

        cursor = conexion.cursor()
        errores = []
        advertencias = []
        info = []

        revisar_integridad_sqlite(cursor, errores)
        revisar_claves_foraneas(cursor, errores)
        revisar_schema_version(cursor, advertencias, info)
        revisar_indices(cursor, advertencias, info)
        revisar_restaurantes_sin_ciudad(cursor, advertencias)
        revisar_repartidores_horas_invalidas(cursor, advertencias)
        revisar_descansos_invalidos(cursor, advertencias)
        revisar_demandas_invalidas(cursor, advertencias)
        revisar_demandas_duplicadas(cursor, advertencias)
        revisar_calendario_duplicado(cursor, advertencias)

        return {
            "ok": not errores and not advertencias,
            "errores": errores,
            "advertencias": advertencias,
            "info": info
        }

    finally:

        conexion.close()


def reparar_base_datos(ruta_bd=None):

    crear_base_datos(ruta_bd)
    conexion = conectar(ruta_bd)

    try:

        cursor = conexion.cursor()
        acciones = []
        ciudad_id = obtener_ciudad_sin_ciudad(cursor)

        cursor.execute("""
        UPDATE restaurantes
        SET ciudad_id=?
        WHERE ciudad_id IS NULL
        """,(ciudad_id,))

        if cursor.rowcount:

            acciones.append(
                f"Restaurantes sin ciudad asociados a {CIUDAD_SIN_CIUDAD}."
            )

        cursor.execute("""
        UPDATE calendario_semanal
        SET fecha_inicio_semana='1970-01-05'
        WHERE fecha_inicio_semana IS NULL
        OR TRIM(fecha_inicio_semana)=''
        """)

        if cursor.rowcount:

            acciones.append(
                "Calendario antiguo asociado a la semana tecnica 1970-01-05."
            )

        acciones.extend(reparar_demandas_duplicadas(cursor))
        acciones.extend(reparar_calendario_duplicado(cursor))

        conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()

    diagnostico = diagnosticar_base_datos(ruta_bd)
    diagnostico["acciones"] = acciones

    return diagnostico


def revisar_integridad_sqlite(cursor, errores):

    cursor.execute("PRAGMA integrity_check")
    resultado = [
        fila[0]
        for fila in cursor.fetchall()
    ]

    if resultado != ["ok"]:

        errores.extend(
            f"SQLite integrity_check: {mensaje}"
            for mensaje in resultado
        )


def revisar_claves_foraneas(cursor, errores):

    cursor.execute("PRAGMA foreign_key_check")
    filas = cursor.fetchall()

    for tabla, fila_id, tabla_referencia, indice_fk in filas:

        errores.append(
            "Clave foranea rota: "
            f"{tabla} fila {fila_id} referencia {tabla_referencia} "
            f"(fk {indice_fk})."
        )


def revisar_schema_version(cursor, advertencias, info):

    if not tabla_existe(cursor, "schema_version"):

        advertencias.append(
            "No existe schema_version. Ejecuta la reparacion para migrar la base."
        )
        return

    cursor.execute("SELECT version FROM schema_version WHERE id=1")
    fila = cursor.fetchone()

    if not fila:

        advertencias.append(
            "schema_version existe pero no tiene version registrada."
        )
        return

    version = int(fila[0])
    info.append(f"Schema version: {version}.")

    if version != SCHEMA_VERSION_ACTUAL:

        advertencias.append(
            f"Schema version {version}; version esperada {SCHEMA_VERSION_ACTUAL}."
        )


def revisar_indices(cursor, advertencias, info):

    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='index'
    """)
    indices = {
        fila[0]
        for fila in cursor.fetchall()
    }
    faltantes = sorted(INDICES_ESPERADOS - indices)

    if faltantes:

        advertencias.append(
            "Faltan indices esperados: " + ", ".join(faltantes) + "."
        )

    else:

        info.append("Indices esperados presentes.")


def revisar_restaurantes_sin_ciudad(cursor, advertencias):

    if not tabla_existe(cursor, "restaurantes"):

        advertencias.append("No existe la tabla restaurantes.")
        return

    if not columna_existe(cursor, "restaurantes", "ciudad_id"):

        advertencias.append("La tabla restaurantes no tiene ciudad_id.")
        return

    cursor.execute("""
    SELECT COUNT(*)
    FROM restaurantes
    WHERE ciudad_id IS NULL
    """)
    total = cursor.fetchone()[0]

    if total:

        advertencias.append(
            f"{total} restaurantes antiguos no tienen ciudad asignada."
        )


def revisar_repartidores_horas_invalidas(cursor, advertencias):

    if not tabla_existe(cursor, "repartidores"):

        advertencias.append("No existe la tabla repartidores.")
        return

    cursor.execute("""
    SELECT id, nombre, horas
    FROM repartidores
    WHERE activo=1
    """)
    invalidos = [
        fila
        for fila in cursor.fetchall()
        if int(fila[2] or 0) not in HORAS_CONTRATO
    ]

    if invalidos:

        advertencias.append(
            "Repartidores con horas contratadas no validas: "
            + ", ".join(
                f"{nombre} ({horas}h)"
                for _, nombre, horas in invalidos
            )
            + "."
        )


def revisar_descansos_invalidos(cursor, advertencias):

    if not tabla_existe(cursor, "descansos"):

        advertencias.append("No existe la tabla descansos.")
        return

    if not tabla_existe(cursor, "repartidores"):

        advertencias.append("No se pueden validar descansos sin repartidores.")
        return

    cursor.execute("""
    SELECT r.nombre, d.dia_inicio, d.dia_fin
    FROM descansos d
    INNER JOIN repartidores r ON r.id=d.repartidor_id
    WHERE d.activo=1
    AND r.activo=1
    """)
    invalidos = [
        fila
        for fila in cursor.fetchall()
        if (fila[1], fila[2]) not in DESCANSOS_VALIDOS
    ]

    if invalidos:

        advertencias.append(
            "Descansos antiguos no validos: "
            + ", ".join(
                f"{nombre} ({inicio}-{fin})"
                for nombre, inicio, fin in invalidos
            )
            + "."
        )


def revisar_demandas_invalidas(cursor, advertencias):

    if not tabla_existe(cursor, "demanda_restaurante"):

        advertencias.append("No existe la tabla demanda_restaurante.")
        return

    cursor.execute("""
    SELECT id, fecha, dia_semana, repartidores_necesarios
    FROM demanda_restaurante
    WHERE activo=1
    """)
    invalidas = []

    for demanda_id, fecha, dia_semana, necesarios in cursor.fetchall():

        motivos = []
        fecha = (fecha or "").strip()
        dia_semana = (dia_semana or "").strip()

        if bool(fecha) == bool(dia_semana):

            motivos.append("usa fecha concreta o dia de semana, solo uno")

        if fecha and not fecha_valida(fecha):

            motivos.append("fecha no valida")

        if dia_semana and dia_semana not in DIAS_SEMANA:

            motivos.append("dia_semana no valido")

        if int(necesarios or 0) < 0:

            motivos.append("demanda negativa")

        if motivos:

            invalidas.append(f"#{demanda_id}: " + ", ".join(motivos))

    if invalidas:

        advertencias.append(
            "Demandas antiguas invalidas: " + "; ".join(invalidas) + "."
        )


def revisar_demandas_duplicadas(cursor, advertencias):

    if not tabla_existe(cursor, "demanda_restaurante"):

        return

    for columna, etiqueta in (("fecha", "fecha"), ("dia_semana", "dia")):

        cursor.execute(f"""
        SELECT restaurante_id, turno_restaurante_id, {columna}, COUNT(*)
        FROM demanda_restaurante
        WHERE activo=1
        AND {columna} IS NOT NULL
        GROUP BY restaurante_id, turno_restaurante_id, {columna}
        HAVING COUNT(*) > 1
        """)
        duplicadas = cursor.fetchall()

        if duplicadas:

            advertencias.append(
                "Demandas duplicadas por "
                + etiqueta
                + ": "
                + ", ".join(
                    f"restaurante {restaurante_id}, turno {turno_id}, "
                    f"{etiqueta} {periodo} ({total})"
                    for restaurante_id, turno_id, periodo, total in duplicadas
                )
                + "."
            )


def revisar_calendario_duplicado(cursor, advertencias):

    if not tabla_existe(cursor, "calendario_semanal"):

        advertencias.append("No existe la tabla calendario_semanal.")
        return

    cursor.execute("""
    SELECT fecha_inicio_semana, dia, turno_id, restaurante_id,
           COALESCE(repartidor_id, -1), COUNT(*)
    FROM calendario_semanal
    GROUP BY fecha_inicio_semana, dia, turno_id, restaurante_id,
             COALESCE(repartidor_id, -1)
    HAVING COUNT(*) > 1
    """)
    duplicados = cursor.fetchall()

    if duplicados:

        advertencias.append(
            "Asignaciones duplicadas en calendario: "
            + ", ".join(
                f"{semana} {dia} turno {turno_id} restaurante {restaurante_id}"
                f" ({total})"
                for semana, dia, turno_id, restaurante_id, _, total in duplicados
            )
            + "."
        )


def reparar_demandas_duplicadas(cursor):

    acciones = []

    for columna, etiqueta in (("fecha", "fecha"), ("dia_semana", "dia")):

        cursor.execute(f"""
        SELECT MIN(id), GROUP_CONCAT(id), COUNT(*)
        FROM demanda_restaurante
        WHERE activo=1
        AND {columna} IS NOT NULL
        GROUP BY restaurante_id, turno_restaurante_id, {columna}
        HAVING COUNT(*) > 1
        """)
        grupos = cursor.fetchall()

        for conservar_id, ids, total in grupos:

            cursor.execute(f"""
            UPDATE demanda_restaurante
            SET activo=0
            WHERE id IN ({ids})
            AND id<>?
            """,(conservar_id,))
            acciones.append(
                f"Desactivadas {total - 1} demandas duplicadas por {etiqueta}."
            )

    return acciones


def reparar_calendario_duplicado(cursor):

    cursor.execute("""
    SELECT COUNT(*)
    FROM calendario_semanal
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM calendario_semanal
        GROUP BY
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id,
            COALESCE(repartidor_id, -1)
    )
    """)
    total = cursor.fetchone()[0]

    if not total:

        return []

    cursor.execute("""
    DELETE FROM calendario_semanal
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM calendario_semanal
        GROUP BY
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id,
            COALESCE(repartidor_id, -1)
    )
    """)

    return [f"Eliminadas {total} asignaciones duplicadas exactas."]


def obtener_ciudad_sin_ciudad(cursor):

    cursor.execute("""
    INSERT OR IGNORE INTO ciudades(nombre, activo)
    VALUES(?,1)
    """,(CIUDAD_SIN_CIUDAD,))
    cursor.execute("""
    SELECT id
    FROM ciudades
    WHERE nombre=?
    """,(CIUDAD_SIN_CIUDAD,))

    return cursor.fetchone()[0]


def tabla_existe(cursor, tabla):

    cursor.execute("""
    SELECT 1
    FROM sqlite_master
    WHERE type='table'
    AND name=?
    """,(tabla,))

    return cursor.fetchone() is not None


def columna_existe(cursor, tabla, columna):

    cursor.execute(f"PRAGMA table_info({tabla})")

    return columna in {
        fila[1]
        for fila in cursor.fetchall()
    }


def fecha_valida(valor):

    try:

        datetime.strptime(valor, "%Y-%m-%d")
        return True

    except ValueError:

        return False
