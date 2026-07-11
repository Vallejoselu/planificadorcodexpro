from dataclasses import asdict, dataclass


@dataclass
class AsignacionCalendario:

    id: int
    dia: str
    turno_id: int
    turno: str
    tipo_turno: str
    color_turno: str
    restaurante_id: int
    restaurante: str
    zona: str | None = None
    repartidor_id: int | None = None
    repartidor: str | None = None
    fecha_inicio_semana: str = "1970-01-05"

    @classmethod
    def from_row(cls, fila):

        return cls(
            id=int(fila[0]),
            dia=fila[1],
            turno_id=int(fila[2]),
            turno=fila[3],
            tipo_turno=fila[4],
            color_turno=fila[5],
            restaurante_id=int(fila[6]),
            restaurante=fila[7],
            zona=fila[8],
            repartidor_id=fila[9],
            repartidor=fila[10],
            fecha_inicio_semana=fila[11]
        )

    def to_dict(self):

        return asdict(self)
