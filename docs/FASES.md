# Fases del proyecto

*TWG51 — Creado por Andrés Londero*

## Fase 1 — base funcional (esta versión)

- Kernel del firmware de stock del teléfono (XT2171-1, Android 12).
- Táctil: módulos de todas las variantes de pantalla, con dependencias y firmware.
- ADB, MTP, fastbootd.
- Particiones dinámicas (montar system/vendor/product/odm).
- Backup y flasheo de boot, vendor_boot, dtbo, vbmeta, EFS y persist.
- MicroSD y USB OTG (rutas a confirmar en la prueba).
- **Sin descifrado**: `/data` no se puede leer si está cifrado. Sí se puede formatear,
  instalar zips por ADB sideload o desde MicroSD/OTG y hacer backups de particiones.

### A confirmar en la prueba
- Rutas de MicroSD (`mmcblk0`) y OTG (`sdg`) en `twrp.flags`.
- Brillo (`TW_MAX_BRIGHTNESS` en BoardConfig.mk).
- Cambio de slot desde TWRP (todavía no se incluye el HAL de bootctrl).

## Fase 2 — descifrado de /data

Con el reporte del firmware (sección "Archivos para descifrado"):
- Agregar `device/qcom/twrp-common` al manifiesto.
- Copiar al recovery los servicios de keymaster/keymint, gatekeeper y qseecomd del vendor de stock.
- Activar `TW_INCLUDE_CRYPTO`, `TW_INCLUDE_FBE_METADATA_DECRYPT` y `BOARD_USES_QCOM_FBE_DECRYPTION`.
- Agregar el HAL de bootctrl para cambiar de slot.

Nota: si después se instala un GSI de Android 17, el vendor sigue siendo el de Motorola, así que
estos mismos archivos deberían servir. Si el GSI cambia el formato de cifrado, puede no descifrar.

## Fase 3 — OrangeFox

Sobre el mismo árbol, compilar OrangeFox (rama 12.1) con sus variables `OF_*`.
