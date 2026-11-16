# Preparar el repo y el firmware

*TWG51 — Creado por Andrés Londero*

## 1. Repo en GitHub

1. Crear un repo (puede ser público o privado).
2. **La primera vez** hay que subir también la carpeta `.github/workflows/` (GitHub solo ejecuta
   workflows que ya están en el repo). Lo más simple: descomprimir `twg51.zip` en la PC y subir
   la carpeta `.github` junto con el zip. Las siguientes veces alcanza con subir `twg51.zip`.

## 2. Firmware de stock (lo más importante)

El recovery usa el kernel y los módulos de **tu** firmware. Si no es el mismo que tiene el
teléfono, el táctil no va a cargar.

1. En el teléfono: **Ajustes → Acerca del teléfono → Número de compilación**. Anotalo
   (algo como `S1RYAS32.xx-xx-xx`). También conviene anotar el **canal** (Ajustes → Acerca del
   teléfono → Información de software, o la caja: RETAIL, RETLA, etc.).
2. Buscar el zip de ese número de compilación, por ejemplo en el espejo de lolinet:
   `https://mirrors.lolinet.com/firmware/lenomola/2021/cypfq/official/`
   o con la herramienta oficial de Motorola (Rescue and Smart Assistant), que lo descarga a la PC.
3. Dárselo al workflow de una de estas dos formas:
   - **URL**: pegar el enlace directo en `config/firmware.conf` → `FIRMWARE_URL=...`
   - **Release**: en el repo, *Releases → Draft a new release*, etiqueta `firmware`,
     adjuntar el zip renombrado a `firmware.zip` y publicar.

## 3. Compilar

Notas:
- Cada vez que subís `twg51.zip`, el workflow guarda en el repo su contenido descomprimido
  (con un commit "Descomprimir twg51.zip [skip ci]"), así lo podés ver y editar en GitHub.
- La carpeta `.github` es la excepción: GitHub no deja que un workflow se modifique a sí mismo.
  Si una versión nueva trae cambios en `compilar.yml`, el run muestra un aviso y hay que pegar
  el archivo a mano (Add file → Create new file → `.github/workflows/compilar.yml`, o editarlo).
- El firmware (3 GB) se baja solo la primera vez; después se usa la copia extraída de la caché.

Subir `twg51.zip`. En la pestaña **Actions** aparece "Compilar TWRP G51":

- Si falla en **preparar**, el error dice qué falta (firmware, fstab, vendor).
- Al terminar **preparar**, el resumen del run muestra el **reporte del firmware**: módulos
  táctiles encontrados, fstab y archivos de cifrado. Mandale ese reporte a Claude si algo no anda.
- **compilar** tarda entre 1 y 2 horas (la mayor parte es bajar el código de TWRP).

También se puede lanzar a mano: Actions → Compilar TWRP G51 → *Run workflow*.
