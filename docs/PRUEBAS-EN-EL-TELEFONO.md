# Probar TWG51 en el teléfono

*TWG51 — Creado por Andrés Londero*

> Requisitos: bootloader desbloqueado y `adb`/`fastboot` (Platform Tools) en la PC.

## 1. Arrancarlo SIN instalar (siempre primero)

```
adb reboot bootloader
fastboot boot twrp-cypfq-AAAAMMDD-HHMM.img
```

Esto arranca TWRP una sola vez. Si algo sale mal, se mantiene apretado el botón de encendido
y el teléfono vuelve a arrancar normal: **no se modifica nada**.

## 2. Lista de control

Anotá qué funciona y qué no:

| # | Prueba | Cómo |
|---|---|---|
| 1 | Arranca y se ve la pantalla | — |
| 2 | Táctil | Tocar botones. Si no anda, conectar un mouse por OTG |
| 3 | ADB | En la PC: `adb devices` (debe decir `recovery`) |
| 4 | MTP | Ver si la PC muestra el almacenamiento |
| 5 | fastbootd | Reboot → Fastboot; en la PC: `fastboot devices` y `fastboot getvar is-userspace` (debe decir `yes`) |
| 6 | Montar system/vendor | Mount → tildar System y Vendor |
| 7 | Backup de EFS y Persist | Backup → tildar EFS y Persist → guardar en la PC por ADB/MTP |
| 8 | MicroSD | Mount → MicroSD (si tenés una puesta) |
| 9 | USB OTG | Pendrive por OTG |
| 10 | Brillo y batería | Ajustes de TWRP / barra superior |

> **Recomendación fuerte:** hacé el backup de **EFS** y **Persist** (prueba 7) apenas TWRP
> arranque bien y guardalo fuera del teléfono. Ahí están el IMEI y las calibraciones.

## 3. Juntar datos si algo falla

Con TWRP arrancado y la PC conectada:

```
adb pull /tmp/recovery.log
adb pull /tmp/twg51_modulos.log
adb shell dmesg > dmesg.txt
adb shell ls -l /dev/block/by-name/ > particiones.txt
adb shell ls /dev/block/ > bloques.txt
adb shell cat /proc/cmdline > cmdline.txt
adb shell getevent -pl > entradas.txt
```

Mandá esos archivos y la lista de control a Claude. `twg51_modulos.log` dice qué módulos
táctiles cargaron y cuáles no.

## 4. Instalarlo de forma permanente (solo cuando todo lo importante ande)

El G51 no tiene partición recovery: TWRP vive dentro de `boot`. Con TWRP arrancado por
`fastboot boot`:

1. Copiar la imagen al teléfono: `adb push twrp-cypfq-*.img /sdcard/`
2. En TWRP: **Advanced → Install Recovery Ramdisk** → elegir la imagen.

Esto reemplaza el ramdisk del boot del slot actual. Si después se instala una ROM o una
actualización, hay que repetirlo.
