# CHANGELOG

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
