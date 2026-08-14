import unittest
from pathlib import Path

import app_info


class TestAutoriaCopyright(unittest.TestCase):

    def test_metadatos_de_autoria(self):

        self.assertRegex(app_info.VERSION, r"^\d+\.\d+\.\d+$")
        self.assertEqual(app_info.AUTHOR, "Valle")
        self.assertIn(
            "Todos los derechos reservados",
            app_info.COPYRIGHT_NOTICE
        )
        self.assertIn("Prohibida la copia", app_info.USAGE_NOTICE)

    def test_documentacion_e_instalador_incluyen_autoria(self):

        raiz = Path(__file__).resolve().parents[1]
        readme = (raiz / "README.md").read_text(encoding="utf-8")
        copyright = (raiz / "COPYRIGHT.md").read_text(encoding="utf-8")
        instalador = (
            raiz / "installer" / "PlanificadorDeliveryPro.iss"
        ).read_text(encoding="utf-8")

        for texto in (
            "Creado por Valle",
            "Todos los derechos reservados",
            "Queda prohibida la copia"
        ):
            self.assertIn(texto, readme)

        self.assertIn("No se autoriza la copia", copyright)
        self.assertIn('#define MyAppPublisher "Valle"', instalador)
        self.assertIn(
            f'#define MyAppVersion "{app_info.VERSION}"',
            instalador
        )
        self.assertIn("AppCopyright=(c) 2026 Valle", instalador)


if __name__ == "__main__":

    unittest.main()
