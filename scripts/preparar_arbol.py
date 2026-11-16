#!/usr/bin/env python3
"""
TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
Creado por Andrés Londero

Completa el device tree con datos del firmware de stock del teléfono.

Lo usa el workflow después de extraer el firmware (ver scripts/extraer_firmware.sh):

  * copia el kernel del boot.img de stock a prebuilt/kernel
    (tiene que ser el MISMO firmware que tiene el teléfono, si no los módulos no cargan);
  * busca los módulos del táctil de todas las variantes de pantalla, les suma sus
    dependencias (modules.dep) y los copia al recovery con un orden de carga;
  * copia el firmware de esos táctiles (vendor/firmware);
  * arma recovery.fstab a partir del fstab de stock (solo las particiones del sistema);
  * escribe generated/info.mk (por ejemplo, si el equipo usa Virtual A/B);
  * deja un reporte en Markdown con todo lo encontrado (sirve para la fase 2: descifrado).

Uso:
  python3 -I scripts/preparar_arbol.py \
      --vendor DIR_VENDOR --kernel ARCHIVO_KERNEL --arbol device/motorola/cypfq \
      [--vendor-ramdisk DIR] [--reporte reporte.md]

No necesita nada fuera de la biblioteca estándar de Python.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

# Nombres típicos de drivers táctiles en Motorola / Qualcomm.
# Se busca en el nombre del archivo .ko (sin distinguir mayúsculas).
PATRON_TACTIL = re.compile(
    r"(touch|tddi|chipone|focaltech|fts|ilitek|ili9|novatek|nvt|himax|hx83|"
    r"goodix|gtx|gt9|synaptics|_ts\b|_ts_|^ts_|mmi_ts|sec_ts)",
    re.IGNORECASE,
)

# Firmware de táctiles en vendor/firmware.
PATRON_FIRMWARE_TACTIL = re.compile(
    r"(chipone|focaltech|fts|ilitek|ili9|novatek|nvt|himax|hx83|goodix|gt9|"
    r"tddi|touch|_ts_|^ts_)",
    re.IGNORECASE,
)

# Límite de tamaño para el firmware táctil copiado (el boot mide 96 MiB).
LIMITE_FIRMWARE_BYTES = 12 * 1024 * 1024

# Puntos de montaje del fstab de stock que TWRP tiene que conocer.
MONTAJES_SISTEMA = ["/system", "/system_ext", "/product", "/vendor", "/odm", "/metadata", "/data"]

# Flags de fs_mgr que en el recovery molestan (verificación AVB de las particiones).
FLAGS_A_QUITAR = re.compile(r"^(avb|avb=.*|avb_keys=.*)$")

NOMBRES_FSTAB = ["fstab.qcom", "fstab.holi", "fstab.default", "fstab.emmc", "fstab.ufs"]


# ---------------------------------------------------------------------------
# Módulos
# ---------------------------------------------------------------------------

def leer_modules_dep(ruta: Path) -> dict[str, list[str]]:
    """Lee modules.dep y devuelve {modulo.ko: [dependencias.ko]} usando solo nombres de archivo."""
    deps: dict[str, list[str]] = {}
    if not ruta.is_file():
        return deps
    for linea in ruta.read_text(errors="replace").splitlines():
        linea = linea.strip()
        if not linea or ":" not in linea:
            continue
        mod, _, resto = linea.partition(":")
        nombre = os.path.basename(mod.strip())
        deps[nombre] = [os.path.basename(d) for d in resto.split() if d.strip()]
    return deps


def es_tactil(nombre: str) -> bool:
    return bool(PATRON_TACTIL.search(nombre))


def ordenar_con_dependencias(elegidos: list[str], deps: dict[str, list[str]]) -> list[str]:
    """
    Devuelve los módulos elegidos más sus dependencias, en orden de carga
    (cada dependencia antes del módulo que la usa). Tolera ciclos y dependencias
    que no figuran en modules.dep.
    """
    orden: list[str] = []
    visitados: set[str] = set()
    en_curso: set[str] = set()

    def visitar(mod: str) -> None:
        if mod in visitados or mod in en_curso:
            return
        en_curso.add(mod)
        for dep in deps.get(mod, []):
            visitar(dep)
        en_curso.discard(mod)
        visitados.add(mod)
        orden.append(mod)

    for mod in sorted(elegidos):
        visitar(mod)
    return orden


def buscar_modulos(dir_modulos: Path) -> list[str]:
    if not dir_modulos.is_dir():
        return []
    return sorted(p.name for p in dir_modulos.glob("*.ko"))


def copiar_modulos(ubicaciones: dict[str, Path], orden: list[str], destino: Path) -> list[str]:
    """
    Copia los módulos a destino y escribe orden.txt. Devuelve los que faltaron.
    ubicaciones: {modulo.ko: ruta del archivo} (vendor o ramdisk del vendor_boot).
    """
    destino.mkdir(parents=True, exist_ok=True)
    faltantes = []
    copiados = []
    for mod in orden:
        origen = ubicaciones.get(mod)
        if origen is not None and origen.is_file():
            shutil.copy2(origen, destino / mod)
            copiados.append(mod)
        else:
            faltantes.append(mod)
    contenido = [
        "# Generado por scripts/preparar_arbol.py (TWG51). Orden de carga: dependencias primero.",
        *copiados,
    ]
    (destino / "orden.txt").write_text("\n".join(contenido) + "\n")
    return faltantes


# ---------------------------------------------------------------------------
# Firmware táctil
# ---------------------------------------------------------------------------

def copiar_firmware_tactil(dir_firmware: Path, destino: Path) -> list[str]:
    if not dir_firmware.is_dir():
        return []
    copiados = []
    total = 0
    for archivo in sorted(dir_firmware.rglob("*")):
        if not archivo.is_file() or archivo.is_symlink():
            continue
        if not PATRON_FIRMWARE_TACTIL.search(archivo.name):
            continue
        tam = archivo.stat().st_size
        if total + tam > LIMITE_FIRMWARE_BYTES:
            print(f"aviso: se omite {archivo.name}, se superaría el límite de firmware", file=sys.stderr)
            continue
        relativo = archivo.relative_to(dir_firmware)
        (destino / relativo).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(archivo, destino / relativo)
        total += tam
        copiados.append(str(relativo))
    return copiados


# ---------------------------------------------------------------------------
# fstab
# ---------------------------------------------------------------------------

def buscar_fstab(dir_vendor: Path, dir_ramdisk: Path | None) -> Path | None:
    candidatos = []
    for base in [dir_vendor / "etc"] + ([dir_ramdisk, dir_ramdisk / "first_stage_ramdisk"] if dir_ramdisk else []):
        if base and base.is_dir():
            for nombre in NOMBRES_FSTAB:
                candidatos.append(base / nombre)
            candidatos.extend(sorted(base.glob("fstab.*")))
    for c in candidatos:
        if c.is_file():
            return c
    return None


def filtrar_fstab(texto: str) -> list[str]:
    """
    Deja solo las líneas de las particiones del sistema, una por punto de montaje,
    sin los flags de AVB. Formato fs_mgr: origen montaje fs opciones flags_fsmgr.
    """
    salida = []
    vistos = set()
    for linea in texto.splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#"):
            continue
        partes = limpia.split()
        if len(partes) < 5:
            continue
        origen, montaje, fs, opciones, flags = partes[:5]
        if montaje not in MONTAJES_SISTEMA or montaje in vistos:
            continue
        flags_ok = [f for f in flags.split(",") if f and not FLAGS_A_QUITAR.match(f)]
        vistos.add(montaje)
        salida.append(f"{origen} {montaje} {fs} {opciones} {','.join(flags_ok) or 'defaults'}")
    return salida


def escribir_fstab(lineas: list[str], destino: Path, origen: str) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    cabecera = [
        "# Generado por scripts/preparar_arbol.py (TWG51) desde el fstab de stock:",
        f"#   {origen}",
        "# Las particiones extra de TWRP están en twrp.flags.",
        "",
    ]
    destino.write_text("\n".join(cabecera + lineas) + "\n")


# ---------------------------------------------------------------------------
# Propiedades
# ---------------------------------------------------------------------------

def leer_props(*rutas: Path) -> dict[str, str]:
    props: dict[str, str] = {}
    for ruta in rutas:
        if not ruta.is_file():
            continue
        for linea in ruta.read_text(errors="replace").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, _, valor = linea.partition("=")
            props.setdefault(clave.strip(), valor.strip())
    return props


def escribir_info_mk(props: dict[str, str], destino: Path) -> None:
    virtual_ab = props.get("ro.virtual_ab.enabled", "true").lower() == "true"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        "# Generado por scripts/preparar_arbol.py (TWG51). No editar a mano.\n"
        f"TWG51_VIRTUAL_AB := {'true' if virtual_ab else 'false'}\n"
        f"TWG51_FIRMWARE := {props.get('ro.vendor.build.fingerprint', 'desconocido')}\n"
    )


# ---------------------------------------------------------------------------
# Reporte
# ---------------------------------------------------------------------------

def listar_blobs_cifrado(dir_vendor: Path) -> list[str]:
    """Archivos relacionados con descifrado (para la fase 2)."""
    patron = re.compile(r"(keymaster|keymint|gatekeeper|qseecom|qsee|weaver|km4|"
                        r"libdiag|libqtikeymaster|libkeymasterdeviceutils|libQSEEComAPI|"
                        r"libspcom|libdrmfs|libdrmtime|librpmb|libssd|libtime_genoff)", re.IGNORECASE)
    encontrados = []
    for sub in ["bin", "bin/hw", "lib64", "lib64/hw", "etc/init", "etc/vintf/manifest"]:
        d = dir_vendor / sub
        if d.is_dir():
            for p in sorted(d.iterdir()):
                if p.is_file() and patron.search(p.name):
                    encontrados.append(f"{sub}/{p.name}")
    return encontrados


def escribir_reporte(destino: Path, datos: dict) -> None:
    l = ["# Reporte de TWG51 (firmware de stock analizado)", ""]
    l.append(f"- Huella del firmware (vendor): `{datos['huella']}`")
    l.append(f"- Virtual A/B: `{datos['virtual_ab']}`")
    l.append(f"- fstab usado: `{datos['fstab']}`")
    l.append("")
    l.append("## Módulos táctiles elegidos (en orden de carga)")
    l += [f"- {m}" for m in datos["orden"]] or ["- (ninguno)"]
    if datos["faltantes"]:
        l.append("")
        l.append("**Dependencias que no se encontraron:** " + ", ".join(datos["faltantes"]))
    l.append("")
    l.append("## Firmware táctil copiado")
    l += [f"- {f}" for f in datos["firmware"]] or ["- (ninguno)"]
    l.append("")
    l.append("## recovery.fstab generado")
    l.append("```")
    l += datos["fstab_lineas"]
    l.append("```")
    l.append("")
    l.append("## Todos los módulos del vendor")
    l.append("```")
    l += datos["todos_modulos"]
    l.append("```")
    l.append("")
    l.append("## Módulos del vendor_boot (los carga el first stage)")
    l.append("```")
    l += datos["modulos_ramdisk"] or ["(no se pudo leer el vendor_boot)"]
    l.append("```")
    l.append("")
    l.append("## Archivos para descifrado (fase 2)")
    l.append("```")
    l += datos["blobs"] or ["(ninguno encontrado)"]
    l.append("```")
    destino.write_text("\n".join(l) + "\n")


# ---------------------------------------------------------------------------
# Principal
# ---------------------------------------------------------------------------

def preparar(dir_vendor: Path, kernel: Path, arbol: Path, dir_ramdisk: Path | None, reporte: Path | None) -> dict:
    if not kernel.is_file() or kernel.stat().st_size == 0:
        raise SystemExit(f"error: no existe el kernel {kernel}")
    if not dir_vendor.is_dir():
        raise SystemExit(f"error: no existe el vendor extraído {dir_vendor}")

    # 1) Kernel
    (arbol / "prebuilt").mkdir(parents=True, exist_ok=True)
    shutil.copy2(kernel, arbol / "prebuilt" / "kernel")

    # 2) Módulos táctiles + dependencias.
    # Se buscan en el vendor Y en el ramdisk del vendor_boot: en el G51 algunos
    # drivers táctiles pueden estar en uno u otro (en la primera compilación solo
    # apareció ili9882_mmi en el vendor). Si un módulo está en los dos, gana el del vendor.
    dirs_modulos = [dir_vendor / "lib" / "modules"]
    if dir_ramdisk:
        dirs_modulos.append(dir_ramdisk / "lib" / "modules")
    deps: dict[str, list[str]] = {}
    ubicaciones: dict[str, Path] = {}
    for d in dirs_modulos:
        for nombre, lista in leer_modules_dep(d / "modules.dep").items():
            deps.setdefault(nombre, lista)
        for nombre in buscar_modulos(d):
            ubicaciones.setdefault(nombre, d / nombre)
    todos = buscar_modulos(dirs_modulos[0])
    elegidos = sorted(m for m in ubicaciones if es_tactil(m))
    orden = ordenar_con_dependencias(elegidos, deps)
    faltantes = copiar_modulos(ubicaciones, orden, arbol / "recovery/root/system/etc/twg51/modulos")
    orden_copiado = [m for m in orden if m not in faltantes]

    # 3) Firmware táctil
    firmware = copiar_firmware_tactil(dir_vendor / "firmware", arbol / "recovery/root/vendor/firmware")

    # 4) fstab
    fstab = buscar_fstab(dir_vendor, dir_ramdisk)
    if fstab is None:
        raise SystemExit("error: no se encontró ningún fstab en el vendor de stock")
    lineas = filtrar_fstab(fstab.read_text(errors="replace"))
    if not any(" /data " in f" {x} " for x in lineas):
        raise SystemExit(f"error: el fstab {fstab} no tiene /data; revisar el firmware")
    escribir_fstab(lineas, arbol / "recovery/root/system/etc/recovery.fstab", str(fstab))

    # 5) Propiedades
    props = leer_props(dir_vendor / "build.prop", dir_vendor / "default.prop")
    escribir_info_mk(props, arbol / "generated" / "info.mk")

    modulos_ramdisk = []
    if dir_ramdisk:
        modulos_ramdisk = buscar_modulos(dir_ramdisk / "lib" / "modules")

    datos = {
        "huella": props.get("ro.vendor.build.fingerprint", "desconocido"),
        "virtual_ab": props.get("ro.virtual_ab.enabled", "(no figura, se asume true)"),
        "fstab": str(fstab),
        "orden": orden_copiado,
        "faltantes": faltantes,
        "firmware": firmware,
        "fstab_lineas": lineas,
        "todos_modulos": todos,
        "modulos_ramdisk": modulos_ramdisk,
        "blobs": listar_blobs_cifrado(dir_vendor),
    }
    if reporte:
        escribir_reporte(reporte, datos)
    return datos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Completa el device tree de TWG51 con el firmware de stock")
    ap.add_argument("--vendor", required=True, type=Path, help="carpeta con el vendor de stock extraído")
    ap.add_argument("--kernel", required=True, type=Path, help="kernel sacado del boot.img de stock")
    ap.add_argument("--arbol", required=True, type=Path, help="device/motorola/cypfq")
    ap.add_argument("--vendor-ramdisk", type=Path, default=None, help="ramdisk del vendor_boot extraído (opcional)")
    ap.add_argument("--reporte", type=Path, default=None, help="dónde escribir el reporte Markdown")
    a = ap.parse_args(argv)

    datos = preparar(a.vendor, a.kernel, a.arbol, a.vendor_ramdisk, a.reporte)
    print(f"Huella del firmware: {datos['huella']}")
    print(f"Módulos táctiles (con dependencias): {len(datos['orden'])}")
    for m in datos["orden"]:
        print(f"  - {m}")
    print(f"Firmware táctil copiado: {len(datos['firmware'])} archivo(s)")
    print(f"fstab: {datos['fstab']} -> {len(datos['fstab_lineas'])} línea(s)")
    for linea in datos["fstab_lineas"]:
        print(f"  {linea}")
    # Listas completas en el log (además del reporte), para poder revisarlas
    # mandando solo el zip de logs de GitHub.
    print(f"Módulos del vendor ({len(datos['todos_modulos'])}):")
    print("  " + " ".join(datos["todos_modulos"]))
    print(f"Módulos del vendor_boot ({len(datos['modulos_ramdisk'])}):")
    print("  " + " ".join(datos["modulos_ramdisk"]))
    print(f"Archivos para descifrado ({len(datos['blobs'])}):")
    for b in datos["blobs"]:
        print(f"  {b}")
    if not datos["orden"]:
        print("AVISO: no se encontró ningún módulo táctil; el táctil puede no andar.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
