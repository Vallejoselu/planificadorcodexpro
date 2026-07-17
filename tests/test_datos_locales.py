import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.datos_locales import (
    crear_backup,
    diagnosticar_datos,
    exportar_base,
    importar_base,
    informacion_almacenamiento,
    listar_backups,
    reparar_datos,
    restaurar_backup,
    resumen_diagnostico,
    validar_base_sqlite,
    validar_restauracion
)
from utils.paths import (
    DATA_DIR_ENV,
    database_path,
    migrate_legacy_database_if_needed,
    user_data_dir
)


class TestDatosLocales(unittest.TestCase):

    def test_ruta_datos_usa_directorio_configurable(self):

        with tempfile.TemporaryDirectory() as temporal:
            with patch.dict(os.environ, {DATA_DIR_ENV: temporal}):

                self.assertEqual(user_data_dir(), Path(temporal))
                self.assertEqual(database_path(), Path(temporal) / "delivery.db")

    def test_migra_base_legacy_si_no_existe_destino(self):

        with tempfile.TemporaryDirectory() as temporal:

            legacy = Path(temporal) / "legacy.db"
            destino = Path(temporal) / "datos" / "delivery.db"
            self.crear_base_minima(legacy, valor="legacy")

            migrada = migrate_legacy_database_if_needed(destino, legacy)

            self.assertTrue(migrada)
            self.assertTrue(destino.exists())
            self.assertEqual(self.leer_valor(destino), "legacy")

            self.crear_base_minima(legacy, valor="nuevo")
            self.assertFalse(migrate_legacy_database_if_needed(destino, legacy))
            self.assertEqual(self.leer_valor(destino), "legacy")

    def test_backup_exportacion_y_restauracion(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            exportada = Path(temporal) / "exportada.db"
            self.crear_base_minima(ruta, valor="actual")

            backup = crear_backup(ruta_bd=ruta)
            destino = exportar_base(exportada, ruta_bd=ruta)

            self.assertTrue(backup.exists())
            self.assertEqual(destino, exportada)
            self.assertEqual(self.leer_valor(exportada), "actual")

            self.crear_base_minima(exportada, valor="restaurada")
            resultado = restaurar_backup(exportada, ruta_bd=ruta)

            self.assertEqual(self.leer_valor(ruta), "restaurada")
            self.assertTrue(resultado["respaldo"].exists())
            self.assertIn("validacion", resultado)

    def test_listar_backups_recientes(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            self.crear_base_minima(ruta, valor="actual")
            crear_backup(ruta_bd=ruta)
            crear_backup(ruta_bd=ruta)

            backups = listar_backups(ruta_bd=ruta)

            self.assertEqual(len(backups), 2)
            self.assertTrue(backups[0]["ruta"].exists())
            self.assertGreaterEqual(
                backups[0]["modificado"],
                backups[1]["modificado"]
            )

    def test_validar_restauracion_migra_copia_sin_tocar_origen(self):

        with tempfile.TemporaryDirectory() as temporal:

            origen = Path(temporal) / "origen.db"
            self.crear_base_minima(origen, valor="actual")

            validacion = validar_restauracion(origen)

            self.assertIn("resumen", validacion)
            conexion = sqlite3.connect(origen)
            tablas = {
                fila[0]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
            }
            conexion.close()
            self.assertEqual(tablas, {"prueba"})

    def test_diagnosticar_y_reparar_datos_crea_backup(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            self.crear_base_minima(ruta, valor="actual")

            diagnostico = diagnosticar_datos(ruta)
            reparacion = reparar_datos(ruta)

            self.assertIn("resumen", diagnostico)
            self.assertIn("resumen", reparacion)
            self.assertTrue(reparacion["respaldo"].exists())

    def test_resumen_diagnostico_prioriza_errores(self):

        self.assertEqual(
            resumen_diagnostico({
                "errores": [],
                "advertencias": []
            }),
            "Base de datos correcta."
        )
        self.assertIn(
            "Revisar",
            resumen_diagnostico({
                "errores": [],
                "advertencias": ["algo"]
            })
        )
        self.assertIn(
            "Critico",
            resumen_diagnostico({
                "errores": ["algo"],
                "advertencias": []
            })
        )

    def test_importar_rechaza_archivo_no_sqlite(self):

        with tempfile.TemporaryDirectory() as temporal:

            origen = Path(temporal) / "archivo.db"
            destino = Path(temporal) / "delivery.db"
            origen.write_text("no es sqlite", encoding="utf-8")

            with self.assertRaises(ValueError):

                importar_base(origen, ruta_bd=destino)

    def test_informacion_almacenamiento_describe_ruta(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            self.crear_base_minima(ruta, valor="actual")

            info = informacion_almacenamiento(ruta)

            self.assertEqual(info["ruta_bd"], ruta)
            self.assertTrue(info["existe"])
            self.assertGreater(info["tamano_bytes"], 0)

    def test_validar_base_sqlite_acepta_base_existente(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            self.crear_base_minima(ruta)

            self.assertTrue(validar_base_sqlite(ruta))

    def crear_base_minima(self, ruta, valor="ok"):

        ruta.parent.mkdir(parents=True, exist_ok=True)
        conexion = sqlite3.connect(ruta)
        conexion.execute("DROP TABLE IF EXISTS prueba")
        conexion.execute("CREATE TABLE prueba(valor TEXT)")
        conexion.execute("INSERT INTO prueba(valor) VALUES(?)", (valor,))
        conexion.commit()
        conexion.close()

    def leer_valor(self, ruta):

        conexion = sqlite3.connect(ruta)
        valor = conexion.execute("SELECT valor FROM prueba").fetchone()[0]
        conexion.close()
        return valor


if __name__ == "__main__":

    unittest.main()
