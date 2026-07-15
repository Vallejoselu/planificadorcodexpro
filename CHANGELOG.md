# CHANGELOG

## 2.1.3 - Hotfix de cuadrantes por empleado

### Corregido

- El guardado de cuadrantes bloquea asignaciones en dias libres,
  descansos, vacaciones, bajas o dias sin disponibilidad.
- La validacion se aplica al generar, asignar manualmente, copiar semanas
  y aplicar plantillas antes de escribir en `calendario_semanal`.
- Las asignaciones manuales invalidas muestran aviso y no se guardan.

### Aniadido

- Nueva vista `Por empleado` en Cuadrantes con filas por repartidor,
  contrato semanal y columnas de lunes a domingo.
- Cada celda muestra `LIBRE`, `COMIDA`, `CENA`, `DOBLE` o `-` con los
  horarios reales y colores diferenciados.

### Validacion

- Se anadieron pruebas para dias no disponibles, bloqueo de asignacion
  manual, copia de semanas, plantillas y vista por empleado.

## 2.1.2 - Correccion de interfaz en cuadrantes

### Corregido

- La pantalla de Cuadrantes ya no comprime los controles superiores en una
  unica fila.
- Los filtros y las acciones del cuadrante se muestran en dos barras separadas
  con desplazamiento horizontal cuando la ventana no tiene suficiente ancho.

### Validacion

- Se anadio una prueba especifica para comprobar que la barra superior de
  Cuadrantes no comprime botones ni selectores.

## 2.1.1 - Correccion de dialogos responsivos

### Corregido

- Los dialogos largos de repartidores y restaurantes ahora se adaptan mejor a
  pantallas pequenas.
- Los formularios largos usan desplazamiento interno para que los botones de
  accion sigan siendo accesibles.

### Validacion

- Se anadieron pruebas especificas para comprobar que los dialogos usan scroll
  y respetan un alto maximo.

## 2.1.0 - Consolidacion Bloque 14

### Incluido

- Copia de cuadrantes entre semanas y plantillas reutilizables.
- Demanda ampliada por restaurante, zona y ciudad con prioridad formal:
  restaurante > zona > ciudad > defecto.
- Integracion de la prioridad de demanda en el generador de cuadrantes.
- Control de horas complementarias, alertas de uso y resumen por repartidor.
- Panel de alertas para turnos sin cubrir, horas pendientes, horas extra,
  restaurantes sin demanda, asignaciones sin repartidor y conflictos de
  vacaciones o bajas.
- Historial de acciones importantes: crear, editar, eliminar, generar,
  exportar y restaurar backup.
- Importacion de repartidores, restaurantes, disponibilidad, vacaciones y
  bajas desde Excel o CSV.
- Mejoras del asistente para consultas, simulaciones y explicaciones de por
  que una persona no puede cubrir un turno.
- Reglas configurables desde interfaz, con aplicacion controlada al motor:
  maximo de horas semanales, horas complementarias, desplazamiento, prioridad
  por zona, restaurante fijo y balance comidas/cenas.
- Integraciones preparadas: credenciales por referencia, exportacion ICS,
  resumen por email, delivery JSON, webhook generico simulado, registro de
  reintentos y visor de sincronizaciones.

### Consolidacion

- Actualizacion de version a 2.1.0.
- Revision de README y documentacion del Bloque 14.
- Preparacion de ejecutable, instalador, tag `v2.1.0` y release estable.

### Limitaciones conocidas

- Las integraciones reales con plataformas externas siguen sin llamadas
  obligatorias a APIs de terceros.
- El visor de sincronizaciones muestra registros y reintentos guardados, pero
  no ejecuta reintentos automaticos.

## 2.0.0 - Version 2.0

### Incluido

- Modelo multiciudad con ciudades, restaurantes por ciudad, turnos propios y demanda por restaurante.
- Generador de cuadrantes adaptado a demanda por ciudad, restaurante, dia y turno.
- Reglas de planificacion mas explicables para disponibilidad, descansos, ausencias, horas y candidatos.
- Servicios, repositorios y modelos de dominio para separar mejor interfaz, datos y negocio.
- Migraciones seguras con `schema_version` y claves foraneas activadas por conexion.
- Diagnostico y reparacion basica de base de datos para instalaciones con datos antiguos.
- Validacion funcional completa de flujos principales de la aplicacion.
- Mejoras de UX en mensajes, confirmaciones, estados vacios, indicadores de cuadrante y resumen de generacion.
- Instalador Windows generado con Inno Setup ademas del ejecutable PyInstaller.

### Compatibilidad

- Se conserva `delivery.db` y los cuadrantes existentes mediante migraciones idempotentes.
- Se mantiene `calendario_semanal` y las funciones legacy necesarias para vistas existentes.
- Los datos de usuario del ejecutable se guardan en `%LOCALAPPDATA%\PlanificadorDeliveryPro\delivery.db`.

### Limitaciones conocidas

- Las integraciones externas siguen preparadas, pero no realizan conexion real.
- El sistema de actualizaciones no tiene servidor remoto configurado.
- La prueba de instalacion requiere permisos suficientes para ejecutar el instalador de Windows.

## 1.0.0 - Primera version estable

### Incluido

- Gestion de repartidores, contratos, descansos y disponibilidad semanal.
- Gestion de restaurantes con horarios, zonas y repartidores fijos.
- Gestion de turnos de comida, cena, turno partido y personalizados.
- Calendario semanal con soporte para varias coberturas por dia y turno.
- Persistencia opcional del repartidor asignado en calendario.
- Generador de horarios con reglas de contrato, descansos, disponibilidad, vacaciones, bajas y solapamientos.
- Asistente local basado en reglas para consultar horarios, horas, descansos, disponibilidad y candidatos.
- Modo simulacion del asistente sin modificar la base real.
- Exportacion a Excel, PDF y CSV.
- Panel de estadisticas.
- Temas claro y oscuro.
- Arquitectura preparada para integraciones futuras con Shipday, Glovo, Uber y APIs genericas.
- Arquitectura preparada para comprobar y descargar futuras actualizaciones.
- Preparacion de empaquetado Windows con PyInstaller.

### Limitaciones conocidas

- Las integraciones externas estan preparadas, pero no implementan conexion real.
- El asistente no se conecta a ningun servicio externo.
- El sistema de actualizaciones no tiene servidor configurado.
- Las simulaciones no aplican cambios automaticamente.
- La distribucion 1.0.0 se genera como carpeta portable, no como instalador.
