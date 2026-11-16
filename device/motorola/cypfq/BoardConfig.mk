#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# Basado en el árbol generado por twrpdtgen
# (github.com/twrpdtgen/android_device_motorola_cypfq), adaptado a twrp-12.1.
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/motorola/cypfq

# Datos que genera el workflow a partir del firmware de stock
# (scripts/preparar_arbol.py). Si no existe, se usan los valores por defecto.
-include $(DEVICE_PATH)/generated/info.mk

# Con el manifiesto mínimo de TWRP faltan módulos que no usamos.
ALLOW_MISSING_DEPENDENCIES := true

# ---------------------------------------------------------------------------
# A/B
# El G51 es A/B y el recovery vive dentro del ramdisk de boot
# (no tiene partición recovery). Por eso se compila "bootimage".
# ---------------------------------------------------------------------------
AB_OTA_UPDATER := true
AB_OTA_PARTITIONS += \
    boot \
    dtbo \
    odm \
    product \
    system \
    system_ext \
    vbmeta \
    vbmeta_system \
    vendor \
    vendor_boot
BOARD_USES_RECOVERY_AS_BOOT := true
TARGET_NO_RECOVERY := true

# ---------------------------------------------------------------------------
# Arquitectura (Snapdragon 480+, SM4350, plataforma "holi")
# ---------------------------------------------------------------------------
TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic
TARGET_CPU_VARIANT_RUNTIME := kryo300

TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic
TARGET_2ND_CPU_VARIANT_RUNTIME := cortex-a55

TARGET_BOARD_PLATFORM := holi
TARGET_BOOTLOADER_BOARD_NAME := cypfq
TARGET_NO_BOOTLOADER := true
TARGET_USES_UEFI := true

# ---------------------------------------------------------------------------
# Kernel
# Se usa el kernel EXACTO del boot.img de stock que tiene el teléfono.
# Motivo: los módulos (táctil, etc.) se cargan desde el vendor/vendor_boot de
# ese mismo firmware y solo funcionan con el kernel con el que fueron compilados.
# El workflow copia ese kernel a prebuilt/kernel.
# ---------------------------------------------------------------------------
BOARD_BOOT_HEADER_VERSION := 3
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += --pagesize $(BOARD_KERNEL_PAGESIZE)
TARGET_FORCE_PREBUILT_KERNEL := true
TARGET_PREBUILT_KERNEL := $(DEVICE_PATH)/prebuilt/kernel

# ---------------------------------------------------------------------------
# Particiones
# ---------------------------------------------------------------------------
BOARD_FLASH_BLOCK_SIZE := 262144
BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_HAS_LARGE_FILESYSTEM := true
BOARD_SYSTEMIMAGE_PARTITION_TYPE := ext4
BOARD_USERDATAIMAGE_FILE_SYSTEM_TYPE := f2fs
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_VENDOR := vendor
# No se definen TARGET_COPY_OUT_PRODUCT/SYSTEM_EXT/ODM: el recovery no genera esas
# imágenes y AOSP exige su tipo de sistema de archivos si se declaran
# (error de board_config.mk en la compilación del 2026-11-16).
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true

# Particiones dinámicas (super). Valores tomados de twrpdtgen.
BOARD_SUPER_PARTITION_SIZE := 9126805504
BOARD_SUPER_PARTITION_GROUPS := motorola_dynamic_partitions
BOARD_MOTOROLA_DYNAMIC_PARTITIONS_PARTITION_LIST := system system_ext product vendor odm
BOARD_MOTOROLA_DYNAMIC_PARTITIONS_SIZE := 9122611200

# ---------------------------------------------------------------------------
# Verified Boot
# ---------------------------------------------------------------------------
BOARD_AVB_ENABLE := true
BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS += --flags 3

# Evita el "anti rollback" de keymaster en el recovery.
PLATFORM_SECURITY_PATCH := 2099-12-31
VENDOR_SECURITY_PATCH := 2099-12-31
PLATFORM_VERSION := 16.1.0

# ---------------------------------------------------------------------------
# Recovery
# El fstab lo genera el workflow desde el fstab de stock
# (recovery/root/system/etc/recovery.fstab). twrp.flags agrega lo propio de TWRP.
# ---------------------------------------------------------------------------
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_RECOVERY_QCOM_RTC_FIX := true
TARGET_USES_MKE2FS := true
BOARD_SUPPRESS_SECURE_ERASE := true

# ---------------------------------------------------------------------------
# Opciones de TWRP
# NOTA: no se cambia nada del aspecto (tema, idioma por defecto, textos):
# queda la interfaz estándar de TWRP.
# ---------------------------------------------------------------------------
TW_THEME := portrait_hdpi
TARGET_SCREEN_DENSITY := 400
TW_EXTRA_LANGUAGES := true
TW_SCREEN_BLANK_ON_BOOT := true
TW_INPUT_BLACKLIST := "hbtp_vm"
TW_USE_TOOLBOX := true
TW_INCLUDE_RESETPROP := true
TW_INCLUDE_LPDUMP := true
TW_INCLUDE_LPTOOLS := true
TW_INCLUDE_FASTBOOTD := true
TW_EXCLUDE_APEX := true
TW_FRAMERATE := 60
TW_MAX_BRIGHTNESS := 4095
TW_DEFAULT_BRIGHTNESS := 1600
RECOVERY_SDCARD_ON_DATA := true
TARGET_USES_LOGD := true
TWRP_INCLUDE_LOGCAT := true
TW_INCLUDE_NTFS_3G := true

# Fase 1: sin descifrado de /data (ver docs/FASES.md).
# En la fase 2 se activan TW_INCLUDE_CRYPTO y los blobs de keymaster/gatekeeper.
TW_INCLUDE_CRYPTO := false
