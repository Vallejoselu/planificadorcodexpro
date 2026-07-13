from dataclasses import dataclass, field


@dataclass(frozen=True)
class PuntuacionConfig:
    peso_restaurante_principal: float = 1
    peso_restaurante_autorizado: float = 1
    peso_ciudad_principal: float = 1
    peso_ciudad_autorizada: float = 1
    peso_apoyo_flexible: float = 1
    peso_preferencia: float = 1
    peso_horas_pendientes: float = 1
    peso_carga_relativa: float = 1
    peso_horas_complementarias: float = 1
    peso_desplazamiento: float = 1
    peso_diferencia_turnos: float = 1
    peso_horas_despues: float = 1


@dataclass(frozen=True)
class PuntuacionCandidato:
    valores: tuple
    detalle: dict = field(default_factory=dict)


@dataclass(frozen=True)
class IncidenciaValidacion:
    regla: str
    motivo: str
    dia: str = ""
    turno: str = ""
    restaurante: str = ""
    advertencia: bool = True

    def to_dict(self):

        return {
            "dia": self.dia,
            "turno": self.turno,
            "restaurante": self.restaurante,
            "motivo": self.motivo,
            "advertencia": self.advertencia,
            "regla": self.regla
        }
