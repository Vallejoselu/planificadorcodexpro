from repositories.calendario_repository import CalendarioRepository
from repositories.ciudades_repository import CiudadesRepository
from repositories.demandas_ciudad_repository import DemandasCiudadRepository
from repositories.demandas_zona_repository import DemandasZonaRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.plantillas_repository import PlantillasRepository
from repositories.turnos_repository import TurnosRepository
from database.schema import DIAS_SEMANA
from services.fechas import normalizar_fecha_inicio_semana
from services.planning_engine import PlanningEngine


class CuadrantesService:

    def __init__(
        self,
        calendario_repository=None,
        ciudades_repository=None,
        repartidores_repository=None,
        restaurantes_repository=None,
        demandas_ciudad_repository=None,
        demandas_zona_repository=None,
        plantillas_repository=None,
        turnos_repository=None,
        planning_engine=None
    ):

        self.calendario_repository = (
            calendario_repository or CalendarioRepository()
        )
        self.ciudades_repository = ciudades_repository or CiudadesRepository()
        self.repartidores_repository = (
            repartidores_repository or RepartidoresRepository()
        )
        self.restaurantes_repository = (
            restaurantes_repository or RestaurantesRepository()
        )
        self.demandas_ciudad_repository = (
            demandas_ciudad_repository or DemandasCiudadRepository()
        )
        self.demandas_zona_repository = (
            demandas_zona_repository or DemandasZonaRepository()
        )
        self.plantillas_repository = (
            plantillas_repository or PlantillasRepository()
        )
        self.turnos_repository = turnos_repository or TurnosRepository()
        self.planning_engine = planning_engine or PlanningEngine()

    def obtener_contexto(self):

        ciudades = [
            ciudad
            for ciudad in self.ciudades_repository.listar_activas()
            if ciudad[2]
        ]
        turnos = self.turnos_repository.listar_activos()
        restaurantes = self.restaurantes_repository.listar_activos()
        restaurante_turnos = []
        demandas_restaurante = []

        for restaurante in restaurantes:

            restaurante_turnos.extend([
                turno
                for turno in self.restaurantes_repository.listar_turnos(
                    restaurante[0]
                )
                if turno[7]
            ])
            demandas_restaurante.extend([
                demanda
                for demanda in self.restaurantes_repository.listar_demanda(
                    restaurante[0]
                )
                if demanda[6]
            ])

        return {
            "ciudades": ciudades,
            "turnos": turnos,
            "restaurantes": restaurantes,
            "restaurante_turnos": restaurante_turnos,
            "demandas_restaurante": demandas_restaurante,
            "demandas_zona": [
                demanda
                for demanda in self.demandas_zona_repository.listar()
                if demanda[6]
            ],
            "demandas_ciudad": [
                demanda
                for demanda in self.demandas_ciudad_repository.listar()
                if demanda[7]
            ],
            "repartidores": self.repartidores_repository.listar_activos()
        }

    def generar_cuadrante(self, contexto, fecha_inicio):

        fecha_inicio = normalizar_fecha_inicio_semana(fecha_inicio)
        self.validar_contexto_generacion(contexto)

        demandas_multinivel = self.preparar_demandas_multinivel(contexto)

        if self.hay_demanda_multiciudad(demandas_multinivel):

            resultado = self.planning_engine.generar_multiciudad(
                contexto["repartidores"],
                contexto["ciudades"],
                contexto["restaurantes"],
                contexto["restaurante_turnos"],
                demandas_multinivel,
                fecha_inicio=fecha_inicio
            )

            return {
                "resultado": resultado,
                "asignaciones": self.convertir_resultado_multiciudad(
                    resultado
                )
            }

        turnos_engine, mapa_turnos = self.preparar_turnos_engine(
            contexto["turnos"]
        )
        resultado = self.planning_engine.generar(
            contexto["repartidores"],
            contexto["restaurantes"],
            turnos_engine,
            fecha_inicio=fecha_inicio
        )

        return {
            "resultado": resultado,
            "asignaciones": self.convertir_resultado_planificador(
                resultado,
                mapa_turnos
            )
        }

    def validar_contexto_generacion(self, contexto):

        if not contexto["repartidores"]:

            raise ValueError("No hay repartidores activos.")

        if not contexto["restaurantes"]:

            raise ValueError("No hay restaurantes activos.")

        if not contexto["turnos"] and not contexto["restaurante_turnos"]:

            raise ValueError("No hay turnos activos.")

    def hay_demanda_multiciudad(self, demandas):

        return any(
            demanda.get("activo", 1)
            for demanda in demandas
        )

    def preparar_demandas_multinivel(self, contexto):

        nombres_turno = {
            turno[0]: turno[2]
            for turno in contexto.get("turnos", [])
        }
        demandas = []

        for demanda in contexto.get("demandas_restaurante", []):

            demandas.append({
                "nivel": "restaurante",
                "id": demanda[0],
                "restaurante_id": demanda[1],
                "turno_restaurante_id": demanda[2],
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            })

        for demanda in contexto.get("demandas_zona", []):

            demandas.append({
                "nivel": "zona",
                "id": demanda[0],
                "zona": demanda[1],
                "turno_id": demanda[2],
                "turno_nombre": nombres_turno.get(demanda[2]),
                "fecha": demanda[3],
                "dia_semana": demanda[4],
                "repartidores_necesarios": demanda[5],
                "activo": demanda[6]
            })

        for demanda in contexto.get("demandas_ciudad", []):

            demandas.append({
                "nivel": "ciudad",
                "id": demanda[0],
                "ciudad_id": demanda[1],
                "ciudad": demanda[2],
                "turno_id": demanda[3],
                "turno_nombre": nombres_turno.get(demanda[3]),
                "fecha": demanda[4],
                "dia_semana": demanda[5],
                "repartidores_necesarios": demanda[6],
                "activo": demanda[7]
            })

        for demanda in contexto.get("demandas_defecto", []):

            datos = dict(demanda)
            datos.setdefault("nivel", "defecto")
            demandas.append(datos)

        return demandas

    def preparar_turnos_engine(self, turnos):

        turnos_engine = []
        mapa_turnos = {}

        for turno in turnos:

            clave = self.clave_turno_engine(turno)

            if clave in mapa_turnos:

                continue

            mapa_turnos[clave] = turno[0]
            turnos_engine.append({
                "nombre": clave,
                "horas": float(turno[6] or 0),
                "hora_inicio": turno[3],
                "hora_fin": turno[4]
            })

        return turnos_engine, mapa_turnos

    def clave_turno_engine(self, turno):

        texto = f"{turno[1]} {turno[2]}".lower()

        if "comida" in texto:

            return "comida"

        if "cena" in texto or "noche" in texto:

            return "noche"

        return str(turno[2]).strip().lower().replace(" ", "_")

    def convertir_resultado_planificador(self, resultado, mapa_turnos):

        asignaciones = {}

        for dia, turnos_dia in resultado.get("horario", {}).items():

            for nombre_turno, elementos in turnos_dia.items():

                turno_id = mapa_turnos.get(nombre_turno)

                if turno_id is None:

                    continue

                clave = (dia, turno_id)

                for elemento in elementos:

                    asignacion = {
                        "restaurante_id": elemento["restaurante_id"],
                        "repartidor_id": elemento.get("repartidor_id")
                    }

                    if asignacion not in asignaciones.setdefault(clave, []):

                        asignaciones[clave].append(asignacion)

        return asignaciones

    def convertir_resultado_multiciudad(self, resultado):

        asignaciones = {}

        for dia, turnos_dia in resultado.get("horario", {}).items():

            for elementos in turnos_dia.values():

                for elemento in elementos:

                    turno_restaurante_id = elemento.get(
                        "turno_restaurante_id"
                    )

                    if not turno_restaurante_id:

                        continue

                    clave = (
                        dia,
                        ("restaurante_turno", turno_restaurante_id)
                    )
                    asignacion = {
                        "restaurante_id": elemento["restaurante_id"],
                        "repartidor_id": elemento.get("repartidor_id")
                    }

                    if asignacion not in asignaciones.setdefault(clave, []):

                        asignaciones[clave].append(asignacion)

        return asignaciones

    def guardar_cuadrante(self, fecha_inicio, asignaciones):

        asignaciones = self.resolver_turnos_asignaciones(asignaciones)

        return self.calendario_repository.reemplazar_semana(
            normalizar_fecha_inicio_semana(fecha_inicio),
            asignaciones
        )

    def sobrescribir_semana(self, fecha_inicio, asignaciones):

        return self.guardar_cuadrante(fecha_inicio, asignaciones)

    def copiar_semana(self, fecha_origen, fecha_destino):

        fecha_origen = normalizar_fecha_inicio_semana(fecha_origen)
        fecha_destino = normalizar_fecha_inicio_semana(fecha_destino)

        if fecha_origen == fecha_destino:

            raise ValueError(
                "La semana origen y la semana destino deben ser distintas."
            )

        calendario_origen = self.cargar_semana(fecha_origen)

        if not calendario_origen:

            raise ValueError(
                "La semana origen no tiene cuadrante guardado."
            )

        asignaciones = self.agrupar_calendario(calendario_origen)
        self.guardar_cuadrante(fecha_destino, asignaciones)

        return {
            "fecha_origen": fecha_origen,
            "fecha_destino": fecha_destino,
            "asignaciones": asignaciones,
            "total_asignaciones": sum(
                len(elementos)
                for elementos in asignaciones.values()
            )
        }

    def listar_plantillas(self):

        return self.plantillas_repository.listar()

    def crear_plantilla_desde_semana(
        self,
        fecha_origen,
        nombre,
        descripcion="",
        incluir_repartidores=True
    ):

        fecha_origen = normalizar_fecha_inicio_semana(fecha_origen)
        nombre = str(nombre or "").strip()

        if not nombre:

            raise ValueError("El nombre de la plantilla es obligatorio.")

        nombres_existentes = {
            str(plantilla[1]).strip().lower()
            for plantilla in self.listar_plantillas()
        }

        if nombre.lower() in nombres_existentes:

            raise ValueError("Ya existe una plantilla con ese nombre.")

        calendario_origen = self.cargar_semana(fecha_origen)

        if not calendario_origen:

            raise ValueError(
                "La semana origen no tiene cuadrante guardado."
            )

        asignaciones = self.agrupar_calendario(calendario_origen)

        if not incluir_repartidores:

            asignaciones = self.quitar_repartidores(asignaciones)

        plantilla_id = self.plantillas_repository.crear(
            nombre,
            descripcion,
            incluir_repartidores,
            asignaciones
        )

        return {
            "plantilla_id": plantilla_id,
            "fecha_origen": fecha_origen,
            "nombre": nombre,
            "incluir_repartidores": bool(incluir_repartidores),
            "total_asignaciones": self.contar_asignaciones(asignaciones)
        }

    def aplicar_plantilla(self, plantilla_id, fecha_destino):

        plantilla = self.plantillas_repository.obtener_por_id(plantilla_id)

        if not plantilla:

            raise ValueError("Selecciona una plantilla valida.")

        asignaciones = self.plantillas_repository.obtener_asignaciones(
            plantilla_id
        )

        if not asignaciones:

            raise ValueError("La plantilla no contiene asignaciones.")

        self.guardar_cuadrante(fecha_destino, asignaciones)

        return {
            "plantilla_id": plantilla_id,
            "nombre": plantilla[1],
            "fecha_destino": normalizar_fecha_inicio_semana(fecha_destino),
            "total_asignaciones": self.contar_asignaciones(asignaciones)
        }

    def quitar_repartidores(self, asignaciones):

        return {
            clave: [
                {
                    "restaurante_id": asignacion["restaurante_id"],
                    "repartidor_id": None
                }
                for asignacion in elementos
            ]
            for clave, elementos in (asignaciones or {}).items()
        }

    def contar_asignaciones(self, asignaciones):

        return sum(
            len(elementos)
            for elementos in (asignaciones or {}).values()
        )

    def resolver_turnos_asignaciones(self, asignaciones):

        resueltas = {}

        for (dia, turno_ref), elementos in (asignaciones or {}).items():

            turno_id = turno_ref

            if (
                isinstance(turno_ref, tuple)
                and turno_ref[0] == "restaurante_turno"
            ):

                turno_id = (
                    self.turnos_repository.obtener_o_crear_para_restaurante(
                        turno_ref[1]
                    )
                )

            resueltas[(dia, turno_id)] = elementos

        return resueltas

    def cargar_semana(self, fecha_inicio):

        return self.calendario_repository.listar_semana(
            normalizar_fecha_inicio_semana(fecha_inicio)
        )

    def preparar_estado_semana(
        self,
        fecha_inicio,
        turnos,
        restaurantes,
        repartidores
    ):

        calendario = self.cargar_semana(fecha_inicio)
        asignaciones = self.agrupar_calendario(calendario)
        indicadores = self.indicadores_semana(asignaciones)

        return {
            "calendario": calendario,
            "asignaciones": asignaciones,
            "estado_texto": (
                self.texto_estado_semana(indicadores)
                if calendario
                else (
                    "Sin cuadrante guardado para esta semana. "
                    "Genera uno o asigna turnos manualmente."
                )
            ),
            "indicadores": indicadores,
            "celdas_semana": self.construir_celdas_semana(
                asignaciones,
                turnos,
                restaurantes,
                repartidores
            ),
            "filas_locales": self.construir_filas_locales(
                asignaciones,
                turnos,
                restaurantes,
                repartidores
            )
        }

    def agrupar_calendario(self, calendario):

        asignaciones = {}

        for asignacion in calendario:

            dia = asignacion[1]
            turno_id = asignacion[2]
            restaurante_id = asignacion[6]
            repartidor_id = asignacion[9] if len(asignacion) > 9 else None

            asignaciones.setdefault((dia, turno_id), []).append({
                "restaurante_id": restaurante_id,
                "repartidor_id": repartidor_id
            })

        return asignaciones

    def indicadores_semana(self, asignaciones):

        total = sum(
            len(elementos)
            for elementos in asignaciones.values()
        )
        sin_repartidor = sum(
            1
            for elementos in asignaciones.values()
            for asignacion in elementos
            if asignacion.get("repartidor_id") is None
        )

        return {
            "asignaciones": total,
            "con_repartidor": total - sin_repartidor,
            "sin_repartidor": sin_repartidor
        }

    def texto_estado_semana(self, indicadores):

        if indicadores["sin_repartidor"]:

            return (
                f"Asignaciones: {indicadores['asignaciones']} | "
                f"Con repartidor: {indicadores['con_repartidor']} | "
                f"Sin repartidor: {indicadores['sin_repartidor']}"
            )

        return (
            f"Asignaciones: {indicadores['asignaciones']} | "
            "Todo cubierto"
        )

    def construir_celdas_semana(
        self,
        asignaciones,
        turnos,
        restaurantes,
        repartidores
    ):

        celdas = {}
        restaurantes_por_id = self.indexar_por_id(restaurantes)
        repartidores_por_id = self.indexar_por_id(repartidores)
        turnos_por_id = self.indexar_por_id(turnos)

        for clave, elementos in asignaciones.items():

            dia, turno_id = clave
            turno = turnos_por_id.get(turno_id)
            textos = []
            detalle = []
            primer_restaurante = None
            sin_repartidor = 0

            for asignacion in elementos:

                restaurante = restaurantes_por_id.get(
                    asignacion["restaurante_id"]
                )

                if not restaurante:

                    continue

                if primer_restaurante is None:

                    primer_restaurante = restaurante

                repartidor = repartidores_por_id.get(
                    asignacion.get("repartidor_id")
                )
                etiqueta_repartidor = (
                    f" - {repartidor[1]}"
                    if repartidor
                    else " - Sin repartidor"
                )
                if not repartidor:

                    sin_repartidor += 1

                textos.append(f"{restaurante[1]}{etiqueta_repartidor}")
                detalle.append(f"{restaurante[1]}{etiqueta_repartidor}")

            celdas[(dia, turno_id)] = {
                "texto": "\n".join(textos),
                "tooltip": self.tooltip_celda(
                    turno,
                    dia,
                    detalle,
                    sin_repartidor
                ),
                "estado": (
                    "pendiente"
                    if sin_repartidor
                    else "completo"
                ),
                "fondo": (
                    self.color_restaurante(primer_restaurante[0])
                    if primer_restaurante
                    else None
                ),
                "color_texto": (
                    self.color_turno(turno)
                    if turno
                    else None
                )
            }

        return celdas

    def tooltip_celda(self, turno, dia, detalle, sin_repartidor):

        partes = []
        nombre_turno = turno[2] if turno else "Turno"
        partes.append(f"{dia.capitalize()} - {nombre_turno}")

        if detalle:

            partes.extend(detalle)

        if sin_repartidor:

            partes.append(
                f"Pendientes sin repartidor: {sin_repartidor}"
            )

        return "\n".join(partes)

    def construir_filas_locales(
        self,
        asignaciones,
        turnos,
        restaurantes,
        repartidores
    ):

        return [
            {
                "restaurante_id": restaurante[0],
                "nombre": restaurante[1],
                "dias": {
                    dia: self.texto_local_dia(
                        asignaciones,
                        restaurante[0],
                        dia,
                        turnos,
                        repartidores
                    )
                    for dia in DIAS_SEMANA
                }
            }
            for restaurante in restaurantes
        ]

    def texto_local_dia(
        self,
        asignaciones,
        restaurante_id,
        dia,
        turnos,
        repartidores
    ):

        lineas = []
        repartidores_por_id = self.indexar_por_id(repartidores)

        for turno in turnos:

            for asignacion in asignaciones.get((dia, turno[0]), []):

                if asignacion["restaurante_id"] != restaurante_id:

                    continue

                repartidor = repartidores_por_id.get(
                    asignacion.get("repartidor_id")
                )
                texto = turno[2]

                if repartidor:

                    texto += f" - {repartidor[1]}"

                else:

                    texto += " - Sin repartidor"

                lineas.append(texto)

        return "\n".join(lineas)

    def preparar_cambio_asignacion(
        self,
        asignaciones,
        dia,
        turno_id,
        restaurante_id=None,
        repartidor_id=None,
        limpiar=False
    ):

        anterior = self.clonar_asignaciones_turno(
            asignaciones.get((dia, turno_id), [])
        )

        if limpiar:

            nuevo = []

        else:

            nuevo = self.agregar_asignacion(
                anterior,
                restaurante_id,
                repartidor_id
            )

        return {
            "anterior": anterior,
            "nuevo": nuevo
        }

    def agregar_asignacion(
        self,
        asignaciones,
        restaurante_id,
        repartidor_id=None
    ):

        nuevo = self.clonar_asignaciones_turno(asignaciones)

        if not restaurante_id:

            return nuevo

        asignacion = {
            "restaurante_id": restaurante_id,
            "repartidor_id": repartidor_id
        }

        if asignacion not in nuevo:

            nuevo.append(asignacion)

        return nuevo

    def clonar_asignaciones_turno(self, asignaciones):

        return [
            dict(asignacion)
            for asignacion in (asignaciones or [])
        ]

    def indexar_por_id(self, elementos):

        return {
            elemento[0]: elemento
            for elemento in elementos
            if elemento
        }

    def color_restaurante(self, restaurante_id):

        colores = [
            "#FFE599",
            "#B6D7A8",
            "#A4C2F4",
            "#D5A6BD",
            "#F9CB9C",
            "#B4A7D6",
            "#76A5AF"
        ]

        return colores[restaurante_id % len(colores)]

    def color_turno(self, turno):

        colores = {
            "Comida": "#0B5394",
            "Cena": "#674EA7",
            "Turno partido": "#38761D",
            "Personalizado": "#990000"
        }

        return turno[5] or colores.get(turno[1], "#333333")

    def semana_tiene_datos(self, fecha_inicio):

        return self.calendario_repository.semana_tiene_datos(
            normalizar_fecha_inicio_semana(fecha_inicio)
        )

    def guardar_asignacion_turno(
        self,
        fecha_inicio,
        dia,
        turno_id,
        asignaciones
    ):

        fecha_inicio = normalizar_fecha_inicio_semana(fecha_inicio)
        asignaciones = asignaciones or []

        self.calendario_repository.eliminar_turno(
            dia,
            turno_id,
            fecha_inicio_semana=fecha_inicio
        )

        for asignacion in asignaciones:

            self.calendario_repository.guardar_turno(
                dia,
                turno_id,
                asignacion["restaurante_id"],
                asignacion.get("repartidor_id"),
                fecha_inicio
            )

    def resumen_generacion(self, resultado):

        resumen = resultado.get("resumen", [])
        incidencias = resultado.get("incidencias", [])
        sin_cubrir = [
            incidencia
            for incidencia in incidencias
            if (
                incidencia.get("motivo") == "No hay repartidor disponible"
                or incidencia.get("regla") == "minimo de repartidores por turno"
            )
        ]
        turnos_cubiertos = sum(
            len(asignaciones)
            for turnos_dia in resultado.get("horario", {}).values()
            for asignaciones in turnos_dia.values()
        )
        horas_totales = sum(
            item.get("horas", 0)
            for item in resumen
        )
        repartidores_asignados = [
            item
            for item in resumen
            if item.get("horas", 0) > 0
        ]

        return {
            "resumen": resumen,
            "incidencias": incidencias,
            "sin_cubrir": sin_cubrir,
            "asignaciones_generadas": turnos_cubiertos,
            "advertencias": len(incidencias),
            "turnos_cubiertos": turnos_cubiertos,
            "horas_totales": horas_totales,
            "repartidores_asignados": repartidores_asignados
        }

    def texto_resumen_generacion(self, resultado):

        datos = self.resumen_generacion(resultado)
        resultado_texto = (
            "Con advertencias"
            if datos["incidencias"]
            else "Listo para guardar"
        )
        lineas = [
            "Resumen del cuadrante",
            "",
            f"Resultado: {resultado_texto}",
            f"Asignaciones generadas: {datos['asignaciones_generadas']}",
            f"Repartidores asignados: {len(datos['repartidores_asignados'])}",
            f"Turnos cubiertos: {datos['turnos_cubiertos']}",
            f"Turnos sin cubrir: {len(datos['sin_cubrir'])}",
            f"Horas totales: {datos['horas_totales']:g}",
            f"Advertencias: {datos['advertencias']}",
            "",
            "Repartidores"
        ]

        if datos["repartidores_asignados"]:

            for item in datos["repartidores_asignados"]:

                lineas.append(
                    f"- {item['nombre']}: {item['horas']:g} h"
                )

        else:

            lineas.append("- Ninguno")

        lineas.extend([
            "",
            "Turnos sin cubrir"
        ])

        if datos["sin_cubrir"]:

            for incidencia in datos["sin_cubrir"]:

                lineas.append(
                    "- "
                    + self.texto_incidencia(incidencia)
                )

        else:

            lineas.append("- Ninguno")

        lineas.extend([
            "",
            "Incidencias"
        ])

        if datos["incidencias"]:

            for incidencia in datos["incidencias"]:

                lineas.append(
                    "- "
                    + self.texto_incidencia(incidencia)
                )

        else:

            lineas.append("- Ninguna")

        return "\n".join(lineas)

    def texto_incidencia(self, incidencia):

        datos = [
            incidencia.get("dia"),
            incidencia.get("turno"),
            incidencia.get("restaurante")
        ]
        cabecera = " / ".join([
            dato
            for dato in datos
            if dato
        ])
        motivo = incidencia.get("motivo", "Incidencia")

        if cabecera:

            return f"{cabecera}: {motivo}"

        return motivo
