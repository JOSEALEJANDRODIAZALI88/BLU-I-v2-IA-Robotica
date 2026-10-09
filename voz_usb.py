import json
import queue
import threading
import time
import unicodedata
import urllib.request
import zipfile
from pathlib import Path

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from conexion_usb import ConexionUSB


# ============================================================
# BLU-I v2.0
# CONTROL POR VOZ + USB
# ============================================================
#
# COMANDOS DE VOZ:
#
# avanzar / adelante   -> F
# atras / retroceder   -> B
# izquierda            -> L
# derecha              -> R
# detener / parar      -> S
# salir                 -> cerrar programa
#
# ============================================================


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

BAUDIOS = 9600

FRECUENCIA_MICROFONO = 16000

INTERVALO_ENVIO = 0.25


# ============================================================
# SEGURIDAD DE MOVIMIENTO
# ============================================================
#
# Cada orden de movimiento dura como maximo 4 segundos.
#
# Ejemplo:
#
# dices "avanzar"
#
# El robot avanza.
#
# Si no recibe otra orden, se detiene automaticamente
# despues de 4 segundos.
#
# Esto evita que el robot siga avanzando si el
# reconocimiento de voz deja de funcionar.
# ============================================================

TIEMPO_MAXIMO_MOVIMIENTO = 4.0


# ============================================================
# MODELO VOSK ESPAÑOL
# ============================================================

CARPETA = Path(__file__).resolve().parent

NOMBRE_MODELO = "vosk-model-small-es-0.42"

CARPETA_MODELO = CARPETA / NOMBRE_MODELO

ARCHIVO_ZIP = CARPETA / f"{NOMBRE_MODELO}.zip"


URL_MODELO = (
    "https://alphacephei.com/vosk/models/"
    "vosk-model-small-es-0.42.zip"
)


# ============================================================
# COLA DE AUDIO
# ============================================================

cola_audio = queue.Queue()


# ============================================================
# VARIABLES DE CONTROL
# ============================================================

comando_actual = "S"

ultimo_comando_voz = time.monotonic()

programa_activo = True

bloqueo = threading.Lock()


# ============================================================
# PREPARAR MODELO DE VOZ
# ============================================================

def preparar_modelo():

    # --------------------------------------------------------
    # Si ya existe, no descargar otra vez
    # --------------------------------------------------------

    if CARPETA_MODELO.exists():

        print()
        print("Modelo de voz encontrado.")

        return True


    print()
    print("==============================================")
    print("PRIMERA EJECUCION")
    print("DESCARGANDO MODELO DE VOZ EN ESPAÑOL")
    print("==============================================")
    print()

    print("Esto solamente se realiza una vez.")
    print()


    # --------------------------------------------------------
    # DESCARGAR ZIP
    # --------------------------------------------------------

    try:

        urllib.request.urlretrieve(
            URL_MODELO,
            ARCHIVO_ZIP
        )

    except Exception as error:

        print()
        print("ERROR DESCARGANDO EL MODELO:")
        print(error)

        return False


    # --------------------------------------------------------
    # EXTRAER ZIP
    # --------------------------------------------------------

    print()
    print("Descarga terminada.")
    print("Extrayendo modelo...")
    print()


    try:

        with zipfile.ZipFile(
            ARCHIVO_ZIP,
            "r"
        ) as archivo:

            archivo.extractall(
                CARPETA
            )

    except Exception as error:

        print()
        print("ERROR EXTRAYENDO EL MODELO:")
        print(error)

        return False


    # --------------------------------------------------------
    # BORRAR ZIP
    # --------------------------------------------------------

    try:

        if ARCHIVO_ZIP.exists():

            ARCHIVO_ZIP.unlink()

    except Exception:

        pass


    # --------------------------------------------------------
    # COMPROBAR
    # --------------------------------------------------------

    if CARPETA_MODELO.exists():

        print()
        print("Modelo instalado correctamente.")

        return True


    print()
    print("No se encontro el modelo despues de extraerlo.")

    return False


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    texto = texto.lower().strip()


    # --------------------------------------------------------
    # QUITAR ACENTOS
    # --------------------------------------------------------

    texto = "".join(

        caracter

        for caracter in unicodedata.normalize(
            "NFD",
            texto
        )

        if unicodedata.category(
            caracter
        ) != "Mn"
    )


    return texto


# ============================================================
# INTERPRETAR COMANDO DE VOZ
# ============================================================

