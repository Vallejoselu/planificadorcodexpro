# Prioridad De Demanda

Este documento fija la regla que debe usar el motor cuando varias demandas
pueden aplicar al mismo restaurante, turno y dia.

## Orden Por Alcance

La demanda mas especifica sustituye a las mas generales. No se suman.

```text
Restaurante > Zona > Ciudad > Demanda por defecto
```

Ejemplo:

- restaurante BK Centro pide 3 repartidores;
- zona Centro pide 5 repartidores;
- ciudad Santiago pide 8 repartidores;
- demanda por defecto pide 1 repartidor.

Para BK Centro se usan 3 repartidores, porque la demanda de restaurante tiene
prioridad. No se calcula 3 + 5 + 8 + 1.

## Orden Por Periodo

Dentro del mismo alcance, una fecha concreta sustituye al dia semanal.

```text
Fecha concreta > Dia de semana
```

Ejemplo:

- lunes normal: zona Centro pide 4 repartidores;
- 2026-07-20: zona Centro pide 6 repartidores.

Si el lunes de la semana generada es 2026-07-20, se usan 6 repartidores. No se
suman 4 y 6.

## Regla Completa

El motor debe resolver la demanda en este orden:

1. Restaurante con fecha concreta.
2. Restaurante por dia de semana.
3. Zona con fecha concreta.
4. Zona por dia de semana.
5. Ciudad con fecha concreta.
6. Ciudad por dia de semana.
7. Demanda por defecto con fecha concreta.
8. Demanda por defecto por dia de semana.

Si ninguna demanda aplica, no se crea cobertura para ese turno desde demanda
configurada.

## Demanda Cero

Una demanda con valor `0` es una configuracion valida. Significa que no se
necesitan repartidores para ese alcance, turno y periodo.

No debe interpretarse como falta de configuracion y debe poder sustituir a una
demanda mas general mayor que cero.

Ejemplo:

- ciudad Santiago pide 4 repartidores los lunes;
- zona Centro pide 0 repartidores los lunes.

Para los restaurantes de la zona Centro se usan 0 repartidores porque zona es
mas especifica que ciudad.

## Fuente De Verdad

La prioridad tecnica vive en `services/rules/demanda.py`:

- `PRIORIDAD_NIVELES_DEMANDA`
- `PRIORIDAD_PERIODOS_DEMANDA`
- `seleccionar_demanda_prioritaria()`

Las fases posteriores deben reutilizar esas funciones en lugar de reconstruir
la prioridad dentro de vistas, repositorios o consultas sueltas.
