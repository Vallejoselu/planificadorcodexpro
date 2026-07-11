from dataclasses import asdict, dataclass


@dataclass
class Ausencia:

    id: int
    repartidor_id: int
    fecha_inicio: str
    fecha_fin: str | None = None
    activa: bool = True
    tipo: str = "ausencia"
    observaciones: str = ""

    @classmethod
    def from_row(cls, fila, tipo="ausencia"):

        return cls(
            id=int(fila[0]),
            repartidor_id=int(fila[1]),
            fecha_inicio=fila[2],
            fecha_fin=fila[3] if len(fila) > 3 else None,
            activa=bool(fila[4]) if len(fila) > 4 else True,
            tipo=tipo,
            observaciones=fila[5] if len(fila) > 5 and fila[5] else ""
        )

    def to_dict(self):

        return asdict(self)