def interpretar_comando(texto):

    texto = normalizar_texto(
        texto
    )


    if not texto:

        return None


    print()
    print(
        "ESCUCHE:",
        texto.upper()
    )


    # ========================================================
    # SALIR
    # ========================================================

    palabras_salir = [

        "salir",
        "cerrar",
        "finalizar",
        "terminar programa"
    ]


    for palabra in palabras_salir:

        if palabra in texto:

            return "X"


    # ========================================================
    # RETROCEDER
    # ========================================================
    #
    # Lo comprobamos antes de "parar" porque alguien
    # podria decir "para atras".
    # ========================================================

    palabras_atras = [

        "atras",
        "retrocede",
        "retroceder",
        "reversa",
        "hacia atras",
        "ve atras",
        "ve hacia atras"
    ]


    for palabra in palabras_atras:

        if palabra in texto:

            return "B"


    # ========================================================
    # IZQUIERDA
    # ========================================================

    palabras_izquierda = [

        "izquierda",
        "gira izquierda",
        "girar izquierda",
        "hacia la izquierda",
        "ve a la izquierda"
    ]


    for palabra in palabras_izquierda:

        if palabra in texto:

            return "L"


    # ========================================================
    # DERECHA
    # ========================================================

    palabras_derecha = [

        "derecha",
        "gira derecha",
        "girar derecha",
        "hacia la derecha",
        "ve a la derecha"
    ]


    for palabra in palabras_derecha:

        if palabra in texto:

            return "R"


    # ========================================================
    # AVANZAR
    # ========================================================

    palabras_avanzar = [

        "avanzar",
        "avanza",
        "adelante",
        "hacia adelante",
        "ve adelante",
        "ve hacia adelante",
        "sigue"
    ]


    for palabra in palabras_avanzar:

        if palabra in texto:

            return "F"


    # ========================================================
    # DETENER
    # ========================================================

    palabras_detener = [

        "detener",
        "detente",
        "parar",
        "parate",
        "alto",
        "frena",
        "frenar",
        "stop"
    ]


    for palabra in palabras_detener:

        if palabra in texto:

            return "S"


    # ========================================================
    # "PARA" SOLAMENTE
    # ========================================================

    palabras = texto.split()


    if texto == "para":

        return "S"


    return None


# ============================================================
# NOMBRE DEL COMANDO
# ============================================================

def nombre_comando(comando):

    if comando == "F":

        return "AVANZAR"

    elif comando == "B":

        return "RETROCEDER"

    elif comando == "L":

        return "IZQUIERDA"

    elif comando == "R":

        return "DERECHA"

    elif comando == "S":

        return "DETENER"

    else:

        return "DESCONOCIDO"


# ============================================================
# ESTABLECER COMANDO
# ============================================================

def establecer_comando(comando):

    global comando_actual
    global ultimo_comando_voz


    with bloqueo:

        comando_actual = comando

        ultimo_comando_voz = (
            time.monotonic()
        )


    print()
    print("==============================================")

    print(
        "COMANDO:",
        nombre_comando(comando)
    )

    print(
        "CODIGO:",
        comando
    )

    print("==============================================")
    print()


# ============================================================
# CALLBACK DEL MICROFONO
# ============================================================

def callback_microfono(
    indata,
    frames,
    tiempo,
    estado
):

    if estado:

        print(
            estado
        )


    cola_audio.put(
        bytes(indata)
    )


# ============================================================
# HILO QUE MANTIENE EL COMANDO EN EL ARDUINO
# ============================================================

def controlar_robot(
    usb
):

    global comando_actual
    global ultimo_comando_voz
    global programa_activo


    ultimo_enviado = None


    while programa_activo:

        ahora = time.monotonic()


        with bloqueo:

            comando = comando_actual

            tiempo_ultimo = ultimo_comando_voz


        # ====================================================
        # AUTO STOP
        # ====================================================

        if comando in [
            "F",
            "B",
            "L",
            "R"
        ]:

            tiempo_transcurrido = (
                ahora
                -
                tiempo_ultimo
            )


            if (
                tiempo_transcurrido
                >
                TIEMPO_MAXIMO_MOVIMIENTO
            ):

                with bloqueo:

                    comando_actual = "S"

                    comando = "S"


                print()
                print("==============================================")
                print("AUTO STOP DE SEGURIDAD")
                print("No se recibio otro comando de voz.")
                print("ROBOT DETENIDO")
                print("==============================================")
                print()


        # ====================================================
        # ENVIAR COMANDO
        # ====================================================

        try:

            usb.enviar(
                comando
            )


            respuesta = usb.leer()


            # Mostrar cambio de comando solamente
            # para no llenar demasiado la terminal

            if comando != ultimo_enviado:

                if respuesta:

                    print(
                        "ARDUINO:",
                        respuesta
                    )


                ultimo_enviado = comando


        except Exception as error:

            print()
            print(
                "ERROR DE COMUNICACION USB:"
            )

            print(error)

            programa_activo = False

            break


        time.sleep(
            INTERVALO_ENVIO
        )


