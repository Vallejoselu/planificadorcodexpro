from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Repartidor:

    id: int
    nombre: str
    horas: int
    zona: str | None
    doble_turno: bool
    puede_hasta_la_una: bool
    prioridad_comida: int
    prioridad_noche: int
    prioridad_grela: int
    descanso_inicio: str | None = None
    descanso_fin: str | None = None
    disponibilidad: dict[str, list[str]] = field(default_factory=dict)
    vacaciones: list[dict[str, Any]] = field(default_factory=list)
    bajas: list[dict[str, Any]] = field(default_factory=list)
    preferencias: list[dict[str, Any]] = field(default_factory=list)
    ciudad_principal_id: int | None = None
    restaurante_principal_id: int | None = None
    apoyo_flexible: bool = False
    horas_complementarias: int = 0
    max_horas_diarias: float = 10
    max_dias_consecutivos: int = 5
    ciudades_autorizadas: list[int] = field(default_factory=list)
    restaurantes_autorizados: list[int] = field(default_factory=list)
    activo: bool = True
    observaciones: str = ""

    @classmethod
    def from_row(cls, fila):

        return cls(
            id=int(fila[0]),
            nombre=fila[1],
            horas=int(fila[2]),
            zona=fila[3],
            doble_turno=bool(fila[4]),
            puede_hasta_la_una=bool(fila[5]),
            prioridad_comida=int(fila[6]),
            prioridad_noche=int(fila[7]),
            prioridad_grela=int(fila[8]),
            descanso_inicio=fila[9] if len(fila) > 9 else None,
            descanso_fin=fila[10] if len(fila) > 10 else None,
            disponibilidad=fila[11] if len(fila) > 11 and fila[11] else {},
            vacaciones=fila[12] if len(fila) > 12 and fila[12] else [],
            bajas=fila[13] if len(fila) > 13 and fila[13] else [],
            preferencias=fila[14] if len(fila) > 14 and fila[14] else [],
            ciudad_principal_id=fila[15] if len(fila) > 15 else None,
            restaurante_principal_id=fila[16] if len(fila) > 16 else None,
            apoyo_flexible=bool(fila[17]) if len(fila) > 17 else False,
            horas_complementarias=int(fila[18] or 0) if len(fila) > 18 else 0,
            max_horas_diarias=float(fila[19] or 0) if len(fila) > 19 else 10,
            max_dias_consecutivos=int(fila[20] or 0) if len(fila) > 20 else 5,
            ciudades_autorizadas=list(fila[21]) if len(fila) > 21 and fila[21] else [],
            restaurantes_autorizados=list(fila[22]) if len(fila) > 22 and fila[22] else []
        )

    def to_dict(self):

        return asdict(self)
