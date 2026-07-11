# TRANSFERENCIA

1. Fecha del paquete: 2026-07-10

2. Pruebas que pasan: 62/62. Tambien pasa python check_project.py.

3. Archivos incluidos:
- TRANSFERENCIA.md
- .github/workflows/tests.yml
- .gitignore
- AGENTS.md
- app_info.py
- build_installer.ps1
- build_windows.ps1
- CHANGELOG.md
- check_project.py
- database/database.py
- database/init_db.py
- docs/FLUJO_GIT_SEGURO.md
- docs/PLANTILLA_TAREA_CODEX.md
- installer/PlanificadorDeliveryPro.iss
- main.py
- models/actualizacion.py
- models/integracion.py
- models/repartidor.py
- PlanificadorDeliveryPro.spec
- README.md
- requirements.txt
- resources/demo/demo_data.sql
- resources/icons/app.ico
- resources/icons/app.svg
- resources/styles/dark.qss
- resources/styles/light.qss
- scripts/backup_database.py
- scripts/restore_database.py
- services/actualizaciones.py
- services/asistente_horarios.py
- services/asistente_simulacion.py
- services/constraints.py
- services/estadisticas.py
- services/exportador.py
- services/integraciones/base.py
- services/integraciones/generica.py
- services/integraciones/glovo.py
- services/integraciones/registro.py
- services/integraciones/shipday.py
- services/integraciones/uber.py
- services/planificador.py
- services/planning_engine.py
- services/rule_engine.py
- services/scheduler.py
- services/validators.py
- tests/test_actualizaciones.py
- tests/test_asistente_horarios.py
- tests/test_auditoria_flujo.py
- tests/test_cuadrantes_planning_engine.py
- tests/test_descansos_reglas.py
- tests/test_planning_engine.py
- tests/test_smoke_app.py
- tests/test_ui_theme_navigation.py
- ui/theme_manager.py
- ui/widgets.py
- utils/paths.py
- views/asistente.py
- views/configuracion.py
- views/cuadrantes.py
- views/estadisticas.py
- views/exportaciones.py
- views/inicio.py
- views/nuevo_repartidor.py
- views/nuevo_restaurante.py
- views/nuevo_turno.py
- views/repartidores.py
- views/restaurantes.py
- views/turnos.py
- views/ventana_principal.py

Archivos solicitados que no existen en el proyecto actual y por tanto no se incluyen:
- requirements-dev.txt
- install.ps1
- run.ps1
- run.bat
- setup.bat

4. Archivos modificados en las ultimas tareas:
- database/database.py
- views/cuadrantes.py
- tests/test_cuadrantes_planning_engine.py
- tests/test_auditoria_flujo.py
- services/rule_engine.py
- services/scheduler.py
- services/validators.py
- services/asistente_horarios.py
- views/nuevo_repartidor.py
- views/repartidores.py
- tests/test_descansos_reglas.py

5. Migraciones de base de datos existentes:
- Creacion idempotente de tablas principales: repartidores, restaurantes, restaurante_repartidores, contratos, descansos, disponibilidad, vacaciones, bajas, preferencias, turnos, calendario_semanal, integraciones_api e integraciones_eventos.
- Columnas idempotentes en restaurantes: horario_comida y horario_cena.
- Columna idempotente en calendario_semanal: repartidor_id.
- Columna idempotente en calendario_semanal: fecha_inicio_semana, con valor legado documentado 1970-01-05 para registros antiguos.
- Indice unico idx_calendario_semana_unico para evitar duplicados por semana, dia, turno, restaurante y repartidor.
- Semillas idempotentes para proveedores de integracion: Shipday, Glovo, Uber y API generica.
- La correccion de disponibilidad y descanso adicional no requiere cambio de esquema: el descanso adicional no necesario se representa sin descanso activo y la disponibilidad se mantiene en su tabla.

6. Archivos que no deben copiarse al repositorio:
- delivery.db
- backups/
- .venv/
- venv/
- env/
- __pycache__/
- *.pyc
- .pytest_cache/
- build/
- dist/
- installer_output/
- *.db
- *.db-shm
- *.db-wal
- *.log
- *.tmp
- .git/

7. Como comprobar que la transferencia se hizo correctamente:
- Descomprimir el ZIP en el repositorio Git real o en una carpeta limpia.
- Confirmar que no existen delivery.db, backups, build, dist, installer_output, .git, __pycache__, .pytest_cache ni archivos .pyc dentro del contenido copiado.
- Instalar dependencias con: python -m pip install -r requirements.txt
- Ejecutar las pruebas y comprobar que pasan 62 pruebas.
- Ejecutar python check_project.py y confirmar que todas las comprobaciones pasan.
- Iniciar la aplicacion y revisar que carga sin errores de importacion.

8. Comando para ejecutar las pruebas:
```powershell
python -m unittest discover -s tests
```

9. Comando para iniciar la aplicacion:
```powershell
python main.py
```
