import os
import tempfile
import unittest

from models.integracion import ConfiguracionIntegracion
from services.credenciales import (
    GestorCredencialesIntegracion,
    enmascarar_referencia,
    referencia_entorno,
    referencia_local,
    validar_referencia_credenciales
)
from services.integraciones.base import IntegracionBase
from services.integraciones.registro import guardar_configuracion


class FakeRepository:

    def __init__(self):

        self.guardada = None

    def guardar_configuracion(self, *args):

        self.guardada = args


class TestIntegracionesCredenciales(unittest.TestCase):

    def test_referencia_entorno_no_expone_valor(self):

        referencia = referencia_entorno("PLANIFICADOR_TEST_CLAVE")
        os.environ["PLANIFICADOR_TEST_CLAVE"] = "valor-local"

        try:

            gestor = GestorCredencialesIntegracion()

            self.assertTrue(gestor.existe(referencia))
            self.assertEqual(gestor.obtener(referencia), {"valor": "valor-local"})
            self.assertEqual(enmascarar_referencia(referencia), "env:***")

        finally:

            os.environ.pop("PLANIFICADOR_TEST_CLAVE", None)

    def test_almacen_local_guarda_fuera_del_proyecto_y_devuelve_referencia(self):

        with tempfile.TemporaryDirectory() as temporal:

            gestor = GestorCredencialesIntegracion(temporal)
            referencia = gestor.guardar_local(
                "shipday",
                "principal",
                {"clave": "valor-local"}
            )

            self.assertEqual(referencia, "local://shipday/principal")
            self.assertTrue(gestor.existe(referencia))
            self.assertEqual(
                gestor.obtener(referencia),
                {"clave": "valor-local"}
            )
            self.assertTrue(gestor.ruta_local(referencia).is_file())
            self.assertTrue(gestor.eliminar(referencia))
            self.assertFalse(gestor.existe(referencia))

    def test_validacion_rechaza_valor_directo_en_configuracion(self):

        configuracion = ConfiguracionIntegracion(
            proveedor="shipday",
            nombre="Shipday",
            credenciales_referencia="valor-directo-no-permitido"
        )

        with self.assertRaises(ValueError):

            guardar_configuracion(configuracion)

    def test_configuracion_guarda_solo_referencia_validada(self):

        import services.integraciones.registro as registro

        repositorio_original = registro.integraciones_repository
        falso = FakeRepository()
        registro.integraciones_repository = falso

        try:

            configuracion = ConfiguracionIntegracion(
                proveedor="shipday",
                nombre="Shipday",
                credenciales_referencia=referencia_local("shipday", "principal")
            )
            guardar_configuracion(configuracion)

        finally:

            registro.integraciones_repository = repositorio_original

        self.assertEqual(falso.guardada[4], "local://shipday/principal")

    def test_integracion_base_expone_estado_sin_mostrar_credencial(self):

        with tempfile.TemporaryDirectory() as temporal:

            gestor = GestorCredencialesIntegracion(temporal)
            referencia = gestor.guardar_local(
                "shipday",
                "principal",
                {"clave": "valor-local"}
            )
            integracion = IntegracionBase(
                ConfiguracionIntegracion(
                    proveedor="shipday",
                    nombre="Shipday",
                    credenciales_referencia=referencia
                ),
                gestor_credenciales=gestor
            )
            estado = integracion.estado_credenciales()

            self.assertTrue(integracion.credenciales_disponibles())
            self.assertEqual(integracion.obtener_credenciales()["clave"], "valor-local")
            self.assertEqual(estado["mascara"], "local://shipday/***")
            self.assertNotIn("valor-local", str(estado))

    def test_valida_referencia_vacia_para_integraciones_sin_configurar(self):

        self.assertEqual(validar_referencia_credenciales(""), "")


if __name__ == "__main__":

    unittest.main()
