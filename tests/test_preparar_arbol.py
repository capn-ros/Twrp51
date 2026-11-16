"""
TWG51 - pruebas de scripts/preparar_arbol.py
Creado por Andrés Londero

Se corren con:  python3 -m unittest discover -s tests -v
(también las corre el workflow antes de compilar).
Arman un "vendor" falso en una carpeta temporal y revisan lo que genera el script.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import preparar_arbol as pa  # noqa: E402

FSTAB_STOCK = """\
# fstab de prueba parecido al de Motorola
system      /system      ext4 ro,barrier=1,discard wait,slotselect,avb=vbmeta_system,logical,first_stage_mount,avb_keys=/avb/q-gsi.avbpubkey:/avb/r-gsi.avbpubkey
system_ext  /system_ext  ext4 ro,barrier=1,discard wait,slotselect,avb=vbmeta_system,logical,first_stage_mount
product     /product     ext4 ro,barrier=1,discard wait,slotselect,avb=vbmeta_system,logical,first_stage_mount
vendor      /vendor      ext4 ro,barrier=1,discard wait,slotselect,avb,logical,first_stage_mount
odm         /odm         ext4 ro,barrier=1,discard wait,slotselect,avb,logical,first_stage_mount
/dev/block/by-name/metadata /metadata ext4 noatime,nosuid,nodev,discard wait,check,formattable,first_stage_mount
/dev/block/bootdevice/by-name/userdata /data f2fs noatime,nosuid,nodev,discard,inlinecrypt latemount,wait,check,formattable,fileencryption=aes-256-xts:aes-256-cts:v2+inlinecrypt_optimized+wrappedkey_v0,keydirectory=/metadata/vold/metadata_encryption,quota
/dev/block/bootdevice/by-name/userdata /data ext4 noatime,nosuid,nodev latemount,wait,check
/dev/block/bootdevice/by-name/modem /vendor/firmware_mnt vfat ro,shortname=lower wait,slotselect
/devices/platform/soc/4784000.sdhci/mmc_host* /storage/sdcard1 auto nosuid,nodev voldmanaged=sdcard1:auto
/dev/block/zram0 none swap defaults zramsize=50%
"""

MODULES_DEP = """\
/vendor/lib/modules/chipone_tddi_v2_mmi.ko: /vendor/lib/modules/touchscreen_mmi.ko /vendor/lib/modules/mmi_relay.ko
/vendor/lib/modules/focaltech_v3.ko: /vendor/lib/modules/touchscreen_mmi.ko /vendor/lib/modules/mmi_relay.ko
/vendor/lib/modules/touchscreen_mmi.ko: /vendor/lib/modules/mmi_relay.ko
/vendor/lib/modules/mmi_relay.ko:
/vendor/lib/modules/wlan.ko:
/vendor/lib/modules/fantasma_ts.ko: /vendor/lib/modules/no_existe.ko
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = Path(self.tmp.name)
        self.vendor = r / "vendor"
        mods = self.vendor / "lib" / "modules"
        mods.mkdir(parents=True)
        for m in ["chipone_tddi_v2_mmi.ko", "focaltech_v3.ko", "touchscreen_mmi.ko",
                  "mmi_relay.ko", "wlan.ko", "fantasma_ts.ko"]:
            (mods / m).write_bytes(b"\x7fELF falso " + m.encode())
        (mods / "modules.dep").write_text(MODULES_DEP)
        (self.vendor / "etc").mkdir()
        (self.vendor / "etc" / "fstab.qcom").write_text(FSTAB_STOCK)
        fw = self.vendor / "firmware"
        fw.mkdir()
        (fw / "chipone-tddi-tianma.bin").write_bytes(b"x" * 100)
        (fw / "focaltech-boe.bin").write_bytes(b"y" * 100)
        (fw / "a660_gmu.bin").write_bytes(b"z" * 100)  # GPU, no tiene que copiarse
        (self.vendor / "build.prop").write_text(
            "ro.vendor.build.fingerprint=motorola/cypfq_g/cypfq:12/S1RYAS32.1/1:user/release-keys\n"
            "ro.virtual_ab.enabled=true\n")
        (self.vendor / "bin" / "hw").mkdir(parents=True)
        (self.vendor / "bin" / "hw" / "android.hardware.gatekeeper@1.0-service-qti").write_text("x")
        (self.vendor / "bin" / "hw" / "android.hardware.devicestate").write_text("x")
        self.kernel = r / "kernel"
        self.kernel.write_bytes(b"kernel falso")
        self.arbol = r / "arbol"
        self.arbol.mkdir()
        self.reporte = r / "reporte.md"

    def tearDown(self):
        self.tmp.cleanup()


class TestModulos(Base):
    def test_detecta_tactiles_y_no_otros(self):
        self.assertTrue(pa.es_tactil("chipone_tddi_v2_mmi.ko"))
        self.assertTrue(pa.es_tactil("focaltech_v3.ko"))
        self.assertTrue(pa.es_tactil("nvt_ts.ko"))
        self.assertFalse(pa.es_tactil("wlan.ko"))
        self.assertFalse(pa.es_tactil("mmi_relay.ko"))

    def test_orden_dependencias_primero(self):
        deps = pa.leer_modules_dep(self.vendor / "lib/modules/modules.dep")
        orden = pa.ordenar_con_dependencias(["chipone_tddi_v2_mmi.ko", "focaltech_v3.ko"], deps)
        self.assertLess(orden.index("mmi_relay.ko"), orden.index("touchscreen_mmi.ko"))
        self.assertLess(orden.index("touchscreen_mmi.ko"), orden.index("chipone_tddi_v2_mmi.ko"))
        self.assertLess(orden.index("touchscreen_mmi.ko"), orden.index("focaltech_v3.ko"))
        self.assertEqual(len(orden), len(set(orden)), "no debe repetir módulos")

    def test_tolera_ciclos(self):
        deps = {"a.ko": ["b.ko"], "b.ko": ["a.ko"]}
        orden = pa.ordenar_con_dependencias(["a.ko"], deps)
        self.assertEqual(sorted(orden), ["a.ko", "b.ko"])


