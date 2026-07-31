import database.database as database


class DatosInicialesService:

    CIUDAD = "Ciudad principal"
    RESTAURANTE = "Restaurante principal"
    ZONA = "Zona principal"
    TURNOS = (
        {
            "nombre": "Comida",
            "hora_inicio": "13:00",
            "hora_fin": "16:00",
            "cruza_medianoche": 0,
            "duracion": 3.0,
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

    def crear_datos_minimos(self):

        database.crear_base_datos()
        ciudad_id, ciudad_creada = self.asegurar_ciudad()
        restaurante_id, restaurante_creado = self.asegurar_restaurante(ciudad_id)
        turnos_creados = self.asegurar_turnos(restaurante_id)
        demandas_creadas = self.asegurar_demanda(restaurante_id)

        return {
            "ciudad_id": ciudad_id,
            "restaurante_id": restaurante_id,
            "ciudad_creada": ciudad_creada,
            "restaurante_creado": restaurante_creado,
            "turnos_creados": turnos_creados,
            "demandas_creadas": demandas_creadas,
            "repartidores_creados": 0
        }

    def asegurar_ciudad(self):

        ciudad = self.buscar_por_nombre("ciudades", self.CIUDAD)

        if ciudad:

            self.reactivar("ciudades", ciudad[0])
            return ciudad[0], False

        return database.insertar_ciudad(self.CIUDAD), True

    def asegurar_restaurante(self, ciudad_id):

        restaurante = self.buscar_por_nombre("restaurantes", self.RESTAURANTE)

        if restaurante:

            conexion = database.conectar()
            cursor = conexion.cursor()
            cursor.execute("""
            UPDATE restaurantes
            SET activo=1,
                ciudad_id=?
            WHERE id=?
            """, (ciudad_id, restaurante[0]))
            conexion.commit()
            conexion.close()
            return restaurante[0], False

        restaurante_id = database.insertar_restaurante(
            self.RESTAURANTE,
            "",
            self.ZONA,
            "",
            50,
            observaciones="Base minima creada desde Puesta en marcha.",
            ciudad_id=ciudad_id
        )
        return restaurante_id, True

    def asegurar_turnos(self, restaurante_id):

        existentes = self.turnos_como_diccionarios(restaurante_id)
        por_nombre = {
            turno["nombre"].casefold(): turno
            for turno in existentes
        }
        creados = 0

        for turno_base in self.TURNOS:

            clave = turno_base["nombre"].casefold()

            if clave in por_nombre:

                por_nombre[clave].update(turno_base)

            else:

                existentes.append(dict(turno_base))
                creados += 1

        database.guardar_restaurante_turnos(restaurante_id, existentes)
        return creados

    def asegurar_demanda(self, restaurante_id):

        turnos = [
            turno
            for turno in database.obtener_restaurante_turnos(restaurante_id)
            if turno[7] and turno[2].casefold() in {"comida", "cena"}
        ]
        demandas = self.demandas_como_diccionarios(restaurante_id)
        por_clave = {
            (demanda["turno_restaurante_id"], demanda.get("dia_semana")): demanda
            for demanda in demandas
            if demanda.get("dia_semana")
        }
        creadas = 0

        for turno in turnos:

            for dia in database.DIAS_SEMANA:

                clave = (turno[0], dia)

                if clave in por_clave:

                    por_clave[clave]["activo"] = 1
                    if por_clave[clave]["repartidores_necesarios"] < 1:
                        por_clave[clave]["repartidores_necesarios"] = 1

                else:

                    demandas.append({
                        "turno_restaurante_id": turno[0],
                        "fecha": None,
                        "dia_semana": dia,
                        "repartidores_necesarios": 1,
                        "activo": 1
                    })
                    creadas += 1

        database.guardar_demanda_restaurante(restaurante_id, demandas)
        return creadas

    def turnos_como_diccionarios(self, restaurante_id):

        return [
            {
                "id": turno[0],
                "nombre": turno[2],
                "hora_inicio": turno[3],
                "hora_fin": turno[4],
                "cruza_medianoche": turno[5],
                "duracion": turno[6],
                "activo": turno[7]
            }
            for turno in database.obtener_restaurante_turnos(restaurante_id)
        ]

    def demandas_como_diccionarios(self, restaurante_id):

        return [
            {
                "id": demanda[0],
                "turno_restaurante_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            }
            for demanda in database.obtener_demanda_restaurante(restaurante_id)
        ]

    def buscar_por_nombre(self, tabla, nombre):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"SELECT id, nombre, activo FROM {tabla} WHERE lower(nombre)=lower(?)",
            (nombre,)
        )
        fila = cursor.fetchone()
        conexion.close()
        return fila

    def reactivar(self, tabla, registro_id):

        conexion = database.conectar()
        cursor = conexion.cursor()
        cursor.execute(
            f"UPDATE {tabla} SET activo=1 WHERE id=?",
            (registro_id,)
        )
        conexion.commit()
        conexion.close()
