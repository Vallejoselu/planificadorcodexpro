from services.rules.candidatos import motivo_no_puede_trabajar


def explicar_regla_incumplida(repartidores, restaurante, dia, turno, fecha):

    motivos = {}

    for repartidor in repartidores:

        motivo = motivo_no_puede_trabajar(
            repartidor,
            restaurante,
            dia,
            turno,
            fecha
        )

        if not motivo:

            continue

        motivos[motivo] = motivos.get(motivo, 0) + 1

    detalle = [
        {
            "motivo": motivo,
            "cantidad": cantidad
        }
        for motivo, cantidad in sorted(
            motivos.items(),
            key=lambda item: (-item[1], item[0])
        )
    ]

    if not detalle:

        return {
            "principal": "sin candidatos disponibles",
            "detalle": []
        }

    return {
        "principal": detalle[0]["motivo"],
        "detalle": detalle
    }
