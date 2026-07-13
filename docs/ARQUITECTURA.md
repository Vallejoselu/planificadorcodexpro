# Arquitectura

Este documento resume la arquitectura tecnica actual de Planificador Delivery
Pro tras las fases de preparacion de la version 2.0.

## Capas

La direccion recomendada de dependencias es:

```text
views -> services -> repositories -> database
                 -> services.rules
                 -> models
```

Las vistas deben encargarse de mostrar datos, recoger acciones del usuario y
refrescar la pantalla. No deben decidir reglas laborales ni transformar datos
profundamente.

Los servicios coordinan casos de uso de aplicacion. Ejemplos actuales:

- `CuadrantesService`: generar, preparar, guardar y presentar cuadrantes.
- `RepartidoresService`: reglas de presentacion y validacion de repartidores.
- `RestaurantesService`: datos preparados para vistas de restaurantes.
- `TurnosService`: operaciones de turnos.
- `PlanningEngine`: entrada publica del motor de planificacion.

Los repositorios encapsulan lectura y escritura de datos. En esta fase siguen
delegando internamente en la fachada `database.database`, pero las vistas y
servicios nuevos deben depender de repositorios, no de funciones sueltas de base
de datos.

Los modelos de dominio viven en `models/` y representan conceptos del negocio:
repartidor, restaurante, turno, calendario, disponibilidad y ausencia.

Las reglas comunes viven en `services/rules/`:

- `disponibilidad.py`
- `descansos.py`
- `ausencias.py`
- `candidatos.py`
- `horas.py`

El asistente y el planificador deben reutilizar estas reglas para mantener
respuestas coherentes.

## Base De Datos

La base de datos esta separada en:

- `database/connection.py`: abre conexiones SQLite con `PRAGMA foreign_keys=ON`.
- `database/schema.py`: constantes y definicion de estructura.
- `database/migrations.py`: creacion inicial y migraciones idempotentes.
- `database/database.py`: fachada de compatibilidad.

`database.database` no debe crecer como segunda fuente de verdad. Se mantiene
por compatibilidad con:

- scripts de arranque y backup;
- pruebas antiguas de migracion;
- repositorios que aun delegan en funciones existentes;
- funciones legacy usadas por versiones anteriores de la app.

## Compatibilidad Legacy

Estas piezas siguen existiendo deliberadamente:

- `database.database`: fachada historica de base de datos.
- `services.rule_engine`: reexporta reglas desde `services.rules.*`.
- `services.planificador.generar_horarios`: entrada legacy que delega en
  `PlanningEngine`.
- Metodos de repositorio como `crear`, `actualizar`, `desactivar`,
  `listar_activos` y `listar_todos`: API estable para vistas y servicios.

No deben eliminarse sin una migracion especifica y pruebas de compatibilidad.

## Estado De Imports

Las vistas principales no importan `database.database` ni `services.rule_engine`.
El estado actual es:

- `views/cuadrantes.py` usa `CuadrantesService`.
- `views/repartidores.py` usa `RepartidoresService`.
- `views/restaurantes.py` usa `RestaurantesService`.
- `views/turnos.py` usa `TurnosService`.
- `views/estadisticas.py` usa `services.estadisticas`.
- `views/exportaciones.py` usa `services.exportador`.
- `views/asistente.py` usa `services.asistente_horarios`.
- formularios de configuracion usan repositorios o servicios segun su alcance.

Imports directos restantes de `database.database` fuera de tests:

- `main.py` y `database/init_db.py`: arranque y creacion de base.
- `scripts/backup_database.py` y `scripts/restore_database.py`: utilidades.
- `repositories/*`: fachada interna pendiente de vaciar.
- `services/estadisticas.py`: aun consulta ausencias con SQL propio.

## Deuda Pendiente

Tareas tecnicas recomendadas para fases posteriores:

- Mover SQL real desde `database.database` a repositorios.
- Crear consultas de lectura de ausencias en `AusenciasRepository` y usarlas
  desde `services.estadisticas`.
- Reducir gradualmente tests que importan `database.database` a favor de
  repositorios cuando no esten probando migraciones o compatibilidad.
- Mantener `services.rule_engine` solo como modulo de compatibilidad hasta que
  no queden imports historicos.
- Evitar que nuevas vistas importen reglas, base de datos o planificador
  directamente.

## Pruebas

La suite cubre capas principales:

- modelos;
- repositorios;
- servicios de cuadrantes;
- reglas de disponibilidad y descansos;
- motor de planificacion;
- exportacion;
- asistente y coherencia con planificador;
- migraciones y base temporal.

Antes de fusionar cambios estructurales se debe ejecutar:

```text
python -m unittest discover -s tests
python check_project.py
python -m compileall .
git diff --check
```
