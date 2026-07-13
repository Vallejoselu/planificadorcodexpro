import database.database as db


class PlantillasRepository:

    def listar(self):

        return db.listar_plantillas_semana()

    def obtener_por_id(self, plantilla_id):

        return db.obtener_plantilla_semana(plantilla_id)

    def crear(
        self,
        nombre,
        descripcion,
        incluir_repartidores,
        asignaciones
    ):

        return db.crear_plantilla_semana(
            nombre,
            descripcion,
            incluir_repartidores,
            asignaciones
        )

    def obtener_asignaciones(self, plantilla_id):

        asignaciones = {}

        for dia, turno_id, restaurante_id, repartidor_id in (
            db.obtener_asignaciones_plantilla_semana(plantilla_id)
        ):

            asignaciones.setdefault((dia, turno_id), []).append({
                "restaurante_id": restaurante_id,
                "repartidor_id": repartidor_id
            })

        return asignaciones
