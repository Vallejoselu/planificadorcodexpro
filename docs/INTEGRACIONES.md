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

## Fase 14.10B2: resumen por email

El resumen por email se prepara desde los mismos datos de exportacion del
cuadrante semanal.

Esta fase permite:

- generar el asunto y cuerpo del mensaje;
- exportar un borrador `.eml`;
- enviar por SMTP usando una referencia de credenciales ya validada.

La configuracion visual queda para la fase 14.10B3. El envio no guarda claves en
`delivery.db`: el campo `credenciales_referencia` debe apuntar a `env:VARIABLE`
o `local://proveedor/nombre`.

## Fase 14.10B3: configuracion desde UI

La pantalla de configuracion permite preparar la integracion de email:

- servidor SMTP;
- puerto;
- uso de TLS;
- remitente;
- destinatarios;
- referencia segura de credenciales.

La pantalla guarda la configuracion en `integraciones_api` y mantiene las claves
fuera de la base de datos. El envio directo y pruebas de conexion avanzadas
quedan para fases posteriores.

## Fase 14.10B4: acciones desde exportaciones

La pantalla de exportaciones permite:

- exportar un borrador `.eml` con el resumen semanal;
- enviar el resumen por email usando la configuracion guardada.

El envio pide confirmacion antes de usar SMTP. Si faltan servidor, remitente,
destinatarios o referencia de credenciales, la app muestra un error y no envia.
