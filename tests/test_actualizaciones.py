import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from services.actualizaciones import ServicioActualizaciones, version_mayor


class TestActualizaciones(unittest.TestCase):

    def test_sin_servidor_configurado_informa_sin_error(self):

        servicio = ServicioActualizaciones(manifest_url="")
        resultado = servicio.comprobar()

        self.assertTrue(resultado.correcto)
        self.assertFalse(resultado.disponible)
        self.assertIn("No hay servidor", resultado.mensaje)

    def test_detecta_version_nueva_desde_manifest_local(self):

        with tempfile.TemporaryDirectory() as temporal:

            manifest = Path(temporal) / "manifest.json"
            manifest.write_text(
                json.dumps({
                    "version": "1.1.0",
                    "url": "",
                    "notas": "Mejoras futuras"
                }),
                encoding="utf-8"
            )

            servicio = ServicioActualizaciones(
                version_actual="1.0.0",
                manifest_url=manifest.resolve().as_uri()
            )
            resultado = servicio.comprobar()

            self.assertTrue(resultado.correcto)
            self.assertTrue(resultado.disponible)
            self.assertEqual(resultado.actualizacion.version, "1.1.0")

    def test_descarga_actualizacion_en_destino_temporal(self):

        with tempfile.TemporaryDirectory() as temporal:

            origen = Path(temporal) / "setup.exe"
            origen.write_bytes(b"instalador demo")
            sha256 = hashlib.sha256(origen.read_bytes()).hexdigest()
            manifest = Path(temporal) / "manifest.json"
            manifest.write_text(
                json.dumps({
                    "version": "1.2.0",
                    "url": origen.resolve().as_uri(),
                    "sha256": sha256
                }),
                encoding="utf-8"
            )
            destino = Path(temporal) / "descargas"

            servicio = ServicioActualizaciones(
                version_actual="1.0.0",
                manifest_url=manifest.resolve().as_uri()
            )
            comprobacion = servicio.comprobar()
            resultado = servicio.descargar(
                comprobacion.actualizacion,
                destino
            )

            self.assertTrue(resultado.correcto)
            self.assertTrue(Path(resultado.ruta_descarga).exists())
            self.assertEqual(
                Path(resultado.ruta_descarga).read_bytes(),
                origen.read_bytes()
            )

    def test_servicio_no_modifica_delivery_db(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "delivery.db"
            conexion = sqlite3.connect(ruta)
            conexion.execute("CREATE TABLE prueba(id INTEGER PRIMARY KEY)")
            conexion.commit()
            conexion.close()

            antes = ruta.read_bytes()

            ServicioActualizaciones(manifest_url="").comprobar()

            despues = ruta.read_bytes()
            self.assertEqual(antes, despues)

    def test_comparacion_versiones(self):

        self.assertTrue(version_mayor("1.0.1", "1.0.0"))
        self.assertTrue(version_mayor("1.1.0", "1.0.9"))
        self.assertFalse(version_mayor("1.0.0", "1.0.0"))


if __name__ == "__main__":

    unittest.main()
