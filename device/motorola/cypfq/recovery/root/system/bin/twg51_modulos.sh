#!/system/bin/sh
#
# TWG51 - TWRP para Motorola Moto G51 5G (cypfq)
# Creado por Andrés Londero
#
# Carga los módulos del kernel que necesita el recovery (sobre todo el táctil).
#
# Por qué existe: el G51 se vende con pantallas de distintos fabricantes
# (Chipone, Focaltech, Ilitek, Novatek...). En Android los módulos los carga el
# vendor; en el recovery nadie lo hace, y por eso en los TWRP anteriores el
# táctil no andaba en algunas unidades. El workflow copia al recovery los
# módulos táctiles de TODAS las variantes (con sus dependencias, en orden) y
# acá se intenta cargarlos todos: el del panel que no está simplemente falla.
#
# Resultado y errores: /tmp/twg51_modulos.log (y también en el log del kernel).
#

DIR=/system/etc/twg51/modulos
ORDEN="$DIR/orden.txt"
LOG=/tmp/twg51_modulos.log

registrar() {
    echo "twg51: $1" >> "$LOG" 2>/dev/null
    echo "twg51: $1" > /dev/kmsg 2>/dev/null
}

registrar "inicio de carga de módulos"

if [ ! -f "$ORDEN" ]; then
    registrar "no hay $ORDEN (el árbol se compiló sin módulos)"
else
    while read -r modulo; do
        # Saltea líneas vacías y comentarios.
        case "$modulo" in
            ''|'#'*) continue ;;
        esac
        if [ ! -f "$DIR/$modulo" ]; then
            registrar "falta $modulo"
            continue
        fi
        salida=$(insmod "$DIR/$modulo" 2>&1)
        if [ $? -eq 0 ]; then
            registrar "cargado $modulo"
        else
            # "File exists" = ya estaba cargado (lo cargó el vendor_boot): está bien.
            registrar "no cargó $modulo: $salida"
        fi
    done < "$ORDEN"
fi

# Controlador USB: si el bootloader no lo pasó, se toma el primero disponible.
if [ -z "$(getprop sys.usb.controller)" ]; then
    udc=$(ls /sys/class/udc 2>/dev/null | head -n 1)
    if [ -n "$udc" ]; then
        setprop sys.usb.controller "$udc"
        registrar "controlador USB detectado: $udc"
    else
        registrar "no se encontró controlador USB en /sys/class/udc"
    fi
fi

registrar "fin de carga de módulos"
exit 0
