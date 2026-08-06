import unittest
from pathlib import Path


class TestPreReleaseChecklist(unittest.TestCase):

    def test_checklist_pre_release_cubre_flujo_operativo(self):

        raiz = Path(__file__).resolve().parents[1]
        checklist = (
            raiz / "docs" / "CHECKLIST_PRE_RELEASE.md"
        ).read_text(encoding="utf-8")
        readme = (raiz / "README.md").read_text(encoding="utf-8")

        for texto in (
            "python scripts\\validar_flujo_base_limpia.py",
            "Empezar de cero",
            "Crear datos minimos",
            "No disponible",
            "Comprobar configuracion",
            "contrato, total de horas y horas complementarias",
            "No se guardan vistas previas vacias",
            "exportar Excel",
            "PlanificadorDeliveryPro-Setup-2.2.0.exe"
        ):

            self.assertIn(texto, checklist)

        self.assertIn("docs\\CHECKLIST_PRE_RELEASE.md", readme)


if __name__ == "__main__":

    unittest.main()
