import tempfile
import unittest
from pathlib import Path

from services.credenciales import GestorCredencialesIntegracion
from services.email_resumen import (
    crear_mensaje_resumen,
    enviar_resumen_email,
    exportar_resumen_email,
    normalizar_destinatarios,
    preparar_resumen_email
)


DATOS_EXPORTACION = {
    "fecha_inicio_semana": "2026-07-13",
    "horarios": [[
        "miercoles",
        "Comida",
        "Comida",
        "BK Centro",
        "Centro",
        "Ana",
        "13:00",
        "16:00",
        3
    ]],
    "totales": [
        ["Total horarios", 1],
        ["Total horas planificadas", 3],
        ["Total restaurantes", 1],
        ["Total repartidores", 2]
    ]
}


class FakeSMTP:

    instancias = []

    def __init__(self, host, puerto, timeout=30):

        self.host = host
        self.puerto = puerto
        self.timeout = timeout
        self.tls = False
        self.login_args = None
        self.mensaje = None
        FakeSMTP.instancias.append(self)

    def __enter__(self):

        return self

    def __exit__(self, exc_type, exc, tb):

        return False

    def starttls(self):

        self.tls = True

    def login(self, usuario, clave):

        self.login_args = (usuario, clave)

    def send_message(self, mensaje):

        self.mensaje = mensaje


class TestEmailResumen(unittest.TestCase):

    def test_prepara_resumen_con_datos_del_cuadrante(self):

        resumen = preparar_resumen_email("2026-07-13", DATOS_EXPORTACION)

        self.assertEqual(resumen["asunto"], "Cuadrante semanal 2026-07-13")
        self.assertIn("Turnos planificados: 1", resumen["cuerpo"])
        self.assertIn("Miercoles 13:00-16:00", resumen["cuerpo"])
        self.assertIn("BK Centro", resumen["cuerpo"])

    def test_crea_mensaje_email_con_destinatarios(self):

        mensaje = crear_mensaje_resumen(
            "ana@example.test; luis@example.test",
            "planificador@example.test",
            "2026-07-13",
            DATOS_EXPORTACION
        )

        self.assertEqual(mensaje["From"], "planificador@example.test")
        self.assertEqual(
            mensaje["To"],
            "ana@example.test, luis@example.test"
        )
        self.assertIn("Cuadrante semanal", mensaje["Subject"])

    def test_exporta_borrador_eml_sin_enviar(self):

        with tempfile.TemporaryDirectory() as temporal:

            ruta = Path(temporal) / "resumen.eml"

            exportar_resumen_email(
                ruta,
                ["ana@example.test"],
                "planificador@example.test",
                "2026-07-13",
                DATOS_EXPORTACION
            )

            contenido = ruta.read_text(encoding="utf-8")
            self.assertIn("Subject: Cuadrante semanal 2026-07-13", contenido)
            self.assertIn("To: ana@example.test", contenido)

    def test_envia_email_usando_referencia_de_credenciales(self):

        FakeSMTP.instancias = []

        with tempfile.TemporaryDirectory() as temporal:

            gestor = GestorCredencialesIntegracion(temporal)
            referencia = gestor.guardar_local(
                "email",
                "principal",
                {
                    "usuario": "planificador@example.test",
                    "clave": "valor-local"
                }
            )
            resultado = enviar_resumen_email(
                ["ana@example.test"],
                {
                    "host": "smtp.example.test",
                    "puerto": 2525,
                    "tls": True
                },
                referencia,
                "2026-07-13",
                DATOS_EXPORTACION,
                gestor_credenciales=gestor,
                smtp_factory=FakeSMTP
            )

        smtp = FakeSMTP.instancias[0]
        self.assertTrue(resultado["enviado"])
        self.assertTrue(smtp.tls)
        self.assertEqual(
            smtp.login_args,
            ("planificador@example.test", "valor-local")
        )
        self.assertEqual(smtp.mensaje["To"], "ana@example.test")

    def test_valida_destinatarios(self):

        self.assertEqual(
            normalizar_destinatarios("ana@example.test,luis@example.test"),
            ["ana@example.test", "luis@example.test"]
        )

        with self.assertRaises(ValueError):

            normalizar_destinatarios("")

        with self.assertRaises(ValueError):

            normalizar_destinatarios(["sin-arroba"])


if __name__ == "__main__":

    unittest.main()
