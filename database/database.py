import sqlite3
from datetime import date, datetime, timedelta

from utils.paths import BASE_DIR, database_path, ensure_user_directories

RUTA_BD = database_path()
FECHA_INICIO_SEMANA_LEGADO = "1970-01-05"
HORAS_CONTRATO = (10, 20, 25, 30, 35, 40)
DIAS_SEMANA = (
    "lunes",
    "martes",
    "miercoles",
    "jueves",
    "viernes",
    "sabado",
    "domingo"
)
DESCANSOS_VALIDOS = (
    ("lunes", "martes"),
    ("martes", "miercoles"),
    ("miercoles", "jueves"),
    ("jueves", "viernes")
)
DIAS_INICIO_DESCANSO = tuple(
    descanso[0]
    for descanso in DESCANSOS_VALIDOS
)
TURNOS_DISPONIBILIDAD = (
    "comida",
    "noche"
)
OPCIONES_DISPONIBILIDAD = (
    "Comidas",
    "Cenas",
    "Ambos",
    "No disponible"
)
TIPOS_TURNO = (
    "Comida",
    "Cena",
    "Turno partido",
    "Personalizado"
)
PROVEEDORES_INTEGRACION = (
    "shipday",
    "glovo",
    "uber",
    "api_generica"
)
CIUDAD_SIN_CIUDAD = "Sin ciudad"


def conectar():

    ensure_user_directories()

    return sqlite3.connect(RUTA_BD)


def agregar_columna_si_no_existe(cursor, tabla, columna, definicion):

    columnas = columnas_tabla(cursor, tabla)

    if columna not in columnas:

        cursor.execute(
            f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}"
        )


def columnas_tabla(cursor, tabla):

    cursor.execute(f"PRAGMA table_info({tabla})")

    return [
        fila[1]
        for fila in cursor.fetchall()
    ]


def normalizar_fecha_inicio_semana(fecha_inicio_semana=None):

    if fecha_inicio_semana is None:

        return FECHA_INICIO_SEMANA_LEGADO

    if isinstance(fecha_inicio_semana, datetime):

        fecha = fecha_inicio_semana.date()

    elif isinstance(fecha_inicio_semana, date):

        fecha = fecha_inicio_semana

    else:

        fecha = datetime.strptime(
            str(fecha_inicio_semana),
            "%Y-%m-%d"
        ).date()

    inicio = fecha - timedelta(days=fecha.weekday())

    return inicio.isoformat()


def crear_base_datos():

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ciudades(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nombre TEXT NOT NULL UNIQUE,

        activo INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO ciudades(nombre, activo)
    VALUES(?,1)
    """,(CIUDAD_SIN_CIUDAD,))

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
    UPDATE restaurantes
    SET ciudad_id=(
        SELECT id
        FROM ciudades
        WHERE nombre=?
    )
    WHERE ciudad_id IS NULL
    """,(CIUDAD_SIN_CIUDAD,))

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

    for proveedor, nombre in (
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

    conexion.commit()
    conexion.close()


def validar_horas_contratadas(horas):

    horas = int(horas)

    if horas not in HORAS_CONTRATO:

        raise ValueError("Horas contratadas no validas.")

    return horas


def validar_descanso(dia_inicio, dia_fin):

    if not descanso_es_valido(dia_inicio, dia_fin):

        raise ValueError(
            "Descanso no valido. Solo se permiten lunes-martes, "
            "martes-miercoles, miercoles-jueves o jueves-viernes."
        )

    return dia_inicio, dia_fin


def descanso_es_valido(dia_inicio, dia_fin):

    return (dia_inicio, dia_fin) in DESCANSOS_VALIDOS


def siguiente_descanso_valido(dia_inicio):

    for inicio, fin in DESCANSOS_VALIDOS:

        if inicio == dia_inicio:

            return fin

    return DESCANSOS_VALIDOS[0][1]


def obtener_descansos_invalidos():

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        r.id,
        r.nombre,
        d.dia_inicio,
        d.dia_fin
    FROM descansos d
    INNER JOIN repartidores r
        ON r.id=d.repartidor_id
    WHERE d.activo=1
    AND r.activo=1
    """)

    datos = [
        fila
        for fila in cursor.fetchall()
        if not descanso_es_valido(fila[2], fila[3])
    ]

    conexion.close()

    return datos


def insertar_descanso(repartidor_id, dia_inicio, dia_fin):

    dia_inicio, dia_fin = validar_descanso(dia_inicio, dia_fin)

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE descansos
    SET activo=0
    WHERE repartidor_id=?
    """,(repartidor_id,))

    cursor.execute("""
    INSERT INTO descansos(
        repartidor_id,
        dia_inicio,
        dia_fin
    )
    VALUES(?,?,?)
    """,(
        repartidor_id,
        dia_inicio,
        dia_fin
    ))

    conexion.commit()
    conexion.close()


