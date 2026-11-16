# CLAUDE.md — TWG51 (TWRP para Moto G51 5G, cypfq)

**Creado por Andrés Londero.** Todo en castellano (código comentado, docs, mensajes).

## Qué es
TWRP para el Motorola Moto G51 5G (`cypfq`, SM4350 "holi", kernel 5.4, A/B, recovery dentro de
`boot`, header v3 con `vendor_boot`, particiones dinámicas Virtual A/B). Teléfono de Andrés:
**XT2171-1, canal RETAR, Android 12, compilación S2RYA32.58-13-12-5-6-1**
(firmware ya cargado en `config/firmware.conf`). Se compila en GitHub Actions al subir `twg51.zip`.

## Reglas del proyecto
- **No cambiar la interfaz** (tema, idioma por defecto, textos que se ven en pantalla, nombre
  de versión mostrado) sin consultarlo antes con Andrés.
- Al terminar cada etapa, dejar todo documentado dentro del zip: este archivo, `docs/`,
  `README.md`, pruebas y comentarios.
- El kernel debe salir del **mismo firmware** que tiene el teléfono (los módulos dependen de eso).
- No se puede probar en el dispositivo desde acá: cada cambio se valida con
  `fastboot boot` siguiendo `docs/PRUEBAS-EN-EL-TELEFONO.md`.

## Decisiones tomadas
- Base: árbol de twrpdtgen (firmware A11) adaptado a **twrp-12.1** con manifiesto mínimo.
- El árbol se completa en el workflow con `scripts/preparar_arbol.py` desde el firmware de stock:
  kernel → `prebuilt/kernel`; módulos táctiles + dependencias → `recovery/root/system/etc/twg51/modulos/`
  con `orden.txt`; firmware táctil → `recovery/root/vendor/firmware/`; fstab de stock filtrado
  (sin flags AVB) → `recovery/root/system/etc/recovery.fstab`; `generated/info.mk`.
- Los módulos los carga `twg51_modulos.sh` (exec desde `init.recovery.cypfq.rc`, `on init`), no
  `TW_LOAD_VENDOR_MODULES`: así no se pisa `/lib/modules/modules.dep` del vendor_boot.
- El workflow commitea al repo el contenido del zip (excepto `.github`, que GITHUB_TOKEN no puede
  modificar) con "[skip ci]". Cambios en `compilar.yml` → Andrés lo pega a mano.
- El firmware extraído (kernel, vendor, vendor_ramdisk; ~1 GB) va a la caché de Actions con clave
  = hash de `config/firmware.conf` + `scripts/extraer_firmware.sh`.
- Workflow en dos jobs: `preparar` (firmware, ~15 GB en /mnt) y `compilar` (TWRP, en /mnt).

## Estado
- Fase 1 armada, **sin compilar ni probar todavía** (2026-11-15).
- Firmware exacto cargado (RETAR S2RYA32.58-13-12-5-6-1).
- Pendiente: que Andrés suba el zip, compile, pruebe con `fastboot boot` y mande logs.
- Fases siguientes en `docs/FASES.md` (descifrado, bootctrl, OrangeFox).

## Historial de compilaciones
- 2026-11-16 #1: "preparar" OK (firmware bajado y extraído; kernel 42 MB; vendor 887 MB; huella
  `motorola/cypfq_g/cypfq:11/S2RYA32.58-13-12-5-6-1`). Táctil encontrado en vendor: solo
  `ili9882_mmi.ko` (+ `sensors_class.ko`); fstab con 6 líneas. "compilar" falló en
  board_config.mk por `TARGET_COPY_OUT_PRODUCT` sin tipo de FS → se quitaron
  TARGET_COPY_OUT_PRODUCT/SYSTEM_EXT/ODM. Además ahora se buscan táctiles también en el
  vendor_boot y el log imprime todas las listas de módulos, el fstab y los blobs.
- 2026-11-15 (pedido de Andrés): guardar lo descomprimido en el repo y no bajar el firmware
  cada vez → commit automático + caché. Requiere pegar el compilar.yml nuevo a mano.

## Comandos
- Pruebas: `python3 -m unittest discover -s tests -v`
- Sintaxis de scripts: `bash -n scripts/*.sh device/motorola/cypfq/recovery/root/system/bin/*.sh`
