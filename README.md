# TWG51 — TWRP para Moto G51 5G (cypfq)

**Creado por Andrés Londero**

TWRP para el Motorola Moto G51 5G (codename `cypfq`, Snapdragon 480+), compilado en GitHub Actions.
Su objetivo es arreglar lo que falla en los TWRP no oficiales que existen hoy:

| Problema de los TWRP actuales | Qué hace TWG51 |
|---|---|
| El táctil no anda en algunas pantallas (Chipone) | Mete en el recovery los módulos táctiles de **todas** las variantes de pantalla, con sus dependencias, y los carga al arrancar |
| Kernel de otro firmware (Android 11) | Usa el kernel **exacto** del firmware de stock que tiene tu teléfono |
| Sin fastbootd | fastbootd activado |
| Sin descifrado | Fase 2 (ver [docs/FASES.md](docs/FASES.md)) |

> ⚠️ **Estado: fase 1, sin probar en el teléfono.** Probalo siempre primero con
> `fastboot boot` (arranca una vez, no instala nada). Ver
> [docs/PRUEBAS-EN-EL-TELEFONO.md](docs/PRUEBAS-EN-EL-TELEFONO.md).

## Cómo se compila

1. Completar el firmware en `config/firmware.conf` (o subirlo a un Release `firmware`). Tiene que ser **el mismo** que tiene el teléfono. Ver [docs/INSTALACION.md](docs/INSTALACION.md).
2. Subir `twg51.zip` a la raíz del repo.
3. El workflow **Compilar TWRP G51** hace todo solo:
   - **preparar**: descomprime el zip y **guarda lo descomprimido en el repo** (menos `.github`),
     corre las pruebas, saca kernel, módulos táctiles, firmware táctil y fstab del firmware, y deja
     un **reporte** en el resumen del run. El firmware se baja **una sola vez**: lo extraído queda
     en la caché de GitHub y se reutiliza (se vuelve a bajar si cambia el firmware o pasan 7 días sin compilar);
   - **compilar**: baja TWRP 12.1 (manifiesto mínimo) y compila.
4. La imagen `twrp-cypfq-AAAAMMDD-HHMM.img` queda en los artefactos y en un Release (marcado como prerelease).

## Estructura

```
.github/workflows/compilar.yml   Workflow (preparar + compilar)
config/firmware.conf             URL del firmware de stock
device/motorola/cypfq/           Device tree de TWRP
  BoardConfig.mk, device.mk, twrp_cypfq.mk, AndroidProducts.mk, Android.mk
  recovery/root/init.recovery.cypfq.rc         Arranque propio
  recovery/root/system/bin/twg51_modulos.sh    Carga de módulos táctiles
  recovery/root/system/etc/twrp.flags          Particiones extra (backup, EFS, SD, OTG)
  prebuilt/ y generated/                       Los completa el workflow
scripts/extraer_firmware.sh      Saca kernel, vendor_boot y vendor del firmware
scripts/preparar_arbol.py        Completa el device tree con esos datos
scripts/liberar_espacio.sh       Hace lugar en el runner
tests/                           Pruebas del script (python3 -m unittest discover -s tests -v)
docs/                            Documentación
CLAUDE.md                        Notas para seguir el proyecto con Claude
```

## Créditos

- [TeamWin / TWRP](https://github.com/TeamWin/android_bootable_recovery)
- Árbol base: [twrpdtgen/android_device_motorola_cypfq](https://github.com/twrpdtgen/android_device_motorola_cypfq)
- Manifiesto: [minimal-manifest-twrp](https://github.com/minimal-manifest-twrp/platform_manifest_twrp_aosp)
- [lpunpack](https://github.com/unix3dgforce/lpunpack), mkbootimg de AOSP

Licencia: Apache-2.0 (como el árbol base).