def desactivar_descanso(repartidor_id):

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE descansos
    SET activo=0
    WHERE repartidor_id=?
    """,(repartidor_id,))

    conexion.commit()
    conexion.close()


def validar_disponibilidad(disponibilidad):

    disponibilidad = disponibilidad or {}

    for dia, opcion in disponibilidad.items():

        if dia not in DIAS_SEMANA:

            raise ValueError("Dia de disponibilidad no valido.")

        if opcion not in OPCIONES_DISPONIBILIDAD:

            raise ValueError("Disponibilidad no valida.")

    return disponibilidad


def insertar_disponibilidad(repartidor_id, disponibilidad):

    disponibilidad = validar_disponibilidad(disponibilidad)

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    DELETE FROM disponibilidad
    WHERE repartidor_id=?
    """,(repartidor_id,))

    for dia in DIAS_SEMANA:

        opcion = disponibilidad.get(dia, "Ambos")

        turnos_disponibles = []

        if opcion == "Comidas":

            turnos_disponibles = ["comida"]

        elif opcion == "Cenas":

            turnos_disponibles = ["noche"]

        elif opcion == "Ambos":

            turnos_disponibles = ["comida", "noche"]

        for turno in TURNOS_DISPONIBILIDAD:

            cursor.execute("""
            INSERT INTO disponibilidad(
                repartidor_id,
                dia,
                turno,
                disponible
            )
            VALUES(?,?,?,?)
            """,(
                repartidor_id,
                dia,
                turno,
                int(turno in turnos_disponibles)
            ))

    conexion.commit()
    conexion.close()


def obtener_id_ciudad_sin_ciudad():

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT id
    FROM ciudades
    WHERE nombre=?
    """,(CIUDAD_SIN_CIUDAD,))
    ciudad = cursor.fetchone()
    conexion.close()

    return ciudad[0]


def obtener_ciudades(solo_activas=False):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    consulta = """
    SELECT id, nombre, activo
    FROM ciudades
    """

    if solo_activas:

        consulta += " WHERE activo=1"

    consulta += " ORDER BY activo DESC, nombre"
    cursor.execute(consulta)
    datos = cursor.fetchall()
    conexion.close()

    return datos


def obtener_ciudad(id_ciudad):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT id, nombre, activo
    FROM ciudades
    WHERE id=?
    """,(id_ciudad,))
    ciudad = cursor.fetchone()
    conexion.close()

    return ciudad


def insertar_ciudad(nombre, activo=1):

    nombre = nombre.strip()

    if not nombre:

        raise ValueError("Introduce una ciudad.")

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    INSERT INTO ciudades(nombre, activo)
    VALUES(?,?)
    """,(nombre, activo))
    conexion.commit()
    id_ciudad = cursor.lastrowid
    conexion.close()

    return id_ciudad


def actualizar_ciudad(id_ciudad, nombre, activo=1):

    nombre = nombre.strip()

    if not nombre:

        raise ValueError("Introduce una ciudad.")

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    UPDATE ciudades
    SET nombre=?,
        activo=?
    WHERE id=?
    """,(nombre, activo, id_ciudad))
    conexion.commit()
    conexion.close()


def obtener_restaurante_turnos(restaurante_id):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT
        id,
        restaurante_id,
        nombre,
        hora_inicio,
        hora_fin,
        cruza_medianoche,
        duracion,
        activo
    FROM restaurante_turnos
    WHERE restaurante_id=?
    ORDER BY activo DESC, nombre
    """,(restaurante_id,))
    datos = cursor.fetchall()
    conexion.close()

    return datos


def guardar_restaurante_turnos(restaurante_id, turnos):

    turnos = turnos or []
    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    UPDATE restaurante_turnos
    SET activo=0
    WHERE restaurante_id=?
    """,(restaurante_id,))

    for turno in turnos:

        turno_id = turno.get("id")
        datos = (
            restaurante_id,
            turno["nombre"],
            turno["hora_inicio"],
            turno["hora_fin"],
            int(turno.get("cruza_medianoche", 0)),
            float(turno["duracion"]),
            int(turno.get("activo", 1))
        )

        if turno_id:

            cursor.execute("""
            UPDATE restaurante_turnos
            SET restaurante_id=?,
                nombre=?,
                hora_inicio=?,
                hora_fin=?,
                cruza_medianoche=?,
                duracion=?,
                activo=?
            WHERE id=?
            """, datos + (turno_id,))

        else:

            cursor.execute("""
            INSERT INTO restaurante_turnos(
                restaurante_id,
                nombre,
                hora_inicio,
                hora_fin,
                cruza_medianoche,
                duracion,
                activo
            )
            VALUES(?,?,?,?,?,?,?)
            """, datos)

    conexion.commit()
    conexion.close()


