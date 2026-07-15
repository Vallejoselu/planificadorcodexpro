# Integraciones externas

## Fase 14.10A: credenciales seguras

Las integraciones no guardan claves reales dentro de `delivery.db`.

La tabla `integraciones_api` conserva solo `credenciales_referencia`, que debe
apuntar a una de estas fuentes:

- `env:NOMBRE_VARIABLE`: la credencial vive en una variable de entorno del
  equipo.
- `local://proveedor/nombre`: la credencial vive en un fichero local del usuario,
  fuera del repositorio y fuera de la base de datos.

El almacen local por defecto se crea en la carpeta de datos del usuario:

- Windows: `%APPDATA%\PlanificadorDeliveryPro\credenciales`
- Otros sistemas: `~/.planificador_delivery_pro/credenciales`

Para pruebas o instalaciones personalizadas puede usarse la variable
`PLANIFICADOR_CREDENCIALES_DIR`.

Las fases siguientes pueden usar esta estructura para calendario/email,
plataformas delivery y reintentos de sincronizacion sin introducir claves en el
codigo fuente ni en los commits.
