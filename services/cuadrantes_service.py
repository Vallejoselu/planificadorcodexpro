from datetime import timedelta

from repositories.calendario_repository import CalendarioRepository
from repositories.ciudades_repository import CiudadesRepository
from repositories.demandas_ciudad_repository import DemandasCiudadRepository
from repositories.demandas_zona_repository import DemandasZonaRepository
from repositories.historial_repository import HistorialRepository
from repositories.repartidores_repository import RepartidoresRepository
from repositories.restaurantes_repository import RestaurantesRepository
from repositories.plantillas_repository import PlantillasRepository
from repositories.turnos_repository import TurnosRepository
from database.schema import DIAS_SEMANA
from services.rules.ausencias import esta_ausente, esta_ausente_por_tipo
from services.rules.disponibilidad import (
    categoria_turno,
    esta_disponible,
    parsear_fecha
)
from services.rules.candidatos import motivo_no_puede_trabajar
from services.fechas import normalizar_fecha_inicio_semana
from services.planning_engine import PlanningEngine
from services.scheduler import (
    normalizar_repartidor,
    normalizar_restaurantes,
    preparar_estado_repartidor,
    registrar_asignacion
)


class CuadrantesService:

    def __init__(
        self,
        calendario_repository=None,
        ciudades_repository=None,
        repartidores_repository=None,
        restaurantes_repository=None,
        demandas_ciudad_repository=None,
        demandas_zona_repository=None,
        historial_repository=None,
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
        self.historial_repository = (
            historial_repository or HistorialRepository()
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
        precomprobacion = self.precomprobar_generacion(
            contexto,
            fecha_inicio
        )

        if not precomprobacion["puede_generar"]:

            raise ValueError(precomprobacion["texto"])

        self.validar_contexto_base_generacion(contexto)
        self.asegurar_turnos_generacion(contexto)
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
            self.registrar_historial(
                "Generar cuadrante",
                "cuadrante",
                "Generacion automatica multiciudad",
                fecha_inicio
            )
            resultado["_precomprobacion"] = precomprobacion

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
        self.registrar_historial(
            "Generar cuadrante",
            "cuadrante",
            "Generacion automatica",
            fecha_inicio
        )
        resultado["_precomprobacion"] = precomprobacion

        return {
            "resultado": resultado,
            "asignaciones": self.convertir_resultado_planificador(
                resultado,
                mapa_turnos
            )
        }

    def precomprobar_generacion(self, contexto, fecha_inicio):

        fecha_inicio = normalizar_fecha_inicio_semana(fecha_inicio)
        repartidores = contexto.get("repartidores", [])
        restaurantes = contexto.get("restaurantes", [])
        turnos = contexto.get("turnos", [])
        restaurante_turnos = contexto.get("restaurante_turnos", [])
        demandas_restaurante = contexto.get("demandas_restaurante", [])
        demandas_zona = contexto.get("demandas_zona", [])
        demandas_ciudad = contexto.get("demandas_ciudad", [])
        errores = []
        advertencias = []

        if not repartidores:

            errores.append("No hay repartidores activos.")

        if not restaurantes:

            errores.append("No hay restaurantes activos.")

        if not turnos and not restaurante_turnos:

            advertencias.append(
                "No hay turnos configurados; se crearan turnos base "
                "de comida y cena antes de generar."
            )

        restaurantes_sin_demanda = self.alertas_restaurantes_sin_demanda(
            restaurantes,
            demandas_restaurante,
            demandas_zona,
            demandas_ciudad
        )

        for alerta in restaurantes_sin_demanda:

            advertencias.append(alerta["detalle"])

        if restaurantes and not (
            demandas_restaurante
            or demandas_zona
            or demandas_ciudad
        ):

            advertencias.append(
                "No hay demanda configurada. El generador puede crear "
                "una propuesta basica, pero el resultado no representa "
                "necesidades reales de cobertura."
            )

        datos = {
            "fecha_inicio": fecha_inicio,
            "repartidores": len(repartidores),
            "restaurantes": len(restaurantes),
            "turnos": len(turnos),
            "turnos_propios": len(restaurante_turnos),
            "demandas_restaurante": len(demandas_restaurante),
            "demandas_zona": len(demandas_zona),
            "demandas_ciudad": len(demandas_ciudad),
            "errores": errores,
            "advertencias": advertencias,
            "puede_generar": not errores
        }
        datos["texto"] = self.texto_precomprobacion(datos)
        return datos

    def texto_precomprobacion(self, datos):

        estado = (
            "Lista para generar"
            if datos["puede_generar"]
            else "No se puede generar"
        )
        lineas = [
            "Comprobacion previa del cuadrante",
            "",
            f"Estado: {estado}",
            f"Semana: {datos['fecha_inicio']}",
            f"Repartidores activos: {datos['repartidores']}",
            f"Restaurantes activos: {datos['restaurantes']}",
            f"Turnos globales: {datos['turnos']}",
            f"Turnos propios de restaurante: {datos['turnos_propios']}",
            (
                "Demandas configuradas: "
                f"{datos['demandas_restaurante']} por restaurante, "
                f"{datos['demandas_zona']} por zona, "
                f"{datos['demandas_ciudad']} por ciudad"
            )
        ]

        lineas.extend(["", "Errores bloqueantes"])

        if datos["errores"]:

            for error in datos["errores"]:

                lineas.append(f"- {error}")

        else:

            lineas.append("- Ninguno")

        lineas.extend(["", "Advertencias"])

        if datos["advertencias"]:

            for advertencia in datos["advertencias"]:

                lineas.append(f"- {advertencia}")

        else:

            lineas.append("- Ninguna")

        return "\n".join(lineas)

    def validar_contexto_generacion(self, contexto):

        self.validar_contexto_base_generacion(contexto)

        if not contexto["turnos"] and not contexto["restaurante_turnos"]:

            raise ValueError("No hay turnos activos.")

    def validar_contexto_base_generacion(self, contexto):

        if not contexto["repartidores"]:

            raise ValueError("No hay repartidores activos.")

        if not contexto["restaurantes"]:

            raise ValueError("No hay restaurantes activos.")

    def asegurar_turnos_generacion(self, contexto):

        if contexto.get("turnos") or contexto.get("restaurante_turnos"):

            return

        for turno in self.turnos_basicos():

            self.turnos_repository.crear(
                turno["tipo"],
                turno["nombre"],
                turno["hora_inicio"],
                turno["hora_fin"],
                turno["color"],
                turno["duracion"]
            )

        contexto["turnos"] = self.turnos_repository.listar_activos()

    def turnos_basicos(self):

        return [
            {
                "tipo": "Comida",
                "nombre": "Comida",
                "hora_inicio": "13:00",
                "hora_fin": "16:00",
                "color": "#2563EB",
                "duracion": 3
            },
            {
                "tipo": "Cena",
                "nombre": "Cena",
                "hora_inicio": "20:00",
                "hora_fin": "23:30",
                "color": "#16A34A",
                "duracion": 3.5
            }
        ]

    def registrar_historial(
        self,
        accion,
        entidad="",
        detalle="",
        fecha_inicio_semana=None
    ):

        return self.historial_repository.registrar(
            accion,
            entidad,
            detalle,
            fecha_inicio_semana
        )

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
        fecha_inicio = normalizar_fecha_inicio_semana(fecha_inicio)
        self.validar_asignaciones_semana(
            asignaciones,
            fecha_inicio,
            self.turnos_repository.listar_activos(),
            self.restaurantes_repository.listar_activos(),
            self.repartidores_repository.listar_activos()
        )
        total = sum(
            len(elementos)
            for elementos in (asignaciones or {}).values()
        )
        resultado = self.calendario_repository.reemplazar_semana(
            fecha_inicio,
            asignaciones
        )
        self.registrar_historial(
            "Crear cuadrante",
            "cuadrante",
            f"Cuadrante guardado con {total} asignaciones",
            fecha_inicio
        )

        return resultado

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
        repartidores,
        demandas_restaurante=None,
        demandas_zona=None,
        demandas_ciudad=None,
        restaurante_turnos=None
    ):

        calendario = self.cargar_semana(fecha_inicio)
        asignaciones = self.agrupar_calendario(calendario)
        indicadores = self.indicadores_semana(asignaciones)
        alertas = self.alertas_estado_semana(
            fecha_inicio,
            calendario,
            asignaciones,
            indicadores,
            turnos,
            restaurantes,
            repartidores,
            demandas_restaurante=demandas_restaurante,
            demandas_zona=demandas_zona,
            demandas_ciudad=demandas_ciudad,
            restaurante_turnos=restaurante_turnos
        )
        diagnostico = self.diagnosticar_semana(
            fecha_inicio,
            calendario,
            asignaciones,
            indicadores,
            alertas,
            turnos,
            restaurantes,
            repartidores
        )

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
            "alertas": alertas,
            "diagnostico": diagnostico,
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
            ),
            "filas_repartidores": self.construir_filas_repartidores(
                asignaciones,
                turnos,
                restaurantes,
                repartidores,
                fecha_inicio
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

    def alertas_estado_semana(
        self,
        fecha_inicio,
        calendario,
        asignaciones,
        indicadores,
        turnos,
        restaurantes,
        repartidores,
        demandas_restaurante=None,
        demandas_zona=None,
        demandas_ciudad=None,
        restaurante_turnos=None
    ):

        alertas = []
        alertas.extend(
            self.alertas_asignaciones_sin_repartidor(
                asignaciones,
                turnos
            )
        )
        alertas.extend(
            self.alertas_horas_repartidores(
                asignaciones,
                turnos,
                repartidores
            )
        )
        alertas.extend(
            self.alertas_restaurantes_sin_demanda(
                restaurantes,
                demandas_restaurante or [],
                demandas_zona or [],
                demandas_ciudad or []
            )
        )
        alertas.extend(
            self.alertas_conflictos_ausencias(
                fecha_inicio,
                calendario,
                repartidores
            )
        )
        alertas.extend(
            self.alertas_reglas_asignaciones(
                fecha_inicio,
                asignaciones,
                turnos,
                restaurantes,
                repartidores
            )
        )

        if not calendario and indicadores["asignaciones"] == 0:

            return alertas

        return alertas

    def alertas_asignaciones_sin_repartidor(self, asignaciones, turnos):

        alertas = []
        turnos_por_id = self.indexar_por_id(turnos)

        for (dia, turno_id), elementos in sorted(asignaciones.items()):

            pendientes = [
                asignacion
                for asignacion in elementos
                if asignacion.get("repartidor_id") is None
            ]

            if not pendientes:

                continue

            turno = turnos_por_id.get(turno_id)
            nombre_turno = self.nombre_turno(turno)
            detalle = (
                f"{dia} / {nombre_turno}: "
                f"{len(pendientes)} asignaciones sin repartidor."
            )
            alertas.append(
                self.crear_alerta("Turnos sin cubrir", detalle, "alta")
            )
            alertas.append(
                self.crear_alerta(
                    "Asignaciones sin repartidor",
                    detalle,
                    "alta"
                )
            )

        return alertas

    def alertas_horas_repartidores(self, asignaciones, turnos, repartidores):

        alertas = []
        horas = self.horas_por_repartidor_asignado(asignaciones, turnos)

        for repartidor in repartidores:

            repartidor_id = self.valor_campo(repartidor, "id", 0)
            nombre = self.valor_campo(repartidor, "nombre", 1)
            contratadas = float(self.valor_campo(repartidor, "horas", 2) or 0)
            trabajadas = float(horas.get(repartidor_id, 0) or 0)
            extra = max(0, trabajadas - contratadas)
            pendientes = max(0, contratadas - trabajadas)

            if pendientes > 0 and trabajadas > 0:

                alertas.append(
                    self.crear_alerta(
                        "Horas pendientes",
                        (
                            f"{nombre}: {pendientes:g} h pendientes "
                            f"de {contratadas:g} contratadas."
                        ),
                        "media"
                    )
                )

            if extra > 0:

                alertas.append(
                    self.crear_alerta(
                        "Horas extra",
                        (
                            f"{nombre}: {extra:g} h extra "
                            f"({trabajadas:g}/{contratadas:g} h)."
                        ),
                        "media"
                    )
                )

        return alertas

    def horas_por_repartidor_asignado(self, asignaciones, turnos):

        turnos_por_id = self.indexar_por_id(turnos)
        horas = {}

        for (dia, turno_id), elementos in asignaciones.items():

            turno = turnos_por_id.get(turno_id)
            duracion = float(self.valor_campo(turno, "duracion", 6) or 0)

            for asignacion in elementos:

                repartidor_id = asignacion.get("repartidor_id")

                if repartidor_id is None:

                    continue

                horas[repartidor_id] = horas.get(repartidor_id, 0) + duracion

        return horas

    def alertas_restaurantes_sin_demanda(
        self,
        restaurantes,
        demandas_restaurante,
        demandas_zona,
        demandas_ciudad
    ):

        alertas = []

        for restaurante in restaurantes:

            if not self.restaurante_activo(restaurante):

                continue

            if self.restaurante_tiene_demanda_configurada(
                restaurante,
                demandas_restaurante,
                demandas_zona,
                demandas_ciudad
            ):

                continue

            alertas.append(
                self.crear_alerta(
                    "Restaurantes sin demanda",
                    (
                        f"{self.valor_campo(restaurante, 'nombre', 1)} "
                        "no tiene demanda configurada."
                    ),
                    "media"
                )
            )

        return alertas

    def restaurante_tiene_demanda_configurada(
        self,
        restaurante,
        demandas_restaurante,
        demandas_zona,
        demandas_ciudad
    ):

        restaurante_id = self.valor_campo(restaurante, "id", 0)
        zona = self.valor_campo(restaurante, "zona", 3)
        ciudad_id = self.valor_campo(restaurante, "ciudad_id", 9)

        return (
            any(
                self.demanda_activa(demanda, 6)
                and self.valor_campo(demanda, "restaurante_id", 1)
                == restaurante_id
                for demanda in demandas_restaurante
            )
            or any(
                self.demanda_activa(demanda, 6)
                and self.valor_campo(demanda, "zona", 1) == zona
                for demanda in demandas_zona
            )
            or any(
                self.demanda_activa(demanda, 7)
                and self.valor_campo(demanda, "ciudad_id", 1) == ciudad_id
                for demanda in demandas_ciudad
            )
        )

    def alertas_conflictos_ausencias(
        self,
        fecha_inicio,
        calendario,
        repartidores
    ):

        alertas = []
        fechas = self.fechas_semana(fecha_inicio)
        repartidores_por_id = {
            self.valor_campo(repartidor, "id", 0): repartidor
            for repartidor in repartidores
        }

        for fila in calendario:

            repartidor_id = fila[9] if len(fila) > 9 else None

            if repartidor_id is None:

                continue

            dia = fila[1]
            fecha = fechas.get(dia)
            repartidor = self.repartidor_para_alertas(
                repartidores_por_id.get(repartidor_id)
            )

            if not repartidor:

                continue

            if esta_ausente_por_tipo(repartidor, "vacaciones", fecha, dia):

                alertas.append(
                    self.crear_alerta(
                        "Conflictos por vacaciones/bajas",
                        (
                            f"{repartidor['nombre']} esta de vacaciones "
                            f"el {dia} y tiene un turno asignado."
                        ),
                        "alta"
                    )
                )

            if esta_ausente_por_tipo(repartidor, "bajas", fecha, dia):

                alertas.append(
                    self.crear_alerta(
                        "Conflictos por vacaciones/bajas",
                        (
                            f"{repartidor['nombre']} esta de baja "
                            f"el {dia} y tiene un turno asignado."
                        ),
                        "alta"
                    )
                )

        return alertas

    def alertas_reglas_asignaciones(
        self,
        fecha_inicio,
        asignaciones,
        turnos,
        restaurantes,
        repartidores
    ):

        problemas = self.problemas_reglas_asignaciones(
            fecha_inicio,
            asignaciones,
            turnos,
            restaurantes,
            repartidores
        )

        return [
            self.crear_alerta(
                "Reglas incumplidas",
                problema["detalle"],
                "alta"
            )
            for problema in problemas
        ]

    def problemas_reglas_asignaciones(
        self,
        fecha_inicio,
        asignaciones,
        turnos,
        restaurantes,
        repartidores
    ):

        turnos_por_id = {
            self.valor_campo(turno, "id", 0): self.turno_para_reglas(turno)
            for turno in turnos
        }
        restaurantes_por_id = {
            restaurante["id"]: restaurante
            for restaurante in normalizar_restaurantes(restaurantes)
        }
        repartidores_por_id = self.repartidores_normalizados_para_reglas(
            repartidores
        )

        for repartidor in repartidores_por_id.values():

            preparar_estado_repartidor(repartidor)

        fechas = self.fechas_semana(fecha_inicio)
        problemas = []

        for (dia, turno_id), elementos in sorted(
            (asignaciones or {}).items(),
            key=lambda item: (DIAS_SEMANA.index(item[0][0]), item[0][1])
        ):

            turno = turnos_por_id.get(turno_id)

            if not turno:

                continue

            for asignacion in elementos or []:

                repartidor_id = asignacion.get("repartidor_id")

                if repartidor_id is None:

                    continue

                repartidor = repartidores_por_id.get(repartidor_id)
                restaurante = restaurantes_por_id.get(
                    asignacion.get("restaurante_id")
                )

                if not repartidor or not restaurante:

                    continue

                motivo = motivo_no_puede_trabajar(
                    repartidor,
                    restaurante,
                    dia,
                    turno,
                    fechas.get(dia)
                )

                if motivo:

                    problemas.append({
                        "dia": dia,
                        "turno": turno.get("nombre", "Turno"),
                        "restaurante": restaurante.get("nombre", ""),
                        "repartidor": repartidor.get("nombre", ""),
                        "motivo": motivo,
                        "detalle": (
                            f"{repartidor.get('nombre', 'Repartidor')} "
                            f"no puede cubrir {dia} / "
                            f"{turno.get('nombre', 'Turno')} en "
                            f"{restaurante.get('nombre', 'restaurante')}: "
                            f"{motivo}."
                        )
                    })
                    continue

                registrar_asignacion(
                    repartidor,
                    restaurante,
                    turno,
                    dia
                )

        return problemas

    def repartidores_normalizados_para_reglas(self, repartidores):

        normalizados = {}

        for repartidor in repartidores or []:

            try:

                datos = normalizar_repartidor(repartidor)

            except (IndexError, KeyError, TypeError, ValueError):

                continue

            normalizados[datos["id"]] = datos

        return normalizados

    def diagnosticar_semana(
        self,
        fecha_inicio,
        calendario,
        asignaciones,
        indicadores,
        alertas,
        turnos,
        restaurantes,
        repartidores
    ):

        alertas = alertas or []
        altas = [
            alerta
            for alerta in alertas
            if alerta.get("severidad") == "alta"
        ]
        medias = [
            alerta
            for alerta in alertas
            if alerta.get("severidad") == "media"
        ]
        problemas = [
            self.problema_desde_alerta(alerta)
            for alerta in alertas
        ]

        if not calendario and not indicadores.get("asignaciones"):

            estado = "pendiente"
            resumen = (
                "No hay cuadrante guardado para esta semana. "
                "Genera uno o asigna turnos manualmente para poder analizarlo."
            )

        elif altas:

            estado = "critico"
            resumen = (
                f"Hay {len(altas)} problema(s) critico(s) que conviene "
                "resolver antes de usar el cuadrante."
            )

        elif medias:

            estado = "aviso"
            resumen = (
                f"El cuadrante puede usarse, pero tiene {len(medias)} "
                "aviso(s) operativo(s)."
            )

        else:

            estado = "ok"
            resumen = (
                "Cuadrante cubierto sin problemas detectados con las "
                "reglas actuales."
            )

        return {
            "fecha_inicio": normalizar_fecha_inicio_semana(fecha_inicio),
            "estado": estado,
            "resumen": resumen,
            "total_alertas": len(alertas),
            "criticas": len(altas),
            "avisos": len(medias),
            "asignaciones": indicadores.get("asignaciones", 0),
            "con_repartidor": indicadores.get("con_repartidor", 0),
            "sin_repartidor": indicadores.get("sin_repartidor", 0),
            "problemas": problemas,
            "texto": self.texto_diagnostico(
                resumen,
                indicadores,
                problemas
            )
        }

    def problema_desde_alerta(self, alerta):

        tipo = alerta.get("tipo", "")
        return {
            "tipo": tipo,
            "detalle": alerta.get("detalle", ""),
            "severidad": alerta.get("severidad", "media"),
            "accion": self.accion_recomendada_alerta(tipo)
        }

    def accion_recomendada_alerta(self, tipo):

        acciones = {
            "Turnos sin cubrir": (
                "Asigna un repartidor compatible o baja la demanda "
                "si la plaza no es necesaria."
            ),
            "Asignaciones sin repartidor": (
                "Completa las plazas vacias antes de publicar el cuadrante."
            ),
            "Horas pendientes": (
                "Revisa si el repartidor necesita mas turnos o si su "
                "disponibilidad impide completar contrato."
            ),
            "Horas extra": (
                "Confirma que las horas complementarias estan permitidas "
                "y dentro del limite."
            ),
            "Restaurantes sin demanda": (
                "Configura demanda por restaurante, zona o ciudad para "
                "que el generador sepa cuantas plazas crear."
            ),
            "Conflictos por vacaciones/bajas": (
                "Cambia la asignacion o retira al repartidor ausente."
            ),
            "Reglas incumplidas": (
                "Sustituye el repartidor o corrige disponibilidad, descanso "
                "y autorizaciones."
            )
        }

        return acciones.get(
            tipo,
            "Revisa la configuracion relacionada con esta alerta."
        )

    def texto_diagnostico(self, resumen, indicadores, problemas):

        lineas = [
            resumen,
            (
                f"Asignaciones: {indicadores.get('asignaciones', 0)} | "
                f"Cubiertas: {indicadores.get('con_repartidor', 0)} | "
                f"Pendientes: {indicadores.get('sin_repartidor', 0)}"
            )
        ]

        if problemas:

            lineas.append("Acciones recomendadas:")

            for problema in problemas[:5]:

                lineas.append(
                    f"- {problema['tipo']}: {problema['accion']}"
                )

        return "\n".join(lineas)

    def alertas_generacion(self, resultado):

        alertas = []

        for incidencia in resultado.get("incidencias", []):

            alerta = self.alerta_desde_incidencia(incidencia)

            if alerta:

                alertas.append(alerta)

        for item in resultado.get("horas_complementarias", []):

            if item.get("usadas", 0) <= 0:

                continue

            alertas.append(
                self.crear_alerta(
                    "Horas extra",
                    (
                        f"{item['nombre']}: {item['usadas']:g} h extra "
                        f"de {item['limite']:g} permitidas."
                    ),
                    "media"
                )
            )

        for dia, turnos_dia in resultado.get("horario", {}).items():

            for nombre_turno, asignaciones in turnos_dia.items():

                sin_repartidor = sum(
                    1
                    for asignacion in asignaciones
                    if asignacion.get("repartidor_id") is None
                )

                if sin_repartidor:

                    detalle = (
                        f"{dia} / {nombre_turno}: "
                        f"{sin_repartidor} asignaciones sin repartidor."
                    )
                    alertas.append(
                        self.crear_alerta(
                            "Asignaciones sin repartidor",
                            detalle,
                            "alta"
                        )
                    )

        return alertas

    def alerta_desde_incidencia(self, incidencia):

        motivo = incidencia.get("motivo", "")
        regla = incidencia.get("regla", "")
        texto = f"{motivo} {regla}".lower()
        detalle = self.texto_incidencia(incidencia)

        if (
            "cobertura" in texto
            or "faltan" in texto
            or "minimo de repartidores" in texto
            or "no hay repartidor" in texto
        ):

            return self.crear_alerta("Turnos sin cubrir", detalle, "alta")

        if "horas pendientes" in texto:

            return self.crear_alerta("Horas pendientes", detalle, "media")

        if (
            "horas complementarias" in texto
            or "horas extra" in texto
        ):

            return self.crear_alerta("Horas extra", detalle, "media")

        if (
            "ausencia" in texto
            or "vacaciones" in texto
            or "baja" in texto
        ):

            return self.crear_alerta(
                "Conflictos por vacaciones/bajas",
                detalle,
                "alta"
            )

        return None

    def crear_alerta(self, tipo, detalle, severidad="media"):

        return {
            "tipo": tipo,
            "detalle": detalle,
            "severidad": severidad
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
            horario = self.texto_horario_turno(turno)
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
                    f" - {self.valor_campo(repartidor, 'nombre', 1)}"
                    if repartidor
                    else " - Sin repartidor"
                )
                if not repartidor:

                    sin_repartidor += 1

                nombre_restaurante = self.valor_campo(
                    restaurante,
                    "nombre",
                    1
                )
                textos.append(f"{nombre_restaurante}{etiqueta_repartidor}")
                detalle.append(f"{nombre_restaurante}{etiqueta_repartidor}")

            if horario and textos:

                textos.insert(0, horario)

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
                    self.color_restaurante(
                        self.valor_campo(primer_restaurante, "id", 0)
                    )
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
        nombre_turno = self.nombre_turno(turno) if turno else "Turno"
        partes.append(f"{dia.capitalize()} - {nombre_turno}")
        horario = self.texto_horario_turno(turno)

        if horario:

            partes.append(horario)

        if detalle:

            partes.extend(detalle)

        if sin_repartidor:

            partes.append(
                f"Pendientes sin repartidor: {sin_repartidor}"
            )

        return "\n".join(partes)

    def texto_horario_turno(self, turno):

        if not turno:

            return ""

        inicio = self.valor_campo(turno, "hora_inicio", 3)
        fin = self.valor_campo(turno, "hora_fin", 4)
        duracion = self.valor_campo(turno, "duracion", 6)

        if not inicio or not fin:

            return ""

        texto = f"{inicio}-{fin}"

        if duracion:

            texto += f" ({float(duracion):g} h)"

        return texto

    def construir_filas_locales(
        self,
        asignaciones,
        turnos,
        restaurantes,
        repartidores
    ):

        return [
            {
                "restaurante_id": self.valor_campo(restaurante, "id", 0),
                "nombre": self.valor_campo(restaurante, "nombre", 1),
                "dias": {
                    dia: self.texto_local_dia(
                        asignaciones,
                        self.valor_campo(restaurante, "id", 0),
                        dia,
                        turnos,
                        repartidores
                    )
                    for dia in DIAS_SEMANA
                }
            }
            for restaurante in restaurantes
        ]

    def construir_filas_repartidores(
        self,
        asignaciones,
        turnos,
        restaurantes,
        repartidores,
        fecha_inicio=None
    ):

        return [
            self.fila_repartidor_cuadrante(
                repartidor,
                asignaciones,
                turnos,
                restaurantes,
                fecha_inicio
            )
            for repartidor in repartidores
        ]

    def fila_repartidor_cuadrante(
        self,
        repartidor,
        asignaciones,
        turnos,
        restaurantes,
        fecha_inicio=None
    ):

        repartidor_normalizado = self.repartidor_para_cuadrante(repartidor)
        preparar_estado_repartidor(repartidor_normalizado)
        fechas = self.fechas_semana(fecha_inicio)
        celdas = {
            dia: self.celda_repartidor_dia(
                asignaciones,
                repartidor_normalizado,
                dia,
                turnos,
                restaurantes,
                fechas.get(dia)
            )
            for dia in DIAS_SEMANA
        }

        return {
            "repartidor_id": repartidor_normalizado["id"],
            "nombre": repartidor_normalizado["nombre"],
            "contrato": f"{repartidor_normalizado['horas_contratadas']}h",
            "dias": {
                dia: celdas[dia]["texto"]
                for dia in DIAS_SEMANA
            },
            "celdas": celdas
        }

    def repartidor_para_cuadrante(self, repartidor):

        if isinstance(repartidor, dict):

            return normalizar_repartidor(repartidor)

        if len(repartidor) >= 9:

            return normalizar_repartidor(repartidor)

        return normalizar_repartidor({
            "id": self.valor_campo(repartidor, "id", 0),
            "nombre": self.valor_campo(repartidor, "nombre", 1, ""),
            "horas": self.valor_campo(repartidor, "horas", 2, 0),
            "zona": self.valor_campo(repartidor, "zona", 3, None),
            "doble_turno": self.valor_campo(
                repartidor,
                "doble_turno",
                4,
                1
            ),
            "puede_hasta_la_una": self.valor_campo(
                repartidor,
                "puede_hasta_la_una",
                5,
                1
            ),
            "prioridad_comida": self.valor_campo(
                repartidor,
                "prioridad_comida",
                6,
                50
            ),
            "prioridad_noche": self.valor_campo(
                repartidor,
                "prioridad_noche",
                7,
                50
            ),
            "prioridad_grela": self.valor_campo(
                repartidor,
                "prioridad_grela",
                8,
                50
            ),
            "disponibilidad": {}
        })

    def celda_repartidor_dia(
        self,
        asignaciones,
        repartidor,
        dia,
        turnos,
        restaurantes,
        fecha=None
    ):

        asignaciones_dia = self.asignaciones_repartidor_dia(
            asignaciones,
            repartidor["id"],
            dia,
            turnos,
            restaurantes
        )

        if not asignaciones_dia:

            if self.repartidor_libre_dia(repartidor, dia, fecha):

                return {
                    "texto": "LIBRE",
                    "estado": "libre",
                    "tooltip": self.motivo_libre_dia(repartidor, dia, fecha)
                }

            return {
                "texto": "-",
                "estado": "disponible",
                "tooltip": "Disponible sin turno asignado"
            }

        comidas = [
            asignacion
            for asignacion in asignaciones_dia
            if categoria_turno(asignacion["turno"]) == "comida"
        ]
        cenas = [
            asignacion
            for asignacion in asignaciones_dia
            if categoria_turno(asignacion["turno"]) == "noche"
        ]

        if comidas and cenas:

            estado = "doble"
            cabecera = "DOBLE"

        elif comidas:

            estado = "comida"
            cabecera = "COMIDA"

        elif cenas:

            estado = "cena"
            cabecera = "CENA"

        else:

            estado = "turno"
            cabecera = "TURNO"

        lineas = [cabecera]

        for asignacion in asignaciones_dia:

            horario = self.texto_horario_turno(asignacion["turno"])
            restaurante = asignacion["restaurante"]
            nombre_turno = self.nombre_turno(asignacion["turno"]).upper()
            detalle = nombre_turno

            if horario:

                detalle += f" {horario}"

            if restaurante:

                detalle += (
                    f"\n{self.valor_campo(restaurante, 'nombre', 1)}"
                )

            lineas.append(detalle)

        texto = "\n".join(lineas)

        return {
            "texto": texto,
            "estado": estado,
            "tooltip": texto
        }

    def asignaciones_repartidor_dia(
        self,
        asignaciones,
        repartidor_id,
        dia,
        turnos,
        restaurantes
    ):

        resultado = []
        turnos_por_id = self.indexar_por_id(turnos)
        restaurantes_por_id = self.indexar_por_id(restaurantes)

        for (dia_asignado, turno_id), elementos in asignaciones.items():

            if dia_asignado != dia:

                continue

            turno = turnos_por_id.get(turno_id)

            if not turno:

                continue

            for asignacion in elementos:

                if asignacion.get("repartidor_id") != repartidor_id:

                    continue

                resultado.append({
                    "turno": turno,
                    "restaurante": restaurantes_por_id.get(
                        asignacion["restaurante_id"]
                    )
                })

        return resultado

    def repartidor_libre_dia(self, repartidor, dia, fecha=None):

        if dia in repartidor.get("descanso", []):

            return True

        if esta_ausente(repartidor, dia, fecha):

            return True

        return not esta_disponible(repartidor, dia, None)

    def motivo_libre_dia(self, repartidor, dia, fecha=None):

        if dia in repartidor.get("descanso", []):

            return "Descanso"

        if esta_ausente_por_tipo(repartidor, "vacaciones", fecha, dia):

            return "Vacaciones"

        if esta_ausente_por_tipo(repartidor, "bajas", fecha, dia):

            return "Baja"

        return "No disponible"

    def texto_repartidor_dia(
        self,
        asignaciones,
        repartidor_id,
        dia,
        turnos,
        restaurantes
    ):

        lineas = []
        restaurantes_por_id = self.indexar_por_id(restaurantes)

        for turno in turnos:

            for asignacion in asignaciones.get((dia, turno[0]), []):

                if asignacion.get("repartidor_id") != repartidor_id:

                    continue

                restaurante = restaurantes_por_id.get(
                    asignacion["restaurante_id"]
                )
                texto = turno[2]
                horario = self.texto_horario_turno(turno)

                if horario:

                    texto += f" {horario}"

                if restaurante:

                    texto += f" - {restaurante[1]}"

                lineas.append(texto)

        return "\n".join(lineas)

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

            turno_id = self.valor_campo(turno, "id", 0)

            for asignacion in asignaciones.get((dia, turno_id), []):

                if asignacion["restaurante_id"] != restaurante_id:

                    continue

                repartidor = repartidores_por_id.get(
                    asignacion.get("repartidor_id")
                )
                texto = self.nombre_turno(turno)
                horario = self.texto_horario_turno(turno)

                if horario:

                    texto += f" {horario}"

                if repartidor:

                    texto += (
                        f" - {self.valor_campo(repartidor, 'nombre', 1)}"
                    )

                else:

                    texto += " - Sin repartidor"

                lineas.append(texto)

        return "\n".join(lineas)

    def validar_asignaciones_semana(
        self,
        asignaciones,
        fecha_inicio,
        turnos,
        restaurantes,
        repartidores
    ):

        turnos_por_id = {
            self.valor_campo(turno, "id", 0): self.turno_para_reglas(turno)
            for turno in turnos
        }
        restaurantes_normalizados = normalizar_restaurantes(restaurantes)
        restaurantes_por_id = {
            restaurante["id"]: restaurante
            for restaurante in restaurantes_normalizados
        }
        repartidores_por_id = {
            repartidor["id"]: repartidor
            for repartidor in [
                normalizar_repartidor(repartidor)
                for repartidor in repartidores
            ]
        }

        for repartidor in repartidores_por_id.values():

            preparar_estado_repartidor(repartidor)

        fechas = self.fechas_semana(fecha_inicio)

        for (dia, turno_id), elementos in sorted(
            (asignaciones or {}).items(),
            key=lambda item: (DIAS_SEMANA.index(item[0][0]), item[0][1])
        ):

            turno = turnos_por_id.get(turno_id)

            if not turno:

                continue

            for asignacion in elementos or []:

                repartidor_id = asignacion.get("repartidor_id")

                if repartidor_id is None:

                    continue

                repartidor = repartidores_por_id.get(repartidor_id)
                restaurante = restaurantes_por_id.get(
                    asignacion.get("restaurante_id")
                )

                if not repartidor or not restaurante:

                    continue

                motivo = motivo_no_puede_trabajar(
                    repartidor,
                    restaurante,
                    dia,
                    turno,
                    fechas.get(dia)
                )

                if motivo:

                    raise ValueError(
                        self.texto_rechazo_asignacion(
                            repartidor,
                            restaurante,
                            dia,
                            turno,
                            motivo
                        )
                    )

                registrar_asignacion(
                    repartidor,
                    restaurante,
                    turno,
                    dia
                )

    def turno_para_reglas(self, turno):

        if isinstance(turno, dict):

            datos = dict(turno)

        else:

            datos = {
                "id": turno[0],
                "tipo": turno[1],
                "nombre": turno[2],
                "hora_inicio": turno[3],
                "hora_fin": turno[4],
                "color": turno[5],
                "duracion": turno[6],
                "activo": turno[7] if len(turno) > 7 else 1
            }

        datos["horas"] = float(
            datos.get("duracion", datos.get("horas", 0)) or 0
        )
        datos.setdefault("cruza_medianoche", 0)

        return datos

    def texto_rechazo_asignacion(
        self,
        repartidor,
        restaurante,
        dia,
        turno,
        motivo
    ):

        horario = self.texto_horario_turno(turno)
        turno_texto = turno.get("nombre", "Turno")

        if horario:

            turno_texto = f"{turno_texto} {horario}"

        return (
            f"No se puede asignar a {repartidor['nombre']}.\n\n"
            f"Dia: {dia}\n"
            f"Turno: {turno_texto}\n"
            f"Restaurante: {restaurante['nombre']}\n"
            f"Regla incumplida: {motivo}."
        )

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
            self.valor_campo(elemento, "id", 0): elemento
            for elemento in elementos
            if elemento
        }

    def valor_campo(self, elemento, clave, indice, defecto=None):

        if not elemento:

            return defecto

        if isinstance(elemento, dict):

            return elemento.get(clave, defecto)

        if len(elemento) > indice:

            return elemento[indice]

        return defecto

    def demanda_activa(self, demanda, indice_activo):

        return bool(self.valor_campo(demanda, "activo", indice_activo, 1))

    def restaurante_activo(self, restaurante):

        return bool(self.valor_campo(restaurante, "activo", 6, 1))

    def nombre_turno(self, turno):

        return self.valor_campo(turno, "nombre", 2, "Turno")

    def fechas_semana(self, fecha_inicio):

        inicio = parsear_fecha(normalizar_fecha_inicio_semana(fecha_inicio))

        if not inicio:

            return {}

        return {
            dia: inicio + timedelta(days=indice)
            for indice, dia in enumerate(DIAS_SEMANA)
        }

    def repartidor_para_alertas(self, repartidor):

        if not repartidor:

            return None

        if isinstance(repartidor, dict):

            return repartidor

        return {
            "id": self.valor_campo(repartidor, "id", 0),
            "nombre": self.valor_campo(repartidor, "nombre", 1),
            "vacaciones": self.valor_campo(
                repartidor,
                "vacaciones",
                12,
                []
            ) or [],
            "bajas": self.valor_campo(repartidor, "bajas", 13, []) or []
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

        color = self.valor_campo(turno, "color", 5)
        tipo = self.valor_campo(turno, "tipo", 1)

        return color or colores.get(tipo, "#333333")

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

        if asignaciones:

            propuestas = self.agrupar_calendario(
                self.cargar_semana(fecha_inicio)
            )
            propuestas[(dia, turno_id)] = self.clonar_asignaciones_turno(
                asignaciones
            )
            self.validar_asignaciones_semana(
                propuestas,
                fecha_inicio,
                self.turnos_repository.listar_activos(),
                self.restaurantes_repository.listar_activos(),
                self.repartidores_repository.listar_activos()
            )

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

        if asignaciones:

            self.registrar_historial(
                "Editar asignacion",
                "calendario_semanal",
                (
                    f"{dia} turno {turno_id}: "
                    f"{len(asignaciones)} asignaciones"
                ),
                fecha_inicio
            )

        else:

            self.registrar_historial(
                "Eliminar turno",
                "calendario_semanal",
                f"{dia} turno {turno_id}",
                fecha_inicio
            )

    def resumen_generacion(self, resultado):

        resumen = resultado.get("resumen", [])
        incidencias = resultado.get("incidencias", [])
        horas_complementarias = [
            item
            for item in resultado.get("horas_complementarias", [])
            if item.get("usadas", 0) > 0
        ]
        sin_cubrir = [
            incidencia
            for incidencia in incidencias
            if (
                incidencia.get("motivo") == "No hay repartidor disponible"
                or incidencia.get("regla") == "minimo de repartidores por turno"
            )
        ]
        asignaciones_generadas = sum(
            len(asignaciones)
            for turnos_dia in resultado.get("horario", {}).values()
            for asignaciones in turnos_dia.values()
        )
        asignaciones_con_repartidor = sum(
            1
            for turnos_dia in resultado.get("horario", {}).values()
            for asignaciones in turnos_dia.values()
            for asignacion in asignaciones
            if asignacion.get("repartidor_id") is not None
        )
        asignaciones_sin_repartidor = (
            asignaciones_generadas - asignaciones_con_repartidor
        )
        cobertura_porcentaje = (
            round(
                asignaciones_con_repartidor
                * 100
                / asignaciones_generadas,
                1
            )
            if asignaciones_generadas
            else 0
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
            "horas_complementarias": horas_complementarias,
            "sin_cubrir": sin_cubrir,
            "asignaciones_generadas": asignaciones_generadas,
            "asignaciones_con_repartidor": asignaciones_con_repartidor,
            "asignaciones_sin_repartidor": asignaciones_sin_repartidor,
            "cobertura_porcentaje": cobertura_porcentaje,
            "advertencias": len(incidencias),
            "turnos_cubiertos": asignaciones_con_repartidor,
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
            "Vista previa del cuadrante",
            "",
            "El cuadrante aun no esta guardado.",
            f"Resultado: {resultado_texto}",
            f"Asignaciones generadas: {datos['asignaciones_generadas']}",
            (
                "Asignaciones con repartidor: "
                f"{datos['asignaciones_con_repartidor']}"
            ),
            (
                "Asignaciones sin repartidor: "
                f"{datos['asignaciones_sin_repartidor']}"
            ),
            f"Cobertura: {datos['cobertura_porcentaje']:g}%",
            f"Repartidores asignados: {len(datos['repartidores_asignados'])}",
            f"Turnos cubiertos: {datos['turnos_cubiertos']}",
            f"Turnos sin cubrir: {len(datos['sin_cubrir'])}",
            f"Horas totales: {datos['horas_totales']:g}",
            f"Advertencias: {datos['advertencias']}"
        ]

        precomprobacion = resultado.get("_precomprobacion")

        if precomprobacion:

            lineas.extend([
                "",
                "Comprobacion previa"
            ])

            if precomprobacion.get("advertencias"):

                for advertencia in precomprobacion["advertencias"]:

                    lineas.append(f"- {advertencia}")

            else:

                lineas.append("- Sin advertencias previas")

        lineas.extend([
            "",
            "Repartidores"
        ])

        if datos["repartidores_asignados"]:

            for item in datos["repartidores_asignados"]:

                lineas.append(
                    f"- {item['nombre']}: {item['horas']:g} h"
                )

        else:

            lineas.append("- Ninguno")

        lineas.extend([
            "",
            "Horas complementarias"
        ])

        if datos["horas_complementarias"]:

            for item in datos["horas_complementarias"]:

                lineas.append(
                    f"- {item['nombre']}: {item['usadas']:g} h "
                    f"de {item['limite']:g} permitidas"
                )

        else:

            lineas.append("- Ninguna")

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
