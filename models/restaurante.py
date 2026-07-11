from dataclasses import asdict, dataclass


@dataclass
class Restaurante:

    id: int
    nombre: str
    direccion: str | None = None
    zona: str | None = None
    telefono: str | None = None
    prioridad: int = 50
    activo: bool = True
    horario_comida: str | None = None
    horario_cena: str | None = None
    ciudad_id: int | None = None
    ciudad: str | None = None
    observaciones: str = ""

    @classmethod
    def from_row(cls, fila):

        return cls(
            id=int(fila[0]),
            nombre=fila[1],
            direccion=fila[2] if len(fila) > 2 else None,
            zona=fila[3] if len(fila) > 3 else None,
            telefono=fila[4] if len(fila) > 4 else None,
            prioridad=int(fila[5] or 0) if len(fila) > 5 else 50,
            activo=bool(fila[6]) if len(fila) > 6 else True,
            horario_comida=fila[7] if len(fila) > 7 else None,
            horario_cena=fila[8] if len(fila) > 8 else None,
            ciudad_id=fila[9] if len(fila) > 9 else None,
            ciudad=fila[10] if len(fila) > 10 else None
        )

    def to_dict(self):

        return asdict(self)
