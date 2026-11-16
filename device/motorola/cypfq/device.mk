#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# SPDX-License-Identifier: Apache-2.0
#

LOCAL_PATH := device/motorola/cypfq

-include $(LOCAL_PATH)/generated/info.mk

# El G51 salió con Android 11 (API 30).
PRODUCT_SHIPPING_API_LEVEL := 30

# Particiones dinámicas
PRODUCT_USE_DYNAMIC_PARTITIONS := true

# Virtual A/B: el workflow lo detecta en el build.prop del vendor de stock
# (ro.virtual_ab.enabled). Por defecto se asume que sí.
TWG51_VIRTUAL_AB ?= true
ifeq ($(TWG51_VIRTUAL_AB),true)
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)
endif

# fastbootd (para "fastboot flash system/vendor/..." con particiones dinámicas)
PRODUCT_PACKAGES += \
    android.hardware.fastboot@1.0-impl-mock \
    android.hardware.fastboot@1.0-impl-mock.recovery \
    fastbootd

PRODUCT_PROPERTY_OVERRIDES += \
    ro.fastbootd.available=true

PRODUCT_SOONG_NAMESPACES += $(LOCAL_PATH)