def obtener_demanda_restaurante(restaurante_id):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT
        id,
        restaurante_id,
        turno_restaurante_id,
        fecha,
        dia_semana,
        repartidores_necesarios,
        activo
    FROM demanda_restaurante
    WHERE restaurante_id=?
    ORDER BY activo DESC, COALESCE(fecha, ''), COALESCE(dia_semana, '')
    """,(restaurante_id,))
    datos = cursor.fetchall()
    conexion.close()

    return datos


def guardar_demanda_restaurante(restaurante_id, demandas):

    demandas = demandas or []
    demandas = validar_demandas_restaurante(demandas)
    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    UPDATE demanda_restaurante
    SET activo=0
    WHERE restaurante_id=?
    """,(restaurante_id,))

    for demanda in demandas:

        demanda_id = demanda.get("id")
        datos = (
            restaurante_id,
            demanda["turno_restaurante_id"],
            demanda.get("fecha") or None,
            demanda.get("dia_semana") or None,
            int(demanda["repartidores_necesarios"]),
            int(demanda.get("activo", 1))
        )

        if demanda_id:

            cursor.execute("""
            UPDATE demanda_restaurante
            SET restaurante_id=?,
                turno_restaurante_id=?,
                fecha=?,
                dia_semana=?,
                repartidores_necesarios=?,
                activo=?
            WHERE id=?
            """, datos + (demanda_id,))

        else:

            cursor.execute("""
            INSERT INTO demanda_restaurante(
                restaurante_id,
                turno_restaurante_id,
                fecha,
                dia_semana,
                repartidores_necesarios,
                activo
            )
            VALUES(?,?,?,?,?,?)
            """, datos)

    conexion.commit()
    conexion.close()


def validar_demandas_restaurante(demandas):

    resultado = []
    claves = set()

    for demanda in demandas:

        demanda = dict(demanda)
        fecha = (demanda.get("fecha") or "").strip()
        dia_semana = (demanda.get("dia_semana") or "").strip()

        if bool(fecha) == bool(dia_semana):

            raise ValueError(
                "Configura una fecha concreta o un dia de semana, solo uno."
            )

        if dia_semana and dia_semana not in DIAS_SEMANA:

            raise ValueError("Dia de semana no valido.")

        if fecha:

            try:

                datetime.strptime(fecha, "%Y-%m-%d")

            except ValueError as error:

                raise ValueError("Fecha de demanda no valida.") from error

        necesarios = int(demanda["repartidores_necesarios"])

        if necesarios <= 0:

            raise ValueError("La demanda debe ser mayor que cero.")

        clave = (
            int(demanda["turno_restaurante_id"]),
            "fecha" if fecha else "dia",
            fecha or dia_semana
        )

        if clave in claves:

            raise ValueError("Demanda duplicada para el mismo turno y periodo.")

        claves.add(clave)
        demanda["fecha"] = fecha or None
        demanda["dia_semana"] = dia_semana or None
        demanda["repartidores_necesarios"] = necesarios
        resultado.append(demanda)

    return resultado


def guardar_repartidor_ciudades(repartidor_id, ciudades):

    ciudades = ciudades or []
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    UPDATE repartidor_ciudades
    SET activo=0
    WHERE repartidor_id=?
    """,(repartidor_id,))

    for ciudad_id in ciudades:

        cursor.execute("""
        INSERT INTO repartidor_ciudades(
            repartidor_id,
            ciudad_id,
            activo
        )
        VALUES(?,?,1)
        ON CONFLICT(repartidor_id, ciudad_id) DO UPDATE SET
            activo=1
        """,(repartidor_id, ciudad_id))

    conexion.commit()
    conexion.close()


def obtener_repartidor_ciudades(repartidor_id):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT ciudad_id
    FROM repartidor_ciudades
    WHERE repartidor_id=?
    AND activo=1
    """,(repartidor_id,))
    datos = [fila[0] for fila in cursor.fetchall()]
    conexion.close()

    return datos


