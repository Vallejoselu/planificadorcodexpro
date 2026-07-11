from dataclasses import asdict, dataclass


@dataclass
class Disponibilidad:

    repartidor_id: int
    dia: str
    turno: str
    disponible: bool = True
    observaciones: str = ""

    @classmethod
    def from_row(cls, fila):

        return cls(
            repartidor_id=int(fila[0]),
            dia=fila[1],
            turno=fila[2],
            disponible=bool(fila[3]),
            observaciones=fila[4] if len(fila) > 4 and fila[4] else ""
        )

    def to_dict(self):

        return asdict(self)
