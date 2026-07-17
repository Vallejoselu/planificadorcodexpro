import database.database as db


PREFIJO_DEMO = "[Demo]"


class DatosDemoService:

    CIUDADES = ("Santiago", "A Coruna", "Ourense")
    RESTAURANTES = (
        ("Santiago", "Burger King Santiago Centro", "Centro"),
        ("Santiago", "Burger King Santiago Norte", "Norte"),
        ("A Coruna", "Burger King A Coruna Ronda", "Ronda"),
        ("Ourense", "Burger King Ourense Centro", "Centro")
    )
    TURNOS_RESTAURANTE = (
        {
            "nombre": "Comida",
            "hora_inicio": "13:00",
            "hora_fin": "16:00",
            "cruza_medianoche": 0,
            "duracion": 3,
            "activo": 1
        },
        {
            "nombre": "Cena",
            "hora_inicio": "20:00",
            "hora_fin": "23:30",
            "cruza_medianoche": 0,
            "duracion": 3.5,
            "activo": 1
        }
    )
    REPARTIDORES = (
        ("Ana Demo", 30, "Centro", "Santiago", "Burger King Santiago Centro"),
        ("Bruno Demo", 20, "Norte", "Santiago", "Burger King Santiago Norte"),
        ("Carla Demo", 25, "Ronda", "A Coruna", "Burger King A Coruna Ronda"),
        ("Diego Demo", 30, "Centro", "Ourense", "Burger King Ourense Centro"),
        ("Elena Demo", 20, "Centro", "Santiago", None)
    )

    def cargar_demo(self):

        db.crear_base_datos()
        ciudades = self._crear_ciudades()
        restaurantes = self._crear_restaurantes(ciudades)
        turnos = self._crear_turnos_restaurante(restaurantes)
        self._crear_demanda(restaurantes, turnos)
        repartidores = self._crear_repartidores(ciudades, restaurantes)

        return {
            "ciudades": len(ciudades),
            "restaurantes": len(restaurantes),
            "turnos": sum(len(valor) for valor in turnos.values()),
            "repartidores": len(repartidores)
        }

    def limpiar_demo(self):

        db.crear_base_datos()
        conexion = db.conectar()
        cursor = conexion.cursor()

        cursor.execute("""
        SELECT id
        FROM repartidores
        WHERE nombre LIKE ?
        """, (self._like_demo(),))
        repartidores = [fila[0] for fila in cursor.fetchall()]

        cursor.execute("""
        SELECT id
        FROM restaurantes
        WHERE nombre LIKE ?
        """, (self._like_demo(),))
        restaurantes = [fila[0] for fila in cursor.fetchall()]

        cursor.execute("""
        SELECT id
        FROM ciudades
        WHERE nombre LIKE ?
        """, (self._like_demo(),))
        ciudades = [fila[0] for fila in cursor.fetchall()]

        self._desactivar_por_ids(cursor, "repartidores", repartidores)
        self._desactivar_por_ids(cursor, "restaurantes", restaurantes)
        self._desactivar_por_ids(cursor, "ciudades", ciudades)
        self._eliminar_calendario_demo(cursor, repartidores, restaurantes)
        self._desactivar_relaciones_demo(
            cursor,
            repartidores,
            restaurantes,
            ciudades
        )

        conexion.commit()
        conexion.close()

        return {
            "ciudades": len(ciudades),
            "restaurantes": len(restaurantes),
            "repartidores": len(repartidores)
        }

    def estado(self):

        db.crear_base_datos()
        conexion = db.conectar()
        cursor = conexion.cursor()
        resultado = {}

        for tabla in ("ciudades", "restaurantes", "repartidores"):

            cursor.execute(
                f"SELECT COUNT(*) FROM {tabla} WHERE nombre LIKE ? AND activo=1",
                (self._like_demo(),)
            )
            resultado[tabla] = cursor.fetchone()[0]

        conexion.close()
        return resultado

    def empezar_de_cero(self):

        from services.datos_locales import crear_backup

        db.crear_base_datos()
        respaldo = crear_backup(ruta_bd=db.RUTA_BD)
        conexion = db.conectar()
        cursor = conexion.cursor()

        resumen = {
            "respaldo": str(respaldo),
            "ciudades": self._contar_activos(cursor, "ciudades"),
            "restaurantes": self._contar_activos(cursor, "restaurantes"),
            "turnos": self._contar_activos(cursor, "turnos"),
            "repartidores": self._contar_activos(cursor, "repartidores"),
            "cuadrantes": self._contar_filas(cursor, "calendario_semanal")
        }

        for tabla in (
            "repartidores",
            "restaurantes",
            "ciudades",
            "turnos",
            "restaurante_turnos",
            "demanda_restaurante",
            "demanda_zona",
            "demanda_ciudad",
            "restaurante_repartidores",
            "repartidor_ciudades",
            "repartidor_restaurantes_autorizados",
            "descansos",
            "vacaciones",
            "bajas",
            "plantillas_semana",
            "integraciones_api"
        ):

            self._desactivar_tabla(cursor, tabla)

        for tabla in (
            "calendario_semanal",
            "plantilla_semana_asignaciones",
            "cuadrante_publicaciones",
            "integraciones_sincronizaciones",
            "integraciones_eventos"
        ):

            self._vaciar_tabla(cursor, tabla)

        conexion.commit()
        conexion.close()

        return resumen

    def _crear_ciudades(self):

        existentes = self._filas_por_nombre("ciudades")
        ciudades = {}

        for nombre_ciudad in self.CIUDADES:

            nombre = self._nombre(nombre_ciudad)
            fila_ciudad = existentes.get(nombre)
            ciudad_id = fila_ciudad[0] if fila_ciudad else None

            if not ciudad_id:

                ciudad_id = db.insertar_ciudad(nombre)

            else:

                db.actualizar_ciudad(ciudad_id, nombre, 1)

            ciudades[nombre_ciudad] = ciudad_id

        return ciudades

    def _crear_restaurantes(self, ciudades):

        existentes = self._filas_por_nombre("restaurantes")
        restaurantes = {}

        for ciudad, restaurante, zona in self.RESTAURANTES:

            nombre = self._nombre(restaurante)
            fila_restaurante = existentes.get(nombre)
            restaurante_id = fila_restaurante[0] if fila_restaurante else None

            if not restaurante_id:

                restaurante_id = db.insertar_restaurante(
                    nombre,
                    "",
                    zona,
                    "",
                    50,
                    observaciones="Datos demo para probar la aplicacion.",
                    horario_comida="13:00-16:00",
                    horario_cena="20:00-23:30",
                    ciudad_id=ciudades[ciudad]
                )

            else:

                db.actualizar_restaurante(
                    restaurante_id,
                    nombre,
                    "",
                    zona,
                    "",
                    1,
                    "13:00-16:00",
                    "20:00-23:30",
                    ciudad_id=ciudades[ciudad]
                )

            restaurantes[restaurante] = restaurante_id

        return restaurantes

    def _crear_turnos_restaurante(self, restaurantes):

        resultado = {}

        for restaurante, restaurante_id in restaurantes.items():

            existentes = {
                turno[2]: turno
                for turno in db.obtener_restaurante_turnos(restaurante_id)
            }
            turnos = []

            for turno in self.TURNOS_RESTAURANTE:

                existente = existentes.get(turno["nombre"])
                datos = dict(turno)

                if existente:

                    datos["id"] = existente[0]

                turnos.append(datos)

            db.guardar_restaurante_turnos(restaurante_id, turnos)
            resultado[restaurante] = [
                turno
                for turno in db.obtener_restaurante_turnos(restaurante_id)
                if turno[7]
            ]

        return resultado

    def _crear_demanda(self, restaurantes, turnos_por_restaurante):

        dias = ("lunes", "martes", "miercoles", "jueves", "viernes")

        for restaurante, restaurante_id in restaurantes.items():

            demandas = []
            existentes = {
                (demanda[2], demanda[4]): demanda
                for demanda in db.obtener_demanda_restaurante(restaurante_id)
                if demanda[4]
            }

            for turno in turnos_por_restaurante[restaurante]:

                necesarios = 2 if turno[2] == "Cena" else 1

                for dia in dias:

                    demanda = {
                        "turno_restaurante_id": turno[0],
                        "dia_semana": dia,
                        "fecha": None,
                        "repartidores_necesarios": necesarios,
                        "activo": 1
                    }
                    existente = existentes.get((turno[0], dia))

                    if existente:

                        demanda["id"] = existente[0]

                    demandas.append(demanda)

            db.guardar_demanda_restaurante(restaurante_id, demandas)

    def _crear_repartidores(self, ciudades, restaurantes):

        existentes = self._filas_por_nombre("repartidores")
        resultado = {}

        for nombre, horas, zona, ciudad, restaurante in self.REPARTIDORES:

            nombre_demo = self._nombre(nombre)
            repartidor = existentes.get(nombre_demo)
            repartidor_id = repartidor[0] if repartidor else None
            restaurante_id = restaurantes.get(restaurante) if restaurante else None
            ciudades_autorizadas = [ciudades[ciudad]]
            restaurantes_autorizados = [restaurante_id] if restaurante_id else []

            if not repartidor_id:

                repartidor_id = db.insertar_repartidor(
                    nombre_demo,
                    horas,
                    zona,
                    1,
                    1,
                    70,
                    60,
                    50,
                    observaciones="Datos demo para probar la aplicacion.",
                    descanso_inicio="martes",
                    descanso_fin="miercoles",
                    disponibilidad=self._disponibilidad_demo(),
                    ciudad_principal_id=ciudades[ciudad],
                    restaurante_principal_id=restaurante_id,
                    apoyo_flexible=0 if restaurante_id else 1,
                    horas_complementarias=4,
                    max_horas_diarias=10,
                    max_dias_consecutivos=5,
                    ciudades_autorizadas=ciudades_autorizadas,
                    restaurantes_autorizados=restaurantes_autorizados
                )

            else:

                db.actualizar_repartidor(
                    repartidor_id,
                    nombre_demo,
                    horas,
                    zona,
                    1,
                    1,
                    70,
                    60,
                    50,
                    observaciones="Datos demo para probar la aplicacion.",
                    descanso_inicio="martes",
                    descanso_fin="miercoles",
                    disponibilidad=self._disponibilidad_demo(),
                    ciudad_principal_id=ciudades[ciudad],
                    restaurante_principal_id=restaurante_id,
                    apoyo_flexible=0 if restaurante_id else 1,
                    horas_complementarias=4,
                    max_horas_diarias=10,
                    max_dias_consecutivos=5,
                    ciudades_autorizadas=ciudades_autorizadas,
                    restaurantes_autorizados=restaurantes_autorizados
                )
                self._activar_repartidor(repartidor_id)

            resultado[nombre] = repartidor_id

        return resultado

    def _disponibilidad_demo(self):

        return {
            "lunes": "Ambos",
            "martes": "No disponible",
            "miercoles": "No disponible",
            "jueves": "Ambos",
            "viernes": "Ambos",
            "sabado": "Cenas",
            "domingo": "Comidas"
        }

    def _desactivar_relaciones_demo(
        self,
        cursor,
        repartidores,
        restaurantes,
        ciudades
    ):

        for tabla, columna, ids in (
            ("descansos", "repartidor_id", repartidores),
            ("restaurante_repartidores", "restaurante_id", restaurantes),
            ("restaurante_turnos", "restaurante_id", restaurantes),
            ("demanda_restaurante", "restaurante_id", restaurantes),
            ("repartidor_ciudades", "repartidor_id", repartidores),
            (
                "repartidor_restaurantes_autorizados",
                "repartidor_id",
                repartidores
            )
        ):

            self._desactivar_por_ids(cursor, tabla, ids, columna=columna)

    def _eliminar_calendario_demo(self, cursor, repartidores, restaurantes):

        condiciones = []
        parametros = []

        if repartidores:

            marcadores = ",".join("?" for _ in repartidores)
            condiciones.append(f"repartidor_id IN ({marcadores})")
            parametros.extend(repartidores)

        if restaurantes:

            marcadores = ",".join("?" for _ in restaurantes)
            condiciones.append(f"restaurante_id IN ({marcadores})")
            parametros.extend(restaurantes)

        if not condiciones:

            return

        cursor.execute(
            "DELETE FROM calendario_semanal WHERE " + " OR ".join(condiciones),
            parametros
        )

    def _desactivar_por_ids(self, cursor, tabla, ids, columna="id"):

        if not ids:

            return

        marcadores = ",".join("?" for _ in ids)
        cursor.execute(
            f"UPDATE {tabla} SET activo=0 WHERE {columna} IN ({marcadores})",
            ids
        )

    def _tabla_existe(self, cursor, tabla):

        cursor.execute("""
        SELECT 1
        FROM sqlite_master
        WHERE type='table'
        AND name=?
        """, (tabla,))
        return cursor.fetchone() is not None

    def _columnas(self, cursor, tabla):

        if not self._tabla_existe(cursor, tabla):

            return set()

        cursor.execute(f"PRAGMA table_info({tabla})")
        return {
            fila[1]
            for fila in cursor.fetchall()
        }

    def _contar_filas(self, cursor, tabla):

        if not self._tabla_existe(cursor, tabla):

            return 0

        cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
        return cursor.fetchone()[0]

    def _contar_activos(self, cursor, tabla):

        columnas = self._columnas(cursor, tabla)

        if not columnas:

            return 0

        condicion = " WHERE activo=1" if "activo" in columnas else ""
        cursor.execute(f"SELECT COUNT(*) FROM {tabla}{condicion}")
        return cursor.fetchone()[0]

    def _desactivar_tabla(self, cursor, tabla):

        if "activo" not in self._columnas(cursor, tabla):

            return

        cursor.execute(f"UPDATE {tabla} SET activo=0")

    def _vaciar_tabla(self, cursor, tabla):

        if not self._tabla_existe(cursor, tabla):

            return

        cursor.execute(f"DELETE FROM {tabla}")

    def _filas_por_nombre(self, tabla):

        db.crear_base_datos()
        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"SELECT id, nombre, activo FROM {tabla} WHERE nombre LIKE ?",
            (self._like_demo(),)
        )
        filas = cursor.fetchall()
        conexion.close()

        return {
            fila[1]: fila
            for fila in filas
        }

    def _activar_repartidor(self, repartidor_id):

        conexion = db.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE repartidores SET activo=1 WHERE id=?",
            (repartidor_id,)
        )
        conexion.commit()
        conexion.close()

    def _por_nombre(self, filas):

        return {
            fila[1]: fila[0]
            for fila in filas
        }

    def _nombre(self, nombre):

        return f"{PREFIJO_DEMO} {nombre}"

    def _like_demo(self):

        return f"{PREFIJO_DEMO} %"
