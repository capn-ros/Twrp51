#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#

LOCAL_PATH := $(call my-dir)

ifeq ($(TARGET_DEVICE),cypfq)
include $(call all-subdir-makefiles,$(LOCAL_PATH))
endif
