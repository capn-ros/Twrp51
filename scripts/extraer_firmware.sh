#!/usr/bin/env bash
#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# Extrae del firmware de stock (zip oficial de Motorola) lo que necesita el árbol:
#   - el kernel del boot.img
#   - el ramdisk del vendor_boot.img (fstab y módulos de primera etapa)
#   - la partición vendor_a de super (módulos, firmware táctil, fstab, blobs)
#
# Uso: scripts/extraer_firmware.sh <firmware.zip> <carpeta_de_trabajo>
# Requiere (Ubuntu): unzip, simg2img (android-sdk-libsparse-utils), lz4, cpio,
#                    python3, git, e2fsprogs/erofs-utils y sudo para montar.
# Deja en <carpeta>:  kernel   vendor/   vendor_ramdisk/
#

set -euo pipefail

ZIP="${1:?falta el zip del firmware}"
TRAB="${2:?falta la carpeta de trabajo}"
mkdir -p "$TRAB"
TRAB="$(cd "$TRAB" && pwd)"
HERR="$TRAB/herramientas"
mkdir -p "$HERR"

paso() { echo; echo "==> $*"; }

paso "Contenido del firmware"
unzip -l "$ZIP" | grep -E 'boot|super|vendor' || true

paso "Descomprimiendo boot, vendor_boot y super"
# unzip devuelve error si algún patrón no existe (por ejemplo, super.img suelto): se tolera
# y después se controla que esté lo imprescindible.
unzip -o -j "$ZIP" 'boot.img' 'vendor_boot.img' 'super.img*' -d "$TRAB/fw" >/dev/null || true
ls -la "$TRAB/fw"
[ -s "$TRAB/fw/boot.img" ] || { echo "error: el firmware no trae boot.img" >&2; exit 1; }

paso "Herramientas de AOSP (unpack_bootimg) y lpunpack"
if [ ! -d "$HERR/mkbootimg" ]; then
    git clone --depth=1 https://android.googlesource.com/platform/system/tools/mkbootimg "$HERR/mkbootimg"
fi
if [ ! -d "$HERR/lpunpack" ]; then
    git clone --depth=1 https://github.com/unix3dgforce/lpunpack "$HERR/lpunpack"
fi

# ---------------------------------------------------------------- kernel
paso "Extrayendo kernel de boot.img"
python3 "$HERR/mkbootimg/unpack_bootimg.py" --boot_img "$TRAB/fw/boot.img" --out "$TRAB/boot_out"
cp "$TRAB/boot_out/kernel" "$TRAB/kernel"
echo "kernel: $(stat -c %s "$TRAB/kernel") bytes"

# ---------------------------------------------------------- vendor_boot
descomprimir_ramdisk() {
    local entrada="$1" salida="$2"
    mkdir -p "$salida"
    local magia
    magia="$(xxd -p -l 4 "$entrada")"
    case "$magia" in
        1f8b*)    gzip -dc "$entrada" > "$entrada.cpio" ;;
        02214c18|04224d18) lz4 -dc "$entrada" > "$entrada.cpio" ;;
        *)        cp "$entrada" "$entrada.cpio" ;;
    esac
    (cd "$salida" && cpio -idm --quiet < "$entrada.cpio") || true
}

paso "Extrayendo ramdisk de vendor_boot.img (no es obligatorio)"
if python3 "$HERR/mkbootimg/unpack_bootimg.py" --boot_img "$TRAB/fw/vendor_boot.img" --out "$TRAB/vboot_out"; then
    for r in "$TRAB"/vboot_out/vendor_ramdisk*; do
        [ -f "$r" ] && descomprimir_ramdisk "$r" "$TRAB/vendor_ramdisk"
    done
else
    echo "aviso: no se pudo desempaquetar vendor_boot.img"
fi

# ---------------------------------------------------------------- super
paso "Uniendo super (sparse) en una imagen cruda"
if ls "$TRAB"/fw/super.img_sparsechunk.* >/dev/null 2>&1; then
    mapfile -t PEDAZOS < <(ls "$TRAB"/fw/super.img_sparsechunk.* | sort -V)
    simg2img "${PEDAZOS[@]}" "$TRAB/super.raw"
    rm -f "${PEDAZOS[@]}"
elif [ -f "$TRAB/fw/super.img" ]; then
    if [ "$(xxd -p -l 4 "$TRAB/fw/super.img")" = "3aff26ed" ]; then
        simg2img "$TRAB/fw/super.img" "$TRAB/super.raw"
    else
        mv "$TRAB/fw/super.img" "$TRAB/super.raw"
    fi
else
    echo "error: el firmware no trae super.img ni super.img_sparsechunk.*" >&2
    exit 1
fi

paso "Sacando vendor de super"
mkdir -p "$TRAB/particiones"
for nombre in vendor_a vendor; do
    if python3 "$HERR/lpunpack/lpunpack.py" --partition="$nombre" "$TRAB/super.raw" "$TRAB/particiones"; then
        [ -s "$TRAB/particiones/$nombre.img" ] && break
    fi
done
rm -f "$TRAB/super.raw"
VIMG="$(ls "$TRAB"/particiones/vendor*.img | head -n 1)"
[ -s "$VIMG" ] || { echo "error: no se pudo extraer vendor de super" >&2; exit 1; }

paso "Copiando el contenido de vendor ($(basename "$VIMG"))"
mkdir -p "$TRAB/montaje" "$TRAB/vendor"
if sudo mount -o ro,loop "$VIMG" "$TRAB/montaje"; then
    sudo cp -a "$TRAB/montaje/." "$TRAB/vendor/"
    sudo umount "$TRAB/montaje"
elif command -v fsck.erofs >/dev/null && fsck.erofs --extract="$TRAB/vendor" "$VIMG"; then
    echo "vendor extraído como EROFS"
else
    echo "aviso: no se pudo montar; se intenta con debugfs (ext4)"
    debugfs -R "rdump / $TRAB/vendor" "$VIMG"
fi
sudo chown -R "$(id -u):$(id -g)" "$TRAB/vendor"
rm -f "$VIMG"

paso "Listo"
du -sh "$TRAB/vendor" "$TRAB/kernel"
