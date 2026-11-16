#!/usr/bin/env bash
#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# Borra del runner de GitHub lo que no se usa (SDKs de otros lenguajes, imágenes
# de Docker) para tener lugar para el firmware (~15 GB) o el código de TWRP (~30 GB).
#

set -uo pipefail

echo "Antes:"; df -h / /mnt 2>/dev/null

sudo rm -rf \
    /usr/share/dotnet \
    /usr/local/lib/android \
    /opt/ghc \
    /usr/local/.ghcup \
    /opt/hostedtoolcache/CodeQL \
    /usr/local/share/boost \
    /usr/share/swift \
    /usr/local/share/powershell \
    /usr/local/share/chromium \
    /usr/local/lib/node_modules \
    /opt/microsoft /opt/google /opt/az 2>/dev/null

sudo docker image prune --all --force >/dev/null 2>&1 || true
sudo apt-get clean >/dev/null 2>&1 || true

echo "Después:"; df -h / /mnt 2>/dev/null
exit 0
