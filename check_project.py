import ast
import hashlib
import importlib
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REAL_DB = ROOT / "delivery.db"
EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "build",
    "dist",
    "backups",
    "__pycache__",
    ".pytest_cache"
}


def main():

    sys.dont_write_bytecode = True
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    checks = [
        ("Sintaxis con compileall", check_compileall),
        ("Pruebas automatizadas", check_tests),
        ("Imports principales", check_imports),
        ("Arranque sin ventana bloqueada", check_app_smoke),
        ("Archivos no deseados", check_unwanted_files),
        ("Secretos evidentes", check_secrets),
        ("delivery.db sin cambios", check_delivery_db_unchanged),
        ("Pruebas con base temporal", check_tests_use_temp_db),
        ("Diagnostico de base temporal", check_database_diagnostics),
        ("Reglas criticas", check_business_rules)
    ]
    failures = []

    for title, func in checks:

        print(f"\n== {title} ==")

        try:

            func()

        except Exception as error:

            failures.append((title, str(error)))
            print(f"[ERROR] {error}")

        else:

            print("[OK]")

    if failures:

        print("\nComprobaciones fallidas:")

        for title, error in failures:

            print(f"- {title}: {error}")

        return 1

    print("\nTodas las comprobaciones han pasado.")
    return 0


def check_compileall():

    import compileall

    with tempfile.TemporaryDirectory() as temporal:

        previous = getattr(sys, "pycache_prefix", None)
        sys.pycache_prefix = temporal

        try:

            ok = compileall.compile_dir(
                ROOT,
                quiet=1,
                force=True,
                maxlevels=20
            )

        finally:

            sys.pycache_prefix = previous

    if not ok:

        raise RuntimeError("Hay archivos Python con errores de sintaxis.")


def check_tests():

    before = file_hash(REAL_DB)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True
    )
    print(result.stdout.strip())

    if result.stderr.strip():

        print(result.stderr.strip())

    after = file_hash(REAL_DB)

    if before != after:

        raise RuntimeError("delivery.db cambio durante las pruebas.")

    if result.returncode != 0:

        raise RuntimeError("Las pruebas automatizadas han fallado.")


def check_imports():

    modules = [
        "app_info",
        "main",
        "database.database",
        "services.planificador",
        "services.planning_engine",
        "services.rule_engine",
        "services.constraints",
        "services.validators",
        "services.scheduler",
        "services.asistente_horarios",
        "services.asistente_simulacion",
        "services.exportador",
        "views.ventana_principal",
        "ui.theme_manager"
    ]

    for module in modules:

        importlib.import_module(module)


def check_app_smoke():

    from PySide6.QtWidgets import QApplication

    import database.database as database
    from database.database import crear_base_datos
    from ui.theme_manager import ThemeManager
    from views.ventana_principal import VentanaPrincipal

    original = database.RUTA_BD

    with tempfile.TemporaryDirectory() as temporal:

        database.RUTA_BD = Path(temporal) / "delivery.db"

        try:

            crear_base_datos()
            app = QApplication.instance() or QApplication([])
            ThemeManager.set_theme("light")
            ventana = VentanaPrincipal()

            for pagina in ventana.paginas:

                ventana.mostrar_pagina(pagina)

            ventana.close()
            app.processEvents()

        finally:

            database.RUTA_BD = original


def check_unwanted_files():

    unwanted = []

    for path in ROOT.rglob("*"):

        if is_excluded(path):

            continue

        name = path.name.lower()

        if path.is_dir() and name in {"__pycache__", ".pytest_cache", ".venv", "venv", "env"}:

            unwanted.append(path)

        if path.is_file() and (
            name.endswith(".pyc")
            or name.endswith(".pyo")
            or name.endswith(".tmp")
        ):

            unwanted.append(path)

    if unwanted:

        raise RuntimeError(
            "Archivos no deseados: "
            + ", ".join(str(path.relative_to(ROOT)) for path in unwanted[:10])
        )


def check_secrets():

    pattern = re.compile(
        r"(?i)(api[_-]?key|secret|token|password|contrasena|contraseña)"
        r"\s*[:=]\s*['\"][^'\"]{8,}['\"]"
    )
    findings = []

    for path in iter_text_files():

        text = path.read_text(encoding="utf-8", errors="ignore")

        if pattern.search(text):

            findings.append(path)

    if findings:

        raise RuntimeError(
            "Posibles secretos encontrados: "
            + ", ".join(str(path.relative_to(ROOT)) for path in findings)
        )


def check_delivery_db_unchanged():

    before = file_hash(REAL_DB)

    if before != file_hash(REAL_DB):

        raise RuntimeError("delivery.db cambio durante la comprobacion.")