def guardar_repartidor_restaurantes_autorizados(repartidor_id, restaurantes):

    restaurantes = restaurantes or []
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    UPDATE repartidor_restaurantes_autorizados
    SET activo=0
    WHERE repartidor_id=?
    """,(repartidor_id,))

    for restaurante_id in restaurantes:

        cursor.execute("""
        INSERT INTO repartidor_restaurantes_autorizados(
            repartidor_id,
            restaurante_id,
            activo
        )
        VALUES(?,?,1)
        ON CONFLICT(repartidor_id, restaurante_id) DO UPDATE SET
            activo=1
        """,(repartidor_id, restaurante_id))

    conexion.commit()
    conexion.close()


def obtener_repartidor_restaurantes_autorizados(repartidor_id):

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT restaurante_id
    FROM repartidor_restaurantes_autorizados
    WHERE repartidor_id=?
    AND activo=1
    """,(repartidor_id,))
    datos = [fila[0] for fila in cursor.fetchall()]
    conexion.close()

    return datos


def obtener_repartidores():

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        r.id,
        r.nombre,
        r.horas,
        r.zona,
        r.doble_turno,
        r.puede_hasta_la_una,
        r.prioridad_comida,
        r.prioridad_noche,
        r.prioridad_grela,
        d.dia_inicio,
        d.dia_fin
    FROM repartidores r
    LEFT JOIN descansos d
        ON d.repartidor_id=r.id
        AND d.activo=1
    WHERE r.activo=1
    ORDER BY r.nombre
    """)

    datos = []

    for repartidor in cursor.fetchall():

        cursor.execute("""
        SELECT
            dia,
            turno,
            disponible
        FROM disponibilidad
        WHERE repartidor_id=?
        """,(repartidor[0],))

        disponibilidad = {}

        for dia, turno, disponible in cursor.fetchall():

            disponibilidad.setdefault(dia, [])

            if disponible:

                disponibilidad[dia].append(turno)

        cursor.execute("""
        SELECT
            fecha_inicio,
            fecha_fin
        FROM vacaciones
        WHERE repartidor_id=?
        AND activo=1
        """,(repartidor[0],))

        vacaciones = [
            {
                "fecha_inicio": fila[0],
                "fecha_fin": fila[1]
            }
            for fila in cursor.fetchall()
        ]

        cursor.execute("""
        SELECT
            fecha_inicio,
            fecha_fin
        FROM bajas
        WHERE repartidor_id=?
        AND activa=1
        """,(repartidor[0],))

        bajas = [
            {
                "fecha_inicio": fila[0],
                "fecha_fin": fila[1]
            }
            for fila in cursor.fetchall()
        ]

        cursor.execute("""
        SELECT
            restaurante_id,
            zona,
            turno,
            prioridad
        FROM preferencias
        WHERE repartidor_id=?
        """,(repartidor[0],))

        preferencias = [
            {
                "restaurante_id": fila[0],
                "zona": fila[1],
                "turno": fila[2],
                "prioridad": fila[3]
            }
            for fila in cursor.fetchall()
        ]

        datos.append(
            repartidor + (
                disponibilidad,
                vacaciones,
                bajas,
                preferencias
            )
        )

    conexion.close()

    return datos


def obtener_repartidor(id_repartidor):

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        r.id,
        r.nombre,
        r.horas,
        r.zona,
        r.doble_turno,
        r.puede_hasta_la_una,
        r.prioridad_comida,
        r.prioridad_noche,
        r.prioridad_grela,
        r.observaciones,
        r.ciudad_principal_id,
        r.restaurante_principal_id,
        r.apoyo_flexible,
        r.horas_complementarias,
        r.max_horas_diarias,
        r.max_dias_consecutivos,
        d.dia_inicio,
        d.dia_fin
    FROM repartidores r
    LEFT JOIN descansos d
        ON d.repartidor_id=r.id
        AND d.activo=1
    WHERE r.id=?
    """,(id_repartidor,))

    fila = cursor.fetchone()

    if not fila:

        conexion.close()
        return None

    cursor.execute("""
    SELECT
        dia,
        turno,
        disponible
    FROM disponibilidad
    WHERE repartidor_id=?
    """,(id_repartidor,))

    disponibilidad = {}

    for dia, turno, disponible in cursor.fetchall():

        disponibilidad.setdefault(dia, [])

        if disponible:

            disponibilidad[dia].append(turno)

    conexion.close()

    return {
        "id": fila[0],
        "nombre": fila[1],
        "horas": fila[2],
        "zona": fila[3],
        "doble_turno": fila[4],
        "puede_hasta_la_una": fila[5],
        "prioridad_comida": fila[6],
        "prioridad_noche": fila[7],
        "prioridad_grela": fila[8],
        "observaciones": fila[9] or "",
        "ciudad_principal_id": fila[10],
        "restaurante_principal_id": fila[11],
        "apoyo_flexible": fila[12],
        "horas_complementarias": fila[13],
        "max_horas_diarias": fila[14],
        "max_dias_consecutivos": fila[15],
        "descanso_inicio": fila[16],
        "descanso_fin": fila[17],
        "disponibilidad": disponibilidad,
        "ciudades_autorizadas": obtener_repartidor_ciudades(id_repartidor),
        "restaurantes_autorizados": obtener_repartidor_restaurantes_autorizados(
            id_repartidor
        )
    }


