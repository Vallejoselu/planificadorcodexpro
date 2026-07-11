# Plantilla de tarea para Codex

Usar esta plantilla antes de pedir cambios al proyecto.

## Objetivo unico

Describe una sola meta concreta.

Ejemplo:

```text
Corregir la validacion de descansos en el formulario de repartidores.
```

## Archivos permitidos

Lista los archivos que Codex puede tocar.

```text
database/database.py
views/nuevo_repartidor.py
tests/test_descansos_reglas.py
```

## Archivos que no deben tocarse

Lista los archivos o carpetas fuera de alcance.

```text
services/planificador.py
resources/styles/
delivery.db
```

## Reglas de negocio afectadas

Indica las reglas que deben respetarse.

```text
- Descansos solo lunes-martes, martes-miercoles, miercoles-jueves y jueves-viernes.
- Nunca descansos en sabado o domingo.
```

## Criterios de aceptacion

Describe como sabras que el trabajo esta terminado.

```text
- El formulario no muestra viernes, sabado ni domingo.
- El segundo dia se calcula automaticamente.
- Las pruebas de descansos pasan.
```

## Pruebas obligatorias

Lista las pruebas nuevas o existentes que deben ejecutarse.

```text
python -m unittest discover -s tests
python check_project.py
```

## Validacion final

Antes de entregar:

```text
- Ejecutar todas las pruebas.
- Ejecutar python check_project.py.
- Revisar que delivery.db no cambio.
- Revisar git diff.
```

## Resumen de cambios

Al finalizar, Codex debe indicar:

```text
- Archivos creados.
- Archivos modificados.
- Pruebas ejecutadas.
- Resultado de pruebas.
- Limitaciones pendientes.
```

## Prohibicion de commit y push

No hacer commit, push, merge, tag ni release sin autorizacion expresa.
