from repositories.calendario_repository import CalendarioRepository
from repositories.ciudades_repository import CiudadesRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.turnos_repository import TurnosRepository
from services.fechas import normalizar_fecha_inicio_semana
from services.planning_engine import PlanningEngine


class CuadrantesService:

    def __init__(
        self,
        calendario_repository=None,
        ciudades_repository=None,
        repartidores_repository=None,
        restaurantes_repository=None,
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
            "repartidores": self.repartidores_repository.listar_activos()
        }

    def generar_cuadrante(self, contexto, fecha_inicio):

        fecha_inicio = normalizar_fecha_inicio_semana(fecha_inicio)
        self.validar_contexto_generacion(contexto)

        if self.hay_demanda_multiciudad(contexto["demandas_restaurante"]):

            resultado = self.planning_engine.generar_multiciudad(
                contexto["repartidores"],
                contexto["ciudades"],
                contexto["restaurantes"],
                contexto["restaurante_turnos"],
                contexto["demandas_restaurante"],
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

    def hay_demanda_multiciudad(self, demandas_restaurante):

        return any(
            demanda[6]
            for demanda in demandas_restaurante
        )

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
            "turnos_cubiertos": turnos_cubiertos,
            "horas_totales": horas_totales,
            "repartidores_asignados": repartidores_asignados
        }

    def texto_resumen_generacion(self, resultado):

        datos = self.resumen_generacion(resultado)
        lineas = [
            "Resumen del cuadrante",
            "",
            f"Repartidores asignados: {len(datos['repartidores_asignados'])}",
            f"Turnos cubiertos: {datos['turnos_cubiertos']}",
            f"Turnos sin cubrir: {len(datos['sin_cubrir'])}",
            f"Horas totales: {datos['horas_totales']:g}",
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
