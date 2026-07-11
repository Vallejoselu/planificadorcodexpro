# AGENTS.md

Instrucciones permanentes para cualquier agente que trabaje en Planificador Delivery Pro.

## Flujo seguro

- No trabajar directamente sobre la rama `main`.
- Cada tarea debe tener un unico objetivo.
- No realizar cambios ajenos a la tarea solicitada.
- No eliminar funciones existentes sin autorizacion expresa.
- No cambiar nombres de funciones publicas sin necesidad.
- No hacer commit, push, merge, tag ni release sin autorizacion.
- Mostrar siempre los archivos creados y modificados al finalizar.
- Revisar `git diff` antes de entregar cambios.

## Base de datos

- No modificar el esquema de la base de datos sin una migracion segura.
- Crear una copia de seguridad antes de cualquier migracion.
- No borrar ni reemplazar `delivery.db`.
- No incluir datos reales en pruebas.
- Usar bases de datos temporales para probar.
- Las simulaciones nunca deben modificar los datos reales.

## Pruebas y validacion

- Toda correccion de un error debe incluir una prueba que reproduzca ese error.
- Toda funcionalidad nueva debe incluir pruebas.
- Antes de finalizar una tarea deben pasar todas las comprobaciones.
- Ejecutar `python check_project.py` antes de entregar cambios.
- Si una comprobacion falla, informar del fallo y no ocultarlo.

## Reglas de negocio obligatorias

- Los contratos permitidos son 10, 20, 25, 30, 35 y 40 horas.
- Los descansos deben ser dos dias consecutivos.
- Solo se permiten estos descansos:
  - lunes-martes
  - martes-miercoles
  - miercoles-jueves
  - jueves-viernes
- Nunca permitir descansos en sabado o domingo.
- No asignar turnos durante el descanso.
- No permitir solapamientos.
- No superar las horas contratadas salvo autorizacion de horas complementarias.
- Las simulaciones nunca deben modificar los datos reales.

## Alcance de cambios

- Modificar solo los archivos necesarios para el objetivo de la tarea.
- No redisenar la arquitectura sin una tarea explicita.
- No cambiar el diseno visual salvo que el problema sea visual.
- No introducir dependencias nuevas sin justificarlas.
- No introducir claves API, tokens, contrasenas ni secretos.
