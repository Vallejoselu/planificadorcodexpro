# Planificador Delivery Pro

Planificador Delivery Pro es una aplicacion de escritorio para Windows creada con PySide6 y SQLite. Permite gestionar repartidores, restaurantes, turnos, calendarios semanales, exportaciones, estadisticas y un asistente local basado en reglas.

Version actual: 2.2.0

## Requisitos para desarrollo

- Windows 10 o superior.
- Python 3.11 o superior.
- Dependencias de `requirements.txt`.

Instalacion desde codigo fuente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Iniciar la aplicacion

Desde la carpeta del proyecto:

```powershell
python main.py
```

En desarrollo, la base de datos se usa desde `delivery.db` dentro del proyecto. En el ejecutable de Windows, los datos del usuario se guardan en:

```text
%LOCALAPPDATA%\PlanificadorDeliveryPro\delivery.db
```

La aplicacion crea la base de datos si no existe y no sobrescribe una base existente.

## Ejecutar pruebas

```powershell
python -m unittest discover -s tests
```

Comprobacion de sintaxis:

```powershell
python -m compileall .
```

Comprobacion completa recomendada antes de entregar cambios:

```powershell
python check_project.py
```

## Flujo seguro de desarrollo

Antes de pedir o aceptar cambios:

1. Trabaja en una rama distinta de `main`.
2. Haz una copia de seguridad si la tarea afecta a la base de datos.
3. Implementa un unico cambio.
4. Anade o actualiza pruebas.
5. Ejecuta `python check_project.py`.
6. Revisa `git diff`.
7. No hagas commit, push, merge, tag ni release sin autorizacion.

Consulta tambien:

```text
AGENTS.md
docs\PLANTILLA_TAREA_CODEX.md
docs\FLUJO_GIT_SEGURO.md
```

## Funciones principales

- Gestion de repartidores con contratos de 10, 20, 25, 30, 35 y 40 horas.
- Descansos semanales validados: lunes-martes, martes-miercoles, miercoles-jueves y jueves-viernes.
- Disponibilidad semanal por comidas, cenas, ambos o no disponible.
- Gestion de restaurantes con zona, direccion, telefono, estado, horarios y repartidores fijos.
- Gestion de turnos de comida, cena, turno partido y personalizados.
- Calendario semanal con varias coberturas por dia y turno.
- Vista de cuadrante por empleado con contrato, libres, comidas, cenas,
  dobles y horarios visibles.
- Asignacion opcional de repartidor en calendario.
- Generador de horarios con restricciones de contrato, descanso, disponibilidad, vacaciones y bajas.
- Asistente local para consultas sobre horas, descansos, disponibilidad, cobertura y simulaciones.
- Exportacion a Excel, PDF y CSV.
- Copia de cuadrantes entre semanas y plantillas reutilizables.
- Demanda configurable por restaurante, zona y ciudad con prioridad documentada.
- Panel de alertas del cuadrante e historial de acciones importantes.
- Importacion de repartidores, restaurantes, disponibilidad, vacaciones y bajas.
- Exportacion ICS, resumen por email, delivery JSON y webhook generico simulado.
- Credenciales externas por referencia y visor de sincronizaciones recientes.
- Reglas configurables preparadas y aplicadas de forma controlada al motor.
- Panel de estadisticas.
- Temas claro y oscuro.
- Arquitectura preparada para integraciones futuras con Shipday, Glovo, Uber y APIs genericas.
- Arquitectura preparada para futuras actualizaciones sin servidor activo todavia.

## Copias de seguridad

Antes de pruebas reales o cambios importantes, cierra la aplicacion y copia el archivo de base de datos:

```text
%LOCALAPPDATA%\PlanificadorDeliveryPro\delivery.db
```

Guarda la copia con fecha, por ejemplo:

```text
delivery-2026-07-10.db
```

Para restaurar una copia, cierra la aplicacion, sustituye `delivery.db` por la copia elegida y vuelve a iniciar.

En desarrollo, el archivo equivalente es `delivery.db` en la carpeta del proyecto.

Tambien puedes crear una copia con:

```powershell
python scripts\backup_database.py
```

Para restaurar, usa:

```powershell
python scripts\restore_database.py
```

La restauracion pide seleccion y confirmacion explicita.

## Datos de demostracion

Los datos de demostracion estan separados de la base real en:

```text
resources\demo\demo_data.sql
```

No se cargan automaticamente. Usalos solo sobre una base de datos de prueba o una copia.

## Crear ejecutable de Windows

Instala dependencias y ejecuta:

```powershell
.\build_windows.ps1 -Clean
```

El ejecutable se genera en:

```text
dist\PlanificadorDeliveryPro\PlanificadorDeliveryPro.exe
```

La carpeta completa `dist\PlanificadorDeliveryPro` debe copiarse junta. No copies solo el `.exe`, porque necesita los recursos incluidos en la distribucion.

## Crear instalador de Windows

Con Inno Setup 6 instalado, ejecuta:

```powershell
.\build_installer.ps1 -Clean
```

El instalador se genera en:

```text
installer_output\PlanificadorDeliveryPro-Setup-2.2.0.exe
```

## Limitaciones conocidas

- Las integraciones reales con Shipday, Glovo, Uber y APIs futuras estan preparadas, pero no conectan todavia con servicios externos.
- El webhook generico puede prepararse y simular payloads, pero no realiza llamadas obligatorias.
- El asistente es local y basado en reglas; no usa IA externa ni lenguaje natural avanzado.
- Las simulaciones no se aplican automaticamente a la base de datos.
- El sistema de actualizaciones esta preparado, pero no hay servidor ni canal de descarga configurado.
- Los datos demo son ficticios y no representan una operativa real completa.

## Archivos que no deben publicarse

No subas bases de datos reales, copias de seguridad, carpetas `dist`, `build`, entornos virtuales ni archivos temporales.
