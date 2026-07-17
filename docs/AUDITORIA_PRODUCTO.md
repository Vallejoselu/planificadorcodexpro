# Auditoria De Producto

Revision honesta del estado actual de Planificador Delivery Pro y de lo que
conviene mejorar antes de considerarla una aplicacion sencilla y profesional.

## Diagnostico General

La aplicacion ya tiene muchas piezas importantes: base de datos local, modelo
multiciudad, demanda, generador, cuadrantes, exportaciones, backups,
diagnostico, integraciones preparadas y pruebas.

El problema principal ya no es falta de funciones. El problema es exceso de
funciones visibles al mismo tiempo y falta de una experiencia guiada.

## Lo Que Mantendria

- Puesta en marcha como checklist principal.
- Vista por empleado en cuadrantes.
- Backups y diagnostico de datos.
- Demanda por restaurante, zona y ciudad.
- Bloqueo de asignaciones en dias no disponibles.
- Exportacion a Excel/PDF/CSV.
- Base de datos local por usuario.

## Lo Que Simplificaria

- Configuracion: separar en pestanas o secciones plegables.
- Cuadrantes: reducir botones visibles y mover acciones avanzadas a un menu.
- Integraciones: ocultar Shipday/Glovo/Uber mientras no tengan uso real.
- Reglas: mostrar solo las reglas que realmente afectan al motor.
- Asistente: mantenerlo como ayuda, no como centro de operacion.

## Lo Que Corregiria Primero

1. Revisar que el generador no cree plazas sin sentido si no hay demanda real.
2. Mejorar los mensajes de Puesta en marcha para que indiquen exactamente que
   crear y en que pantalla.
3. Revisar los colores de todas las tablas en tema oscuro.
4. Mantener Cuadrantes con modo simple por defecto y modo avanzado bajo demanda.
5. Validar que la vista por empleado sea la vista principal para usuarios no
   tecnicos.
6. Asegurar que "Eliminar" siempre sea "Desactivar" o "Quitar asignacion",
   segun corresponda.
7. Revisar todos los formularios largos para que tengan scroll y botones
   siempre visibles.

## Lo Que Quitaria U Ocultaria

- Integraciones reales no usadas en el dia a dia.
- Controles avanzados de sincronizacion si el usuario no los necesita.
- Columnas tecnicas en tablas principales.
- Opciones que existen solo porque estan preparadas para futuro, pero no
  ayudan a generar cuadrantes ahora.

No significa borrar el codigo. Significa ocultarlo detras de un modo avanzado.

## Riesgos Actuales

- El usuario puede pensar que "Sin repartidor" es un error raro, cuando es una
  plaza pendiente.
- Hay demasiados botones en Cuadrantes.
- Configuracion mezcla tema, backups, email, integraciones y demanda.
- Si se cargan datos demo o datos de prueba, no queda claro como volver a una
  empresa limpia.
- La aplicacion puede parecer mas compleja de lo que realmente necesita ser.

## Propuesta De Roadmap

### Fase A: Claridad

- Guia de uso dentro de la app.
- Modo simple en Cuadrantes.
- Modo simple en Configuracion.
- Mensajes claros de Puesta en marcha.
- Colores consistentes.

### Fase B: Flujo Profesional

- Asistente de configuracion paso a paso.
- Pantalla de demanda mas clara.
- Resumen antes de generar.
- Resumen despues de generar.

### Fase C: Motor

- Validacion final obligatoria del cuadrante.
- Explicaciones por cada plaza sin cubrir.
- Puntuacion visible de candidatos.
- Configuracion de reglas solo cuando este estabilizada.

### Fase D: Entrega

- Instalador estable.
- Guia rapida en README.
- Release con changelog claro.
- Prueba de instalacion limpia y actualizacion.

## Conclusion

La aplicacion puede llegar a ser profesional, pero necesita menos ruido visual y
mas flujo guiado. La prioridad no deberia ser anadir mas funciones, sino hacer
que las funciones actuales sean evidentes, previsibles y faciles de usar.