def insertar_repartidor(
    nombre,
    horas,
    zona,
    doble_turno,
    puede_hasta_la_una,
    prioridad_comida,
    prioridad_noche,
    prioridad_grela,
    observaciones="",
    descanso_inicio=None,
    descanso_fin=None,
    disponibilidad=None,
    ciudad_principal_id=None,
    restaurante_principal_id=None,
    apoyo_flexible=0,
    horas_complementarias=0,
    max_horas_diarias=10,
    max_dias_consecutivos=5,
    ciudades_autorizadas=None,
    restaurantes_autorizados=None
):

    horas = validar_horas_contratadas(horas)

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO repartidores (
            nombre,
            horas,
            zona,
            doble_turno,
            puede_hasta_la_una,
            prioridad_comida,
            prioridad_noche,
            prioridad_grela,
            observaciones,
            ciudad_principal_id,
            restaurante_principal_id,
            apoyo_flexible,
            horas_complementarias,
            max_horas_diarias,
            max_dias_consecutivos
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        nombre,
        horas,
        zona,
        doble_turno,
        puede_hasta_la_una,
        prioridad_comida,
        prioridad_noche,
        prioridad_grela,
        observaciones,
        ciudad_principal_id,
        restaurante_principal_id,
        int(apoyo_flexible),
        int(horas_complementarias or 0),
        float(max_horas_diarias or 0),
        int(max_dias_consecutivos or 0)
    ))

    conexion.commit()
    id_repartidor = cursor.lastrowid
    conexion.close()

    if descanso_inicio and descanso_fin:

        insertar_descanso(
            id_repartidor,
            descanso_inicio,
            descanso_fin
        )

    else:

        desactivar_descanso(id_repartidor)

    if disponibilidad is not None:

        insertar_disponibilidad(
            id_repartidor,
            disponibilidad
        )

    guardar_repartidor_ciudades(
        id_repartidor,
        ciudades_autorizadas
    )
    guardar_repartidor_restaurantes_autorizados(
        id_repartidor,
        restaurantes_autorizados
    )

    return id_repartidor


def actualizar_repartidor(
    id_repartidor,
    nombre,
    horas,
    zona,
    doble_turno,
    puede_hasta_la_una,
    prioridad_comida,
    prioridad_noche,
    prioridad_grela,
    observaciones="",
    descanso_inicio=None,
    descanso_fin=None,
    disponibilidad=None,
    ciudad_principal_id=None,
    restaurante_principal_id=None,
    apoyo_flexible=0,
    horas_complementarias=0,
    max_horas_diarias=10,
    max_dias_consecutivos=5,
    ciudades_autorizadas=None,
    restaurantes_autorizados=None
):

    horas = validar_horas_contratadas(horas)

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE repartidores
    SET
        nombre=?,
        horas=?,
        zona=?,
        doble_turno=?,
        puede_hasta_la_una=?,
        prioridad_comida=?,
        prioridad_noche=?,
        prioridad_grela=?,
        observaciones=?,
        ciudad_principal_id=?,
        restaurante_principal_id=?,
        apoyo_flexible=?,
        horas_complementarias=?,
        max_horas_diarias=?,
        max_dias_consecutivos=?
    WHERE id=?
    """,(
        nombre,
        horas,
        zona,
        doble_turno,
        puede_hasta_la_una,
        prioridad_comida,
        prioridad_noche,
        prioridad_grela,
        observaciones,
        ciudad_principal_id,
        restaurante_principal_id,
        int(apoyo_flexible),
        int(horas_complementarias or 0),
        float(max_horas_diarias or 0),
        int(max_dias_consecutivos or 0),
        id_repartidor
    ))

    conexion.commit()
    conexion.close()

    if descanso_inicio and descanso_fin:

        insertar_descanso(
            id_repartidor,
            descanso_inicio,
            descanso_fin
        )

    else:

        desactivar_descanso(id_repartidor)

    if disponibilidad is not None:

        insertar_disponibilidad(
            id_repartidor,
            disponibilidad
        )

    guardar_repartidor_ciudades(
        id_repartidor,
        ciudades_autorizadas
    )
    guardar_repartidor_restaurantes_autorizados(
        id_repartidor,
        restaurantes_autorizados
    )


def eliminar_repartidor(id_repartidor):

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""

    UPDATE repartidores

    SET activo=0

    WHERE id=?

    """,(id_repartidor,))

    cursor.execute("""

    UPDATE descansos

    SET activo=0

    WHERE repartidor_id=?

    """,(id_repartidor,))

    conexion.commit()

    conexion.close()


