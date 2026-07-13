# CHANGELOG

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
