# Guia De Uso

Esta guia explica el flujo completo de Planificador Delivery Pro. La idea es
que puedas usar la aplicacion sin tener que entender el codigo.

## 1. Que Hace La Aplicacion

Planificador Delivery Pro ayuda a crear cuadrantes semanales para repartidores.
Gestiona:

- ciudades;
- restaurantes;
- turnos;
- repartidores;
- disponibilidad;
- descansos;
- demanda de repartidores;
- cuadrantes;
- alertas;
- exportaciones;
- backups.

La aplicacion necesita datos bien configurados. Si faltan restaurantes,
repartidores, turnos o demanda, el generador no puede hacer magia.

## 2. Orden Recomendado

1. Entra en **Puesta en marcha**.
2. Si hay datos de prueba, pulsa **Empezar de cero**.
3. Crea ciudades.
4. Crea restaurantes y asigna cada restaurante a una ciudad.
5. Configura turnos.
6. Configura repartidores.
7. Revisa disponibilidad y descansos.
8. Configura demanda.
9. Entra en **Cuadrantes**.
10. Pulsa **Comprobar configuracion**.
11. Pulsa **Generar cuadrante**.
12. Revisa alertas.
13. Ajusta manualmente solo si hace falta.
14. Publica o exporta.

## 3. Empezar De Cero

La pantalla **Puesta en marcha** tiene el boton **Empezar de cero**.

Sirve para limpiar datos operativos y empezar una configuracion nueva. Antes de
hacerlo, la app crea un backup automatico.

Limpia o desactiva:

- repartidores;
- restaurantes;
- ciudades;
- turnos;
- demandas;
- cuadrantes guardados;
- publicaciones;
- sincronizaciones.

No borra la estructura de la base de datos.

## 4. Repartidores

Cada repartidor deberia tener:

- nombre;
- horas contratadas;
- ciudad principal;
- restaurante principal, si aplica;
- restaurantes autorizados;
- ciudades autorizadas;
- disponibilidad semanal;
- descanso;
- maximo de horas diarias;
- maximo de dias consecutivos;
- horas complementarias permitidas.

Si un repartidor tiene un dia como **No disponible**, no deberia asignarse ese
dia.

## 5. Ciudades Y Restaurantes

Cada restaurante pertenece a una ciudad. Esto permite ver cuadrantes por local
y preparar vistas globales por ciudad.

La zona sigue siendo util para agrupar restaurantes dentro de una ciudad o para
priorizar repartidores por cercania.

## 6. Turnos

Hay dos conceptos:

- **Turnos globales**: turnos generales de la aplicacion.
- **Turnos propios de restaurante**: horarios concretos de cada restaurante.

Para una empresa real, lo mas importante son los turnos propios por
restaurante, porque cada local puede tener horarios distintos.

## 7. Demanda

La demanda indica cuantos repartidores hacen falta.

La prioridad recomendada es:

1. demanda por restaurante;
2. demanda por zona;
3. demanda por ciudad;
4. demanda por defecto.

Si una demanda pide 14 repartidores, el cuadrante debe crear 14 plazas. Si solo
puede cubrir 11, debe mostrar que faltan 3 y explicar el motivo.

## 8. Cuadrantes

La pantalla **Cuadrantes** tiene varias vistas:

- **Semana**: dias y turnos.
- **Por local**: restaurantes y dias.
- **Por empleado**: repartidores por filas y dias por columnas.

La vista por empleado es la mas facil para revisar una semana como si fuera una
hoja de Excel.

## 9. Significado De Colores Y Textos

- **LIBRE**: el repartidor no trabaja ese dia.
- **COMIDA**: tiene turno de comida.
- **CENA**: tiene turno de cena.
- **DOBLE**: trabaja comida y cena.
- **-**: esta disponible, pero no tiene turno asignado.
- **Sin repartidor**: existe una plaza, pero todavia no hay persona asignada.

## 10. Alertas

Las alertas no siempre significan que la app fallo. Muchas veces significan que
falta configuracion.

Ejemplos:

- restaurante sin demanda;
- turno sin cubrir;
- asignacion sin repartidor;
- repartidor con horas pendientes;
- horas extra;
- conflicto por vacaciones o bajas.

## 11. Exportar

Cuando el cuadrante este revisado, puedes exportarlo. La app prepara salidas a:

- Excel;
- PDF;
- CSV;
- ICS;
- email;
- integraciones futuras.

## 12. Backups Y Datos

La pantalla **Configuracion** muestra la ruta de datos local. En el ejecutable,
la base esta en:

```text
%LOCALAPPDATA%\PlanificadorDeliveryPro\delivery.db
```

Antes de restaurar o empezar de cero, crea copia de seguridad.

## 13. Flujo Diario Recomendado

1. Abrir la app.
2. Revisar Puesta en marcha.
3. Revisar demanda.
4. Generar cuadrante.
5. Revisar alertas.
6. Corregir datos de base, no solo pintar encima.
7. Publicar o exportar.

