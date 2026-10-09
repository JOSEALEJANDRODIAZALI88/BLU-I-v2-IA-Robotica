import time

from conexion_usb import ConexionUSB


# ============================================================
# BLU-I v2.0
# PRUEBA USB + MOTORES
# ============================================================


usb = ConexionUSB(
    puerto=None,
    baudios=9600
)


# ============================================================
# CONECTAR
# ============================================================

if not usb.conectar():

    print()
    print("No se pudo conectar con BLU-I.")
    print()
    print("Comprueba:")
    print("- Cable USB")
    print("- Arduino encendido")
    print("- Serial Monitor cerrado")

    raise SystemExit(1)


# ============================================================
# FUNCION DE MOVIMIENTO
# ============================================================

def mover(
    comando,
    nombre,
    segundos
):

    print()
    print("========================================")
    print(nombre)
    print("========================================")


    inicio = time.monotonic()


    while (
        time.monotonic()
        -
        inicio
        <
        segundos
    ):

        if usb.enviar(comando):

            print(
                "PC -> BLU-I:",
                comando
            )


        time.sleep(0.05)


        respuesta = usb.leer()


        if respuesta:

            print(
                "BLU-I -> PC:",
                respuesta
            )


        time.sleep(0.20)


# ============================================================
# PROGRAMA
# ============================================================

try:

    mover(
        "S",
        "DETENER",
        1
    )


    mover(
        "F",
        "AVANZAR",
        3
    )


    mover(
        "S",
        "DETENER",
        1
    )


    mover(
        "B",
        "RETROCEDER",
        3
    )


    mover(
        "S",
        "DETENER",
        1
    )


    mover(
        "L",
        "IZQUIERDA",
        3
    )


    mover(
        "S",
        "DETENER",
        1
    )


    mover(
        "R",
        "DERECHA",
        3
    )


    mover(
        "S",
        "DETENER",
        1
    )


except KeyboardInterrupt:

    print()
    print("Prueba detenida.")


finally:

    usb.enviar("S")

    time.sleep(0.2)

    usb.cerrar()


    print()
    print("Prueba terminada.")