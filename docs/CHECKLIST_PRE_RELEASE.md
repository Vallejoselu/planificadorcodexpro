# Checklist Pre-Release

Esta checklist se ejecuta antes de generar un instalador nuevo. No anade
funcionalidad: sirve para confirmar que el flujo real de trabajo esta claro,
que no aparecen datos demo por sorpresa y que el cuadrante generado se puede
entender antes de entregarlo.

## 1. Preparar Entorno

Desde la carpeta del proyecto:

```powershell
git switch main
git pull --ff-only github main
git status
python scripts\validar_flujo_base_limpia.py
python -m compileall .
git diff --check
```

Resultado esperado:

- `git status` no muestra cambios pendientes.
- `delivery.db` no aparece versionada.
- La validacion rapida genera 14 asignaciones, 14 cubiertas y 0 pendientes.
- `compileall` y `git diff --check` terminan sin errores.

## 2. Probar Instalacion Limpia

Usar una base sin datos reales. Si la app ya tiene datos, hacer backup antes y
usar `Puesta en marcha > Empezar de cero`.

Comprobar:

- Inicio muestra claramente que faltan datos si la base esta vacia.
- Puesta en marcha explica que los datos minimos no crean repartidores demo.
- Crear datos minimos crea ciudad, restaurante, turnos y demanda base.
- La app queda sin repartidores hasta que el usuario los cree manualmente.
- Las pantallas de ciudades, restaurantes y turnos solo muestran elementos
  activos.

## 3. Crear Datos Reales Minimos

Crear manualmente:

- una ciudad;
- un restaurante asociado a la ciudad;
- turnos propios de comida y cena;
- demanda semanal para comida y cena;
- dos repartidores con contrato, libranzas y disponibilidad.

Comprobar:

- Las libranzas se configuran marcando dias como `No disponible`.
- No aparece el concepto antiguo de descanso adicional como decision principal.
- El restaurante no exige configurar demanda por fecha y por dia a la vez.
- Los formularios caben en pantalla y tienen desplazamiento si son largos.

## 4. Generar Primer Cuadrante

En `Cuadrantes`:

- pulsar `Comprobar configuracion`;
- generar cuadrante;
- revisar la vista previa antes de guardar;
- guardar solo si existen plazas y el resumen se entiende.

Comprobar:

- No se guardan vistas previas vacias.
- No hay repartidores asignados en dias `No disponible`.
- Las plazas sin repartidor se ven como pendientes, no como turnos correctos.
- El resumen muestra contrato, total de horas y horas complementarias usadas.
- La vista `Por empleado` muestra `LIBRE`, `COMIDA`, `CENA`, `DOBLE` o `-`.
- La vista `Semana` permite acciones manuales; `Por empleado` y `Por local`
  son vistas de revision.

## 5. Revisar Horas Y Alertas

Antes de publicar:

- revisar panel de alertas;
- revisar repartidores con horas pendientes;
- revisar repartidores con horas complementarias;
- confirmar que las horas complementarias estan permitidas y dentro del limite;
- confirmar que no hay turnos sin cubrir si el cuadrante se va a publicar.

No aceptar para release:

- texto cortado en mensajes importantes;
- colores que impidan leer el texto;
- botones que prometan borrar cuando solo desactivan;
- datos demo mezclados con datos reales;
- cuadrantes guardados sin plazas;
- asignaciones en dias libres.

## 6. Exportar Y Persistir

Comprobar:

- exportar Excel;
- exportar PDF;
- exportar CSV;
- cerrar la app;
- abrir de nuevo;
- confirmar que cuadrante, repartidores, restaurantes, turnos y demanda siguen
  guardados.

## 7. Generar Instalador

Solo despues de completar la validacion:

```powershell
.\build_installer.ps1 -Clean
```

El instalador debe generarse en:

```text
installer_output\PlanificadorDeliveryPro-Setup-2.2.0.exe
```

Antes de publicarlo en GitHub Releases, instalarlo en una base limpia y repetir
los pasos 2 a 6.