# ============================================================
# INICIO DEL PROGRAMA
# ============================================================

print()
print("==============================================")
print("BLU-I v2.0")
print("CONTROL INTELIGENTE POR VOZ")
print("==============================================")
print()


# ============================================================
# MODELO
# ============================================================

if not preparar_modelo():

    print()
    print(
        "No se pudo preparar el reconocimiento de voz."
    )

    raise SystemExit(1)


# ============================================================
# CONECTAR ARDUINO
# ============================================================

print()
print("Conectando BLU-I por USB...")
print()


usb = ConexionUSB(
    puerto=None,
    baudios=BAUDIOS
)


if not usb.conectar():

    print()
    print("ERROR:")
    print("No se pudo conectar con el Arduino.")
    print()
    print("Comprueba:")
    print("- Cable USB conectado")
    print("- Monitor Serie cerrado")
    print("- camara_usb.py cerrado")

    raise SystemExit(1)


print()
print("Arduino conectado correctamente.")


# ============================================================
# CARGAR VOSK
# ============================================================

print()
print("Cargando inteligencia de voz...")


try:

    modelo = Model(
        str(CARPETA_MODELO)
    )

except Exception as error:

    print()
    print(
        "ERROR CARGANDO MODELO:"
    )

    print(error)

    usb.cerrar()

    raise SystemExit(1)


reconocedor = KaldiRecognizer(
    modelo,
    FRECUENCIA_MICROFONO
)


# ============================================================
# STOP INICIAL
# ============================================================

usb.enviar(
    "S"
)


# ============================================================
# HILO DE CONTROL DEL ROBOT
# ============================================================

hilo_robot = threading.Thread(

    target=controlar_robot,

    args=(
        usb,
    ),

    daemon=True
)


hilo_robot.start()


# ============================================================
# MOSTRAR COMANDOS
# ============================================================

print()
print("==============================================")
print("SISTEMA LISTO")
print("==============================================")
print()

print("PUEDES DECIR:")
print()

print("AVANZAR")
print("ADELANTE")
print()

print("ATRAS")
print("RETROCEDER")
print()

print("IZQUIERDA")
print()

print("DERECHA")
print()

print("DETENER")
print("PARAR")
print("ALTO")
print()

print("SALIR")
print()

print("----------------------------------------------")
print("Habla de forma clara cerca del microfono.")
print("----------------------------------------------")
print()


# ============================================================
# MICROFONO
# ============================================================

try:

    with sd.RawInputStream(

        samplerate=FRECUENCIA_MICROFONO,

        blocksize=8000,

        dtype="int16",

        channels=1,

        callback=callback_microfono

    ):


        print()
        print("MICROFONO ACTIVO")
        print("ESCUCHANDO...")
        print()


        # ====================================================
        # BUCLE DE RECONOCIMIENTO
        # ====================================================

        while programa_activo:

            datos = cola_audio.get()


            if reconocedor.AcceptWaveform(
                datos
            ):

                resultado = json.loads(
                    reconocedor.Result()
                )


                texto = resultado.get(
                    "text",
                    ""
                )


                if not texto:

                    continue


                comando = interpretar_comando(
                    texto
                )


                # ============================================
                # NO SE RECONOCIO UN COMANDO
                # ============================================

                if comando is None:

                    print(
                        "No corresponde a un comando del robot."
                    )

                    continue


                # ============================================
                # SALIR
                # ============================================

                if comando == "X":

                    print()
                    print(
                        "CERRANDO CONTROL POR VOZ..."
                    )


                    establecer_comando(
                        "S"
                    )


                    programa_activo = False

                    break


                # ============================================
                # COMANDO DEL ROBOT
                # ============================================

                establecer_comando(
                    comando
                )


# ============================================================
# CTRL + C
# ============================================================

except KeyboardInterrupt:

    print()
    print(
        "Programa detenido manualmente."
    )


# ============================================================
# ERROR DE MICROFONO
# ============================================================

except Exception as error:

    print()
    print(
        "ERROR CON EL MICROFONO:"
    )

    print(error)


# ============================================================
# CERRAR
# ============================================================

finally:

    programa_activo = False


    print()
    print(
        "Deteniendo motores..."
    )


    try:

        usb.enviar(
            "S"
        )

        time.sleep(
            0.3
        )

    except Exception:

        pass


    try:

        usb.cerrar()

    except Exception:

        pass


    print()
    print(
        "BLU-I detenido correctamente."
    )