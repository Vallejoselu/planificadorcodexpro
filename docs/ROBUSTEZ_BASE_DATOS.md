# Robustez De Base De Datos

Fase 11 de preparacion para datos reales.

## Objetivo

Reducir riesgo al instalar la aplicacion en equipos con bases antiguas o datos
parcialmente invalidos.

## Diagnostico

La app dispone de diagnostico basico mediante:

```python
from database.database import diagnosticar_base_datos

diagnostico = diagnosticar_base_datos()
```

El diagnostico revisa:

- `PRAGMA integrity_check`;
- `PRAGMA foreign_key_check`;
- `schema_version`;
- indices esperados;
- restaurantes sin ciudad;
- repartidores con horas contratadas no validas;
- descansos antiguos no validos;
- demandas invalidas;
- demandas duplicadas;
- asignaciones duplicadas exactas en calendario.

El resultado tiene esta forma:

```python
{
    "ok": True,
    "errores": [],
    "advertencias": [],
    "info": []
}
```

## Reparacion Basica

La reparacion conservadora se ejecuta con:

```python
from database.database import reparar_base_datos

resultado = reparar_base_datos()
```

La reparacion:

- ejecuta migraciones idempotentes;
- crea `schema_version` si falta;
- crea indices esperados;
- crea la ciudad tecnica `Sin ciudad` si falta;
- asocia restaurantes antiguos sin ciudad a `Sin ciudad`;
- rellena semana tecnica `1970-01-05` en calendario antiguo;
- desactiva demandas activas duplicadas conservando la primera;
- elimina asignaciones duplicadas exactas de calendario.

No corrige automaticamente:

- horas contratadas fuera de los valores permitidos;
- descansos antiguos no validos;
- demandas con fecha/dia mal configurados;
- claves foraneas rotas.

Esos casos quedan como advertencia o error para correccion manual.

## Indices Revisados

Indices esperados tras migracion:

- `idx_calendario_semana_unico`
- `idx_calendario_semana_lookup`
- `idx_demanda_restaurante_fecha_unica`
- `idx_demanda_restaurante_dia_unico`
- `idx_demanda_restaurante_lookup`
- `idx_turnos_turno_restaurante_unico`
- `idx_restaurantes_ciudad_id`
- `idx_restaurante_turnos_restaurante`
- `idx_restaurante_repartidores_restaurante`
- `idx_disponibilidad_repartidor`
- `idx_descansos_repartidor_activo`
- `idx_vacaciones_repartidor_activo`
- `idx_bajas_repartidor_activa`

## Pruebas

Cobertura añadida en:

```text
tests/test_database_robustez.py
```

Casos cubiertos:

- diagnostico limpio en base nueva;
- mensajes claros para datos antiguos invalidos;
- migracion/reparacion de base antigua con duplicados;
- idempotencia de reparacion;
- no duplicar `Sin ciudad`;
- deteccion de claves foraneas rotas.