class TestFstab(Base):
    def test_filtra_y_quita_avb(self):
        lineas = pa.filtrar_fstab(FSTAB_STOCK)
        montajes = [l.split()[1] for l in lineas]
        self.assertEqual(montajes, ["/system", "/system_ext", "/product", "/vendor", "/odm", "/metadata", "/data"])
        for l in lineas:
            self.assertNotIn("avb", l.split()[4].split(","), l)
            self.assertNotIn("avb_keys", l)
        data = [l for l in lineas if l.split()[1] == "/data"][0]
        self.assertIn("f2fs", data, "debe quedar la primera línea de /data")
        self.assertIn("fileencryption=", data)
        self.assertFalse(any("zram" in l or "sdhci" in l for l in lineas))


class TestPreparar(Base):
    def test_todo_completo(self):
        datos = pa.preparar(self.vendor, self.kernel, self.arbol, None, self.reporte)
        self.assertEqual((self.arbol / "prebuilt/kernel").read_bytes(), b"kernel falso")

        mods = self.arbol / "recovery/root/system/etc/twg51/modulos"
        orden = [l for l in (mods / "orden.txt").read_text().splitlines() if l and not l.startswith("#")]
        self.assertIn("chipone_tddi_v2_mmi.ko", orden)
        self.assertIn("focaltech_v3.ko", orden)
        self.assertIn("mmi_relay.ko", orden)
        self.assertNotIn("wlan.ko", orden)
        self.assertNotIn("no_existe.ko", orden, "lo faltante no va al orden")
        self.assertIn("no_existe.ko", datos["faltantes"])
        for m in orden:
            self.assertTrue((mods / m).is_file(), m)

        fw = self.arbol / "recovery/root/vendor/firmware"
        self.assertTrue((fw / "chipone-tddi-tianma.bin").is_file())
        self.assertTrue((fw / "focaltech-boe.bin").is_file())
        self.assertFalse((fw / "a660_gmu.bin").exists())

        fstab = (self.arbol / "recovery/root/system/etc/recovery.fstab").read_text()
        self.assertIn(" /data ", fstab)

        info = (self.arbol / "generated/info.mk").read_text()
        self.assertIn("TWG51_VIRTUAL_AB := true", info)

        rep = self.reporte.read_text()
        self.assertIn("gatekeeper", rep)
        self.assertNotIn("devicestate", rep)
        self.assertIn("S1RYAS32", rep)

    def test_virtual_ab_false(self):
        (self.vendor / "build.prop").write_text("ro.virtual_ab.enabled=false\n")
        pa.preparar(self.vendor, self.kernel, self.arbol, None, None)
        self.assertIn("TWG51_VIRTUAL_AB := false", (self.arbol / "generated/info.mk").read_text())

    def test_falla_sin_kernel(self):
        with self.assertRaises(SystemExit):
            pa.preparar(self.vendor, self.kernel.parent / "no_hay", self.arbol, None, None)

    def test_falla_sin_fstab(self):
        (self.vendor / "etc" / "fstab.qcom").unlink()
        with self.assertRaises(SystemExit):
            pa.preparar(self.vendor, self.kernel, self.arbol, None, None)

    def test_fstab_desde_ramdisk(self):
        (self.vendor / "etc" / "fstab.qcom").unlink()
        ram = Path(self.tmp.name) / "ramdisk"
        (ram / "first_stage_ramdisk").mkdir(parents=True)
        (ram / "first_stage_ramdisk" / "fstab.qcom").write_text(FSTAB_STOCK)
        datos = pa.preparar(self.vendor, self.kernel, self.arbol, ram, None)
        self.assertTrue(datos["fstab"].endswith("first_stage_ramdisk/fstab.qcom"))

    def test_tactil_en_vendor_boot(self):
        ram = Path(self.tmp.name) / "ramdisk"
        mods = ram / "lib" / "modules"
        mods.mkdir(parents=True)
        (mods / "chipone_tddi_v2_mmi.ko").write_bytes(b"version del ramdisk")
        (mods / "himax_v3_mmi.ko").write_bytes(b"solo en ramdisk")
        (mods / "sensors_class.ko").write_bytes(b"dep")
        (mods / "modules.dep").write_text(
            "/lib/modules/himax_v3_mmi.ko: /lib/modules/sensors_class.ko\n/lib/modules/sensors_class.ko:\n")
        pa.preparar(self.vendor, self.kernel, self.arbol, ram, None)
        dest = self.arbol / "recovery/root/system/etc/twg51/modulos"
        orden = [l for l in (dest / "orden.txt").read_text().splitlines() if l and not l.startswith("#")]
        self.assertIn("himax_v3_mmi.ko", orden)
        self.assertLess(orden.index("sensors_class.ko"), orden.index("himax_v3_mmi.ko"))
        # Si está en los dos lados, se usa el del vendor.
        self.assertTrue((dest / "chipone_tddi_v2_mmi.ko").read_bytes().startswith(b"\x7fELF falso"))


if __name__ == "__main__":
    unittest.main()
