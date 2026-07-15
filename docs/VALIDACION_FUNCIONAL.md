# Validacion Funcional Completa

Fase 10 de preparacion de Planificador Delivery Pro 2.0.

## Release 2.1.0

La release 2.1.0 consolida el Bloque 14 de mejoras funcionales. No anade una
funcionalidad nueva en esta fase; valida que las mejoras ya integradas conviven
correctamente:

- copia de cuadrantes y plantillas de semanas;
- demanda por restaurante, zona y ciudad;
- prioridad de demanda aplicada al generador;
- horas complementarias controladas;
- panel de alertas e historial de acciones;
- importaciones desde Excel/CSV;
- asistente mejorado y reglas configurables;
- exportacion ICS, email, delivery JSON, webhook generico, reintentos y visor
  de sincronizaciones.

La validacion funcional principal esta automatizada en:

```text
tests/test_validacion_funcional.py
```

La prueba usa una base de datos temporal, ejecuta la app en modo Qt offscreen y
no modifica `delivery.db`.

## Checklist

| Paso | Estado | Evidencia |
| --- | --- | --- |
| Crear repartidores | OK | Crea Ana, Luis y Marta con contratos, zonas, descansos y disponibilidad. |
| Crear restaurantes | OK | Crea BK Centro y BK Norte con zona, telefono y horarios. |
| Crear turnos | OK | Crea Comida y Cena con horas, color e intervalo horario. |
| Generar cuadrante semanal | OK | Usa `CuadrantesService.generar_cuadrante` y guarda la semana `2026-07-13`. |
| Editar cuadrante manualmente | OK | Reemplaza una asignacion de viernes comida y verifica persistencia. |
| Cambiar semana | OK | Guarda una asignacion en `2026-07-20` y confirma que `2026-07-13` no se pierde. |
| Exportar Excel | OK | Genera `cuadrante.xlsx` con tamano mayor que cero. |
| Exportar PDF | OK | Genera `cuadrante.pdf` con tamano mayor que cero. |
| Exportar CSV | OK | Genera `cuadrante.csv` con tamano mayor que cero. |
| Consultar asistente | OK | Pregunta candidatos para cubrir comida del viernes y recibe respuesta util. |
| Cambiar tema | OK | Cambia a tema oscuro y vuelve a claro comprobando `ThemeManager`. |
| Reiniciar app | OK | Crea `VentanaPrincipal`, navega paginas, reconstruye la app y verifica datos persistidos. |

## Comando Reproducible

```text
python -m unittest tests.test_validacion_funcional -v
```

Validacion completa recomendada antes de fusionar:

```text
python -m unittest discover -s tests
python check_project.py
python -m compileall .
git diff --check
```

## Alcance

Esta fase valida el flujo funcional completo desde la perspectiva de usuario,
pero sin ventanas interactivas reales. El objetivo es que el flujo sea
repetible en CI o en local sin tocar datos reales.

Queda fuera de alcance:

- verificacion visual pixel a pixel de cada pantalla;
- pruebas manuales con raton/teclado sobre una ventana visible;
- validacion de impresoras o visores externos de PDF/Excel.