def obtener_restaurantes():

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        id,
        nombre,
        direccion,
        zona,
        telefono,
        prioridad,
        activo,
        horario_comida,
        horario_cena,
        ciudad_id,
        (
            SELECT nombre
            FROM ciudades
            WHERE ciudades.id=restaurantes.ciudad_id
        ) AS ciudad
    FROM restaurantes
    ORDER BY activo DESC, ciudad, nombre
    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


def obtener_restaurante(id_restaurante):

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        id,
        nombre,
        direccion,
        zona,
        telefono,
        prioridad,
        activo,
        horario_comida,
        horario_cena,
        ciudad_id,
        (
            SELECT nombre
            FROM ciudades
            WHERE ciudades.id=restaurantes.ciudad_id
        ) AS ciudad
    FROM restaurantes
    WHERE id=?
    """,(id_restaurante,))

    restaurante = cursor.fetchone()

    conexion.close()

    return restaurante


def obtener_repartidores_fijos(id_restaurante):

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT repartidor_id
    FROM restaurante_repartidores
    WHERE restaurante_id=?
    AND activo=1
    """,(id_restaurante,))

    datos = [
        fila[0]
        for fila in cursor.fetchall()
    ]

    conexion.close()

    return datos


def guardar_repartidores_fijos(id_restaurante, repartidores_fijos):

    repartidores_fijos = repartidores_fijos or []

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE restaurante_repartidores
    SET activo=0
    WHERE restaurante_id=?
    """,(id_restaurante,))

    for id_repartidor in repartidores_fijos:

        cursor.execute("""
        INSERT INTO restaurante_repartidores(
            restaurante_id,
            repartidor_id,
            activo
        )
        VALUES(?,?,1)
        """,(
            id_restaurante,
            id_repartidor
        ))

    conexion.commit()
    conexion.close()


def insertar_restaurante(
    nombre,
    direccion,
    zona,
    telefono,
    prioridad,
    observaciones="",
    activo=1,
    horario_comida="",
    horario_cena="",
    repartidores_fijos=None,
    ciudad_id=None
):

    crear_base_datos()
    ciudad_id = ciudad_id or obtener_id_ciudad_sin_ciudad()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    INSERT INTO restaurantes(

        nombre,
        direccion,
        zona,
        telefono,
        prioridad,
        activo,
        horario_comida,
        horario_cena,
        ciudad_id,
        observaciones

    )

    VALUES(?,?,?,?,?,?,?,?,?,?)

    """,(

        nombre,
        direccion,
        zona,
        telefono,
        prioridad,
        activo,
        horario_comida,
        horario_cena,
        ciudad_id,
        observaciones

    ))

    conexion.commit()
    id_restaurante = cursor.lastrowid

    conexion.close()

    guardar_repartidores_fijos(
        id_restaurante,
        repartidores_fijos
    )

    return id_restaurante


def actualizar_restaurante(
    id_restaurante,
    nombre,
    direccion,
    zona,
    telefono,
    activo,
    horario_comida,
    horario_cena,
    repartidores_fijos=None,
    ciudad_id=None
):

    crear_base_datos()
    ciudad_id = ciudad_id or obtener_id_ciudad_sin_ciudad()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE restaurantes
    SET
        nombre=?,
        direccion=?,
        zona=?,
        telefono=?,
        activo=?,
        horario_comida=?,
        horario_cena=?,
        ciudad_id=?
    WHERE id=?
    """,(
        nombre,
        direccion,
        zona,
        telefono,
        activo,
        horario_comida,
        horario_cena,
        ciudad_id,
        id_restaurante
    ))

    conexion.commit()
    conexion.close()

    guardar_repartidores_fijos(
        id_restaurante,
        repartidores_fijos
    )


def eliminar_restaurante(id_restaurante):

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""

    UPDATE restaurantes

    SET activo=0

    WHERE id=?

    """,(id_restaurante,))

    cursor.execute("""

    UPDATE restaurante_repartidores

    SET activo=0

    WHERE restaurante_id=?

    """,(id_restaurante,))

    conexion.commit()

    conexion.close()


def validar_turno(tipo, nombre, hora_inicio, hora_fin, color, duracion):

    if tipo not in TIPOS_TURNO:

        raise ValueError("Tipo de turno no valido.")

    if nombre.strip() == "":

        raise ValueError("Introduce un nombre.")

    if hora_inicio.strip() == "" or hora_fin.strip() == "":

        raise ValueError("Introduce hora de inicio y fin.")

    if color.strip() == "":

        raise ValueError("Introduce un color.")

    duracion = float(duracion)

    if duracion <= 0:

        raise ValueError("La duracion debe ser mayor que cero.")

    return duracion


def obtener_turnos():

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        id,
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion,
        activo
    FROM turnos
    ORDER BY activo DESC, nombre
    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


def obtener_turno(id_turno):

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        id,
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion,
        activo
    FROM turnos
    WHERE id=?
    """,(id_turno,))

    turno = cursor.fetchone()

    conexion.close()

    return turno


def insertar_turno(
    tipo,
    nombre,
    hora_inicio,
    hora_fin,
    color,
    duracion,
    activo=1
):

    duracion = validar_turno(
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion
    )

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    INSERT INTO turnos(
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion,
        activo
    )
    VALUES(?,?,?,?,?,?,?)
    """,(
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion,
        activo
    ))

    conexion.commit()
    conexion.close()


def actualizar_turno(
    id_turno,
    tipo,
    nombre,
    hora_inicio,
    hora_fin,
    color,
    duracion,
    activo=1
):

    duracion = validar_turno(
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion
    )

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE turnos
    SET
        tipo=?,
        nombre=?,
        hora_inicio=?,
        hora_fin=?,
        color=?,
        duracion=?,
        activo=?
    WHERE id=?
    """,(
        tipo,
        nombre,
        hora_inicio,
        hora_fin,
        color,
        duracion,
        activo,
        id_turno
    ))

    conexion.commit()
    conexion.close()


def eliminar_turno(id_turno):

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    UPDATE turnos
    SET activo=0
    WHERE id=?
    """,(id_turno,))

    conexion.commit()
    conexion.close()


def obtener_calendario_semanal(fecha_inicio_semana=None):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        c.id,
        c.dia,
        c.turno_id,
        t.nombre,
        t.tipo,
        t.color,
        c.restaurante_id,
        r.nombre,
        r.zona,
        c.repartidor_id,
        rep.nombre,
        c.fecha_inicio_semana
    FROM calendario_semanal c
    INNER JOIN turnos t
        ON t.id=c.turno_id
    INNER JOIN restaurantes r
        ON r.id=c.restaurante_id
    LEFT JOIN repartidores rep
        ON rep.id=c.repartidor_id
    WHERE c.fecha_inicio_semana=?
    """,
        (fecha_inicio_semana,)
    )

    datos = cursor.fetchall()

    conexion.close()

    return datos


def guardar_turno_calendario(
    dia,
    turno_id,
    restaurante_id,
    repartidor_id=None,
    fecha_inicio_semana=None
):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )

    conexion = conectar()

    cursor = conexion.cursor()

    if restaurante_id:

        cursor.execute("""
        SELECT id
        FROM calendario_semanal
        WHERE fecha_inicio_semana=?
        AND dia=?
        AND turno_id=?
        AND restaurante_id=?
        AND (
            (repartidor_id IS NULL AND ? IS NULL)
            OR repartidor_id=?
        )
        """,(
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id,
            repartidor_id,
            repartidor_id
        ))

        existente = cursor.fetchone()

        if existente:

            cursor.execute("""
            UPDATE calendario_semanal
            SET repartidor_id=?
            WHERE id=?
            """,(
                repartidor_id,
                existente[0]
            ))

        else:

            cursor.execute("""
            INSERT INTO calendario_semanal(
                fecha_inicio_semana,
                dia,
                turno_id,
                restaurante_id,
                repartidor_id
            )
            VALUES(?,?,?,?,?)
            """,(
                fecha_inicio_semana,
                dia,
                turno_id,
                restaurante_id,
                repartidor_id
            ))

    conexion.commit()
    conexion.close()


def eliminar_turno_calendario(
    dia,
    turno_id,
    restaurante_id=None,
    fecha_inicio_semana=None
):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )

    conexion = conectar()

    cursor = conexion.cursor()

    if restaurante_id:

        cursor.execute("""
        DELETE FROM calendario_semanal
        WHERE fecha_inicio_semana=?
        AND dia=?
        AND turno_id=?
        AND restaurante_id=?
        """,(
            fecha_inicio_semana,
            dia,
            turno_id,
            restaurante_id
        ))

    else:

        cursor.execute("""
        DELETE FROM calendario_semanal
        WHERE fecha_inicio_semana=?
        AND dia=?
        AND turno_id=?
        """,(
            fecha_inicio_semana,
            dia,
            turno_id
        ))

    conexion.commit()
    conexion.close()


def eliminar_calendario_semana(fecha_inicio_semana):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )
    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
    DELETE FROM calendario_semanal
    WHERE fecha_inicio_semana=?
    """,(fecha_inicio_semana,))

    conexion.commit()
    conexion.close()


def semana_tiene_calendario(fecha_inicio_semana):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT 1
    FROM calendario_semanal
    WHERE fecha_inicio_semana=?
    LIMIT 1
    """,(fecha_inicio_semana,))
    existe = cursor.fetchone() is not None
    conexion.close()

    return existe


def listar_semanas_calendario():

    crear_base_datos()

    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("""
    SELECT DISTINCT fecha_inicio_semana
    FROM calendario_semanal
    ORDER BY fecha_inicio_semana
    """)
    semanas = [
        fila[0]
        for fila in cursor.fetchall()
    ]
    conexion.close()

    return semanas


def reemplazar_calendario_semana(fecha_inicio_semana, asignaciones):

    crear_base_datos()

    fecha_inicio_semana = normalizar_fecha_inicio_semana(
        fecha_inicio_semana
    )
    conexion = conectar()

    try:

        cursor = conexion.cursor()
        cursor.execute("""
        DELETE FROM calendario_semanal
        WHERE fecha_inicio_semana=?
        """,(fecha_inicio_semana,))

        for (dia, turno_id), elementos in (asignaciones or {}).items():

            for asignacion in elementos:

                cursor.execute("""
                INSERT OR IGNORE INTO calendario_semanal(
                    fecha_inicio_semana,
                    dia,
                    turno_id,
                    restaurante_id,
                    repartidor_id
                )
                VALUES(?,?,?,?,?)
                """,(
                    fecha_inicio_semana,
                    dia,
                    turno_id,
                    asignacion["restaurante_id"],
                    asignacion.get("repartidor_id")
                ))

        conexion.commit()

    except Exception:

        conexion.rollback()
        raise

    finally:

        conexion.close()


def validar_proveedor_integracion(proveedor):

    proveedor = str(proveedor or "").lower()

    if not proveedor:

        raise ValueError("Proveedor de integracion no valido.")

    if not proveedor.replace("_", "").isalnum():

        raise ValueError("Proveedor de integracion no valido.")

    return proveedor


def obtener_integraciones_api():

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        proveedor,
        nombre,
        activo,
        base_url,
        credenciales_referencia,
        opciones,
        fecha_actualizacion
    FROM integraciones_api
    ORDER BY nombre
    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


def obtener_integracion_api(proveedor):

    proveedor = validar_proveedor_integracion(proveedor)
    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        proveedor,
        nombre,
        activo,
        base_url,
        credenciales_referencia,
        opciones,
        fecha_actualizacion
    FROM integraciones_api
    WHERE proveedor=?
    """,(proveedor,))

    datos = cursor.fetchone()

    conexion.close()

    return datos


def guardar_integracion_api(
    proveedor,
    nombre,
    activo=0,
    base_url="",
    credenciales_referencia="",
    opciones=""
):

    proveedor = validar_proveedor_integracion(proveedor)
    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    INSERT INTO integraciones_api(
        proveedor,
        nombre,
        activo,
        base_url,
        credenciales_referencia,
        opciones,
        fecha_actualizacion
    )
    VALUES(?,?,?,?,?,?,CURRENT_TIMESTAMP)
    ON CONFLICT(proveedor) DO UPDATE SET
        nombre=excluded.nombre,
        activo=excluded.activo,
        base_url=excluded.base_url,
        credenciales_referencia=excluded.credenciales_referencia,
        opciones=excluded.opciones,
        fecha_actualizacion=CURRENT_TIMESTAMP
    """,(
        proveedor,
        nombre,
        activo,
        base_url,
        credenciales_referencia,
        opciones
    ))

    conexion.commit()
    conexion.close()


def registrar_evento_integracion(
    proveedor,
    tipo,
    estado,
    mensaje=""
):

    proveedor = validar_proveedor_integracion(proveedor)
    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    INSERT INTO integraciones_eventos(
        proveedor,
        tipo,
        estado,
        mensaje
    )
    VALUES(?,?,?,?)
    """,(
        proveedor,
        tipo,
        estado,
        mensaje
    ))

    conexion.commit()
    conexion.close()


def obtener_eventos_integracion(limite=100):

    crear_base_datos()

    conexion = conectar()

    cursor = conexion.cursor()

    cursor.execute("""
    SELECT
        proveedor,
        tipo,
        estado,
        mensaje,
        creado_en
    FROM integraciones_eventos
    ORDER BY creado_en DESC
    LIMIT ?
    """,(limite,))

    datos = cursor.fetchall()

    conexion.close()

    return datos
