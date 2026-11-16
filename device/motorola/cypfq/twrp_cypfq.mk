#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)

# Configuración común de TWRP
$(call inherit-product, vendor/twrp/config/common.mk)

# Dispositivo
$(call inherit-product, device/motorola/cypfq/device.mk)

PRODUCT_DEVICE := cypfq
PRODUCT_NAME := twrp_cypfq
PRODUCT_BRAND := motorola
PRODUCT_MODEL := moto g51 5G
PRODUCT_MANUFACTURER := motorola

PRODUCT_GMS_CLIENTID_BASE := android-motorola