def check_tests_use_temp_db():

    forbidden = [
        'parents[1] / "delivery.db"',
        "parents[1] / 'delivery.db'",
        'Path("delivery.db")',
        "Path('delivery.db')"
    ]
    offenders = []

    for path in (ROOT / "tests").rglob("*.py"):

        text = path.read_text(encoding="utf-8", errors="ignore")

        if any(item in text for item in forbidden):

            offenders.append(path)

        if "VentanaPrincipal(" in text and "database.RUTA_BD" not in text:

            offenders.append(path)

    if offenders:

        unique = sorted({str(path.relative_to(ROOT)) for path in offenders})
        raise RuntimeError(
            "Pruebas sin aislamiento claro de base temporal: "
            + ", ".join(unique)
        )


def check_database_diagnostics():

    import database.database as database
    from database.database import crear_base_datos, diagnosticar_base_datos

    original = database.RUTA_BD

    with tempfile.TemporaryDirectory() as temporal:

        database.RUTA_BD = Path(temporal) / "delivery.db"

        try:

            crear_base_datos()
            diagnostico = diagnosticar_base_datos()

            if not diagnostico["ok"]:

                raise RuntimeError(
                    "Diagnostico de base temporal con incidencias: "
                    + "; ".join(
                        diagnostico["errores"] + diagnostico["advertencias"]
                    )
                )

        finally:

            database.RUTA_BD = original


def check_business_rules():

    from database.database import (
        HORAS_CONTRATO,
        validar_descanso,
        validar_horas_contratadas
    )
    from services.asistente_horarios import responder, solapa_turno
    from services.planificador import generar_horarios

    if tuple(HORAS_CONTRATO) != (10, 20, 25, 30, 35, 40):

        raise RuntimeError("Contratos permitidos incorrectos.")

    for descanso in (
        ("lunes", "martes"),
        ("martes", "miercoles"),
        ("miercoles", "jueves"),
        ("jueves", "viernes")
    ):

        validar_descanso(*descanso)

    for descanso in (
        ("viernes", "sabado"),
        ("sabado", "domingo"),
        ("domingo", "lunes")
    ):

        try:

            validar_descanso(*descanso)

        except ValueError:

            pass

        else:

            raise RuntimeError(f"Descanso invalido aceptado: {descanso}")

    for horas in HORAS_CONTRATO:

        validar_horas_contratadas(horas)

    resultado = generar_horarios(
        [{
            "id": 1,
            "nombre": "Ana",
            "horas": 10,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "descanso": ["lunes", "martes"],
            "disponibilidad": {
                "miercoles": ["comida", "noche"],
                "jueves": ["comida", "noche"],
                "viernes": ["comida", "noche"]
            }
        }],
        [{"id": 1, "nombre": "R1", "zona": "Ronda"}]
    )

    if resultado["resumen"][0]["horas"] > 10:

        raise RuntimeError("El generador supera las horas contratadas.")

    contexto = {
        "repartidores": [{
            "id": 1,
            "nombre": "Ana",
            "horas": 10,
            "zona": "Ronda",
            "doble_turno": 1,
            "puede_hasta_la_una": 1,
            "descanso": ["lunes", "martes"],
            "disponibilidad": {"viernes": ["comida", "noche"]},
            "vacaciones": [],
            "bajas": [],
            "preferencias": []
        }],
        "turnos": [{
            "id": 1,
            "tipo": "Cena",
            "nombre": "Cena",
            "hora_inicio": "20:00",
            "hora_fin": "23:30",
            "duracion": 3.5,
            "activo": 1
        }],
        "restaurantes": [{"id": 1, "nombre": "R1", "zona": "Ronda", "activo": 1}],
        "calendario": [],
        "asignaciones_repartidor": [{
            "repartidor_id": 1,
            "dia": "viernes",
            "turno_id": 1,
            "restaurante_id": 1,
            "duracion": 3.5,
            "hora_inicio": "20:00",
            "hora_fin": "23:30"
        }]
    }

    if not solapa_turno(contexto, contexto["repartidores"][0], "viernes", contexto["turnos"][0]):

        raise RuntimeError("No se detecta solapamiento.")

    before = repr(contexto)
    respuesta = responder("Que ocurre si Ana esta de vacaciones el viernes?", contexto)

    if "Simulacion" not in respuesta or repr(contexto) != before:

        raise RuntimeError("La simulacion modifica datos o no responde como simulacion.")


def iter_text_files():

    for path in ROOT.rglob("*"):

        if is_excluded(path) or not path.is_file():

            continue

        if path.suffix.lower() in {
            ".py",
            ".md",
            ".txt",
            ".ps1",
            ".yml",
            ".yaml",
            ".qss",
            ".sql",
            ".json"
        }:

            yield path


def is_excluded(path):

    parts = set(path.relative_to(ROOT).parts)
    return bool(parts & EXCLUDED_DIRS)


def file_hash(path):

    if not path.exists():

        return None

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(lambda: file.read(1024 * 1024), b""):

            digest.update(chunk)

    return digest.hexdigest()


if __name__ == "__main__":

    raise SystemExit(main())
