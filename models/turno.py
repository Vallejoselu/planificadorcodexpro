from dataclasses import asdict, dataclass


@dataclass
class Turno:

    id: int
    tipo: str
    nombre: str
    hora_inicio: str
    hora_fin: str
    color: str = "#2563EB"
    duracion: float = 0
    activo: bool = True
    turno_restaurante_id: int | None = None

    @classmethod
    def from_row(cls, fila):

        return cls(
            id=int(fila[0]),
            tipo=fila[1],
            nombre=fila[2],
            hora_inicio=fila[3],
            hora_fin=fila[4],
            color=fila[5] if len(fila) > 5 else "#2563EB",
            duracion=float(fila[6] or 0) if len(fila) > 6 else 0,
            activo=bool(fila[7]) if len(fila) > 7 else True,
            turno_restaurante_id=fila[8] if len(fila) > 8 else None
        )

    def to_dict(self):

        return asdict(self)


@dataclass
class TurnoRestaurante:

    id: int
    restaurante_id: int
    nombre: str
    hora_inicio: str
    hora_fin: str
    cruza_medianoche: bool = False
    duracion: float = 0
    activo: bool = True

    @classmethod
    def from_row(cls, fila):

        return cls(
            id=int(fila[0]),
            restaurante_id=int(fila[1]),
            nombre=fila[2],
            hora_inicio=fila[3],
            hora_fin=fila[4],
            cruza_medianoche=bool(fila[5]),
            duracion=float(fila[6] or 0),
            activo=bool(fila[7])
        )

    def to_dict(self):

        return asdict(self)
