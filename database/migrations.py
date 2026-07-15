from database.connection import conectar
from database.schema import (
    CIUDAD_SIN_CIUDAD,
    FECHA_INICIO_SEMANA_LEGADO,
    SCHEMA_VERSION_ACTUAL
)


def columnas_tabla(cursor, tabla):

    cursor.execute(f"PRAGMA table_info({tabla})")

    return [
        fila[1]
        for fila in cursor.fetchall()
    ]


def agregar_columna_si_no_existe(cursor, tabla, columna, definicion):

    columnas = columnas_tabla(cursor, tabla)

    if columna not in columnas:

        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


def crear_base_datos(ruta_bd=None):

    conexion = conectar(ruta_bd)

    try:

        cursor = conexion.cursor()
        crear_tabla_schema_version(cursor)
        crear_esquema_inicial(cursor)
        aplicar_migraciones(cursor)
        sembrar_datos_iniciales(cursor)
        guardar_schema_version(cursor)
        conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def crear_tabla_schema_version(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schema_version(

        id INTEGER PRIMARY KEY CHECK(id=1),

        version INTEGER NOT NULL,

        aplicado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def guardar_schema_version(cursor):

    cursor.execute("""
    INSERT INTO schema_version(id, version, aplicado_en)
    VALUES(1,?,CURRENT_TIMESTAMP)
    ON CONFLICT(id) DO UPDATE SET
        version=excluded.version,
        aplicado_en=CURRENT_TIMESTAMP
    WHERE schema_version.version <> excluded.version
    """,(SCHEMA_VERSION_ACTUAL,))


def crear_esquema_inicial(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ciudades(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL UNIQUE,

        activo INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repartidores(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL,

        horas INTEGER NOT NULL,

        zona TEXT,

        doble_turno INTEGER DEFAULT 1,

        puede_hasta_la_una INTEGER DEFAULT 1,

        prioridad_comida INTEGER DEFAULT 50,

        prioridad_noche INTEGER DEFAULT 50,

        prioridad_grela INTEGER DEFAULT 50,

        activo INTEGER DEFAULT 1,

        observaciones TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurantes(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL,

        direccion TEXT,

        zona TEXT,

        telefono TEXT,

        prioridad INTEGER DEFAULT 50,

        activo INTEGER DEFAULT 1,

        observaciones TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurante_repartidores(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        restaurante_id INTEGER NOT NULL,

        repartidor_id INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restaurante_turnos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        restaurante_id INTEGER NOT NULL,

        nombre TEXT NOT NULL,

        hora_inicio TEXT NOT NULL,

        hora_fin TEXT NOT NULL,

        cruza_medianoche INTEGER DEFAULT 0,

        duracion REAL NOT NULL,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demanda_restaurante(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        restaurante_id INTEGER NOT NULL,

        turno_restaurante_id INTEGER NOT NULL,

        fecha TEXT,

        dia_semana TEXT,

        repartidores_necesarios INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),

        FOREIGN KEY(turno_restaurante_id) REFERENCES restaurante_turnos(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demanda_zona(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        zona TEXT NOT NULL,

        turno_id INTEGER NOT NULL,

        fecha TEXT,

        dia_semana TEXT,

        repartidores_necesarios INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(turno_id) REFERENCES turnos(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS demanda_ciudad(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        ciudad_id INTEGER NOT NULL,

        turno_id INTEGER NOT NULL,

        fecha TEXT,

        dia_semana TEXT,

        repartidores_necesarios INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        FOREIGN KEY(ciudad_id) REFERENCES ciudades(id),

        FOREIGN KEY(turno_id) REFERENCES turnos(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repartidor_ciudades(

        repartidor_id INTEGER NOT NULL,

        ciudad_id INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        UNIQUE(repartidor_id, ciudad_id),

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id),

        FOREIGN KEY(ciudad_id) REFERENCES ciudades(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS repartidor_restaurantes_autorizados(

        repartidor_id INTEGER NOT NULL,

        restaurante_id INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        UNIQUE(repartidor_id, restaurante_id),

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id),

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS contratos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL,

        horas INTEGER NOT NULL,

        activo INTEGER DEFAULT 1,

        observaciones TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS descansos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        repartidor_id INTEGER NOT NULL,

        dia_inicio TEXT NOT NULL,

        dia_fin TEXT NOT NULL,

        activo INTEGER DEFAULT 1,

        observaciones TEXT,

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disponibilidad(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        repartidor_id INTEGER NOT NULL,

        dia TEXT NOT NULL,

        turno TEXT,

        disponible INTEGER DEFAULT 1,

        observaciones TEXT,

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vacaciones(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        repartidor_id INTEGER NOT NULL,

        fecha_inicio TEXT NOT NULL,

        fecha_fin TEXT NOT NULL,

        activo INTEGER DEFAULT 1,

        observaciones TEXT,

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bajas(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        repartidor_id INTEGER NOT NULL,

        fecha_inicio TEXT NOT NULL,

        fecha_fin TEXT,

        activa INTEGER DEFAULT 1,

        observaciones TEXT,

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preferencias(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        repartidor_id INTEGER NOT NULL,

        restaurante_id INTEGER,

        zona TEXT,

        turno TEXT,

        prioridad INTEGER DEFAULT 50,

        observaciones TEXT,

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id),

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS turnos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tipo TEXT NOT NULL,

        nombre TEXT NOT NULL,

        hora_inicio TEXT NOT NULL,

        hora_fin TEXT NOT NULL,

        color TEXT NOT NULL,

        duracion REAL NOT NULL,

        activo INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calendario_semanal(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        fecha_inicio_semana TEXT NOT NULL DEFAULT '1970-01-05',

        dia TEXT NOT NULL,

        turno_id INTEGER NOT NULL,

        restaurante_id INTEGER NOT NULL,

        repartidor_id INTEGER,

        FOREIGN KEY(turno_id) REFERENCES turnos(id),

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plantillas_semana(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL,

        descripcion TEXT,

        incluir_repartidores INTEGER DEFAULT 1,

        activo INTEGER DEFAULT 1,

        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS plantilla_semana_asignaciones(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        plantilla_id INTEGER NOT NULL,

        dia TEXT NOT NULL,

        turno_id INTEGER NOT NULL,

        restaurante_id INTEGER NOT NULL,

        repartidor_id INTEGER,

        FOREIGN KEY(plantilla_id) REFERENCES plantillas_semana(id),

        FOREIGN KEY(turno_id) REFERENCES turnos(id),

        FOREIGN KEY(restaurante_id) REFERENCES restaurantes(id),

        FOREIGN KEY(repartidor_id) REFERENCES repartidores(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integraciones_api(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proveedor TEXT NOT NULL UNIQUE,

        nombre TEXT NOT NULL,

        activo INTEGER DEFAULT 0,

        base_url TEXT,

        credenciales_referencia TEXT,

        opciones TEXT,

        fecha_actualizacion TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integraciones_eventos(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proveedor TEXT NOT NULL,

        tipo TEXT NOT NULL,

        estado TEXT NOT NULL,

        mensaje TEXT,

        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    crear_tabla_integraciones_sincronizaciones(cursor)
    crear_tabla_historial_acciones(cursor)
    crear_tabla_reglas_configuracion(cursor)


def crear_tabla_integraciones_sincronizaciones(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS integraciones_sincronizaciones(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proveedor TEXT NOT NULL,

        accion TEXT NOT NULL,

        estado TEXT NOT NULL,

        payload TEXT,

        respuesta TEXT,

        error TEXT,

        intentos INTEGER DEFAULT 0,

        max_reintentos INTEGER DEFAULT 3,

        proximo_intento TEXT,

        creado_en TEXT DEFAULT CURRENT_TIMESTAMP,

        actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def crear_tabla_historial_acciones(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial_acciones(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        accion TEXT NOT NULL,

        entidad TEXT,

        detalle TEXT,

        fecha_inicio_semana TEXT,

        creado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def crear_tabla_reglas_configuracion(cursor):

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reglas_configuracion(

        clave TEXT PRIMARY KEY,

        valor TEXT NOT NULL,

        activo INTEGER DEFAULT 1,

        actualizado_en TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)


def aplicar_migraciones(cursor):

    crear_tabla_integraciones_sincronizaciones(cursor)
    crear_tabla_historial_acciones(cursor)
    crear_tabla_reglas_configuracion(cursor)

    for columna, definicion in (
        ("ciudad_principal_id", "INTEGER"),
        ("restaurante_principal_id", "INTEGER"),
        ("apoyo_flexible", "INTEGER DEFAULT 0"),
        ("horas_complementarias", "INTEGER DEFAULT 0"),
        ("max_horas_diarias", "REAL DEFAULT 10"),
        ("max_dias_consecutivos", "INTEGER DEFAULT 5")
    ):

        agregar_columna_si_no_existe(
            cursor,
            "repartidores",
            columna,
            definicion
        )

    agregar_columna_si_no_existe(
        cursor,
        "restaurantes",
        "horario_comida",
        "TEXT"
    )

    agregar_columna_si_no_existe(
        cursor,
        "restaurantes",
        "horario_cena",
        "TEXT"
    )

    agregar_columna_si_no_existe(
        cursor,
        "restaurantes",
        "ciudad_id",
        "INTEGER"
    )

    cursor.execute("""
    INSERT OR IGNORE INTO ciudades(nombre, activo)
    VALUES(?,1)
    """,(CIUDAD_SIN_CIUDAD,))

    cursor.execute("""
    UPDATE restaurantes
    SET ciudad_id=(
        SELECT id
        FROM ciudades
        WHERE nombre=?
    )
    WHERE ciudad_id IS NULL
    """,(CIUDAD_SIN_CIUDAD,))

    reparar_datos_para_indices(cursor)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_restaurante_fecha_unica
    ON demanda_restaurante(
        restaurante_id,
        turno_restaurante_id,
        fecha
    )
    WHERE activo=1
    AND fecha IS NOT NULL
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_restaurante_dia_unico
    ON demanda_restaurante(
        restaurante_id,
        turno_restaurante_id,
        dia_semana
    )
    WHERE activo=1
    AND dia_semana IS NOT NULL
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_zona_fecha_unica
    ON demanda_zona(
        zona,
        turno_id,
        fecha
    )
    WHERE activo=1
    AND fecha IS NOT NULL
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_zona_dia_unico
    ON demanda_zona(
        zona,
        turno_id,
        dia_semana
    )
    WHERE activo=1
    AND dia_semana IS NOT NULL
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_ciudad_fecha_unica
    ON demanda_ciudad(
        ciudad_id,
        turno_id,
        fecha
    )
    WHERE activo=1
    AND fecha IS NOT NULL
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_demanda_ciudad_dia_unico
    ON demanda_ciudad(
        ciudad_id,
        turno_id,
        dia_semana
    )
    WHERE activo=1
    AND dia_semana IS NOT NULL
    """)

    agregar_columna_si_no_existe(
        cursor,
        "turnos",
        "turno_restaurante_id",
        "INTEGER"
    )

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_turnos_turno_restaurante_unico
    ON turnos(turno_restaurante_id)
    WHERE turno_restaurante_id IS NOT NULL
    """)

    agregar_columna_si_no_existe(
        cursor,
        "calendario_semanal",
        "repartidor_id",
        "INTEGER"
    )

    agregar_columna_si_no_existe(
        cursor,
        "calendario_semanal",
        "fecha_inicio_semana",
        "TEXT NOT NULL DEFAULT '1970-01-05'"
    )

    cursor.execute("""
    UPDATE calendario_semanal
    SET fecha_inicio_semana=?
    WHERE fecha_inicio_semana IS NULL
    OR TRIM(fecha_inicio_semana)=''
    """,(FECHA_INICIO_SEMANA_LEGADO,))

    reparar_datos_para_indices(cursor)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_calendario_semana_unico
    ON calendario_semanal(
        fecha_inicio_semana,
        dia,
        turno_id,
        restaurante_id,
        COALESCE(repartidor_id, -1)
    )
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_plantillas_semana_nombre_activo
    ON plantillas_semana(nombre)
    WHERE activo=1
    """)

    cursor.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_plantilla_asignaciones_unica
    ON plantilla_semana_asignaciones(
        plantilla_id,
        dia,
        turno_id,
        restaurante_id,
        COALESCE(repartidor_id, -1)
    )
    """)

    crear_indices_consulta(cursor)


def reparar_datos_para_indices(cursor):

    cursor.execute("""
    UPDATE demanda_restaurante
    SET activo=0
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM demanda_restaurante
        WHERE activo=1
        AND fecha IS NOT NULL
        GROUP BY restaurante_id, turno_restaurante_id, fecha
    )
    AND activo=1
    AND fecha IS NOT NULL
    """)

    cursor.execute("""
    UPDATE demanda_restaurante
    SET activo=0
    WHERE id NOT IN (
        SELECT MIN(id)
        FROM demanda_restaurante
        WHERE activo=1
        AND dia_semana IS NOT NULL
        GROUP BY restaurante_id, turno_restaurante_id, dia_semana
    )
    AND activo=1
    AND dia_semana IS NOT NULL
    """)

    if "demanda_zona" in tablas_base(cursor):

        cursor.execute("""
        UPDATE demanda_zona
        SET activo=0
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM demanda_zona
            WHERE activo=1
            AND fecha IS NOT NULL
            GROUP BY zona, turno_id, fecha
        )
        AND activo=1
        AND fecha IS NOT NULL
        """)

        cursor.execute("""
        UPDATE demanda_zona
        SET activo=0
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM demanda_zona
            WHERE activo=1
            AND dia_semana IS NOT NULL
            GROUP BY zona, turno_id, dia_semana
        )
        AND activo=1
        AND dia_semana IS NOT NULL
        """)

    if "demanda_ciudad" in tablas_base(cursor):

        cursor.execute("""
        UPDATE demanda_ciudad
        SET activo=0
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM demanda_ciudad
            WHERE activo=1
            AND fecha IS NOT NULL
            GROUP BY ciudad_id, turno_id, fecha
        )
        AND activo=1
        AND fecha IS NOT NULL
        """)

        cursor.execute("""
        UPDATE demanda_ciudad
        SET activo=0
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM demanda_ciudad
            WHERE activo=1
            AND dia_semana IS NOT NULL
            GROUP BY ciudad_id, turno_id, dia_semana
        )
        AND activo=1
        AND dia_semana IS NOT NULL
        """)

    if "fecha_inicio_semana" in columnas_tabla(cursor, "calendario_semanal"):

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


def tablas_base(cursor):

    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table'
    """)

    return {
        fila[0]
        for fila in cursor.fetchall()
    }


def crear_indices_consulta(cursor):

    for nombre, definicion in (
        (
            "idx_restaurantes_ciudad_id",
            "CREATE INDEX IF NOT EXISTS idx_restaurantes_ciudad_id "
            "ON restaurantes(ciudad_id)"
        ),
        (
            "idx_restaurante_turnos_restaurante",
            "CREATE INDEX IF NOT EXISTS idx_restaurante_turnos_restaurante "
            "ON restaurante_turnos(restaurante_id, activo)"
        ),
        (
            "idx_demanda_restaurante_lookup",
            "CREATE INDEX IF NOT EXISTS idx_demanda_restaurante_lookup "
            "ON demanda_restaurante(restaurante_id, turno_restaurante_id, activo)"
        ),
        (
            "idx_demanda_zona_lookup",
            "CREATE INDEX IF NOT EXISTS idx_demanda_zona_lookup "
            "ON demanda_zona(zona, turno_id, activo)"
        ),
        (
            "idx_demanda_ciudad_lookup",
            "CREATE INDEX IF NOT EXISTS idx_demanda_ciudad_lookup "
            "ON demanda_ciudad(ciudad_id, turno_id, activo)"
        ),
        (
            "idx_calendario_semana_lookup",
            "CREATE INDEX IF NOT EXISTS idx_calendario_semana_lookup "
            "ON calendario_semanal(fecha_inicio_semana, dia, turno_id)"
        ),
        (
            "idx_disponibilidad_repartidor",
            "CREATE INDEX IF NOT EXISTS idx_disponibilidad_repartidor "
            "ON disponibilidad(repartidor_id, dia, turno)"
        ),
        (
            "idx_descansos_repartidor_activo",
            "CREATE INDEX IF NOT EXISTS idx_descansos_repartidor_activo "
            "ON descansos(repartidor_id, activo)"
        ),
        (
            "idx_vacaciones_repartidor_activo",
            "CREATE INDEX IF NOT EXISTS idx_vacaciones_repartidor_activo "
            "ON vacaciones(repartidor_id, activo)"
        ),
        (
            "idx_bajas_repartidor_activa",
            "CREATE INDEX IF NOT EXISTS idx_bajas_repartidor_activa "
            "ON bajas(repartidor_id, activa)"
        ),
        (
            "idx_restaurante_repartidores_restaurante",
            "CREATE INDEX IF NOT EXISTS idx_restaurante_repartidores_restaurante "
            "ON restaurante_repartidores(restaurante_id, repartidor_id, activo)"
        ),
        (
            "idx_historial_acciones_creado_en",
            "CREATE INDEX IF NOT EXISTS idx_historial_acciones_creado_en "
            "ON historial_acciones(creado_en)"
        ),
        (
            "idx_historial_acciones_semana",
            "CREATE INDEX IF NOT EXISTS idx_historial_acciones_semana "
            "ON historial_acciones(fecha_inicio_semana)"
        ),
        (
            "idx_reglas_configuracion_activo",
            "CREATE INDEX IF NOT EXISTS idx_reglas_configuracion_activo "
            "ON reglas_configuracion(activo)"
        ),
        (
            "idx_integraciones_sincronizaciones_estado",
            "CREATE INDEX IF NOT EXISTS "
            "idx_integraciones_sincronizaciones_estado "
            "ON integraciones_sincronizaciones("
            "estado, proximo_intento, proveedor)"
        )
    ):

        cursor.execute(definicion)


def sembrar_datos_iniciales(cursor):

    for proveedor, nombre in (
        ("email", "Email"),
        ("shipday", "Shipday"),
        ("glovo", "Glovo"),
        ("uber", "Uber"),
        ("api_generica", "API generica")
    ):

        cursor.execute("""
        INSERT OR IGNORE INTO integraciones_api(
            proveedor,
            nombre,
            activo
        )
        VALUES(?,?,0)
        """,(
            proveedor,
            nombre
        ))
