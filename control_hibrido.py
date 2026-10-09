import cv2
import json
import math
import queue
import threading
import time
import unicodedata
import urllib.request
import zipfile

from pathlib import Path

import mediapipe as mp
import sounddevice as sd

from vosk import Model, KaldiRecognizer

from conexion_usb import ConexionUSB


# ============================================================
# BLU-I v2.0
# CONTROL HIBRIDO
#
# IA POR VISION:
# MediaPipe HandLandmarker
#
# IA POR VOZ:
# Vosk
#
# SALIDA:
# USB -> Arduino -> Motores
# ============================================================


# ============================================================
# CONFIGURACION GENERAL
# ============================================================

CAMARA = 0

ANCHO_CAMARA = 1280
ALTO_CAMARA = 720

BAUDIOS = 9600

FRECUENCIA_MICROFONO = 16000


# ============================================================
# ESTABILIDAD DE GESTOS
# ============================================================

FRAMES_ESTABLES = 4


# ============================================================
# COMUNICACION CON ARDUINO
# ============================================================

INTERVALO_REENVIO = 0.25


# ============================================================
# PRIORIDAD DE VOZ
# ============================================================
#
# Cuando dices:
#
# "avanzar"
#
# la orden de voz tiene prioridad durante 4 segundos.
#
# Después de ese tiempo vuelve automáticamente
# al control por gestos.
#
# La palma abierta siempre puede DETENER.
# ============================================================

TIEMPO_PRIORIDAD_VOZ = 4.0


# ============================================================
# VELOCIDADES ACTUALES
#
# SOLO SE UTILIZAN PARA MOSTRAR INFORMACION EN PANTALLA.
#
# LAS VELOCIDADES REALES ESTAN EN EL ARDUINO.
# ============================================================

VELOCIDAD_DERECHO = 185
VELOCIDAD_IZQUIERDO = 208

GIRO_DERECHO = 200
GIRO_IZQUIERDO = 235


# ============================================================
# CARPETA DEL PROYECTO
# ============================================================

CARPETA = Path(__file__).resolve().parent


# ============================================================
# MODELO DE MANO
# ============================================================

MODELO_MANO = (
    CARPETA
    /
    "hand_landmarker.task"
)


URL_MODELO_MANO = (
    "https://storage.googleapis.com/"
    "mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/"
    "hand_landmarker.task"
)


# ============================================================
# MODELO DE VOZ
# ============================================================

NOMBRE_MODELO_VOZ = (
    "vosk-model-small-es-0.42"
)


CARPETA_MODELO_VOZ = (
    CARPETA
    /
    NOMBRE_MODELO_VOZ
)


ZIP_MODELO_VOZ = (
    CARPETA
    /
    f"{NOMBRE_MODELO_VOZ}.zip"
)


URL_MODELO_VOZ = (
    "https://alphacephei.com/"
    "vosk/models/"
    "vosk-model-small-es-0.42.zip"
)


# ============================================================
# CONEXIONES DE LA MANO
# ============================================================

CONEXIONES_MANO = [

    # PULGAR
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    # INDICE
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    # MEDIO
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    # ANULAR
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    # MENIQUE
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),

    # PALMA
    (0, 17)
]


PUNTAS_DEDOS = [
    4,
    8,
    12,
    16,
    20
]


# ============================================================
# COLA DEL MICROFONO
# ============================================================

cola_audio = queue.Queue()


# ============================================================
# EVENTO PARA CERRAR TODO
# ============================================================

evento_salida = threading.Event()


# ============================================================
# BLOQUEO PARA VARIABLES DE VOZ
# ============================================================

bloqueo_voz = threading.Lock()


# ============================================================
# ESTADO GLOBAL DE VOZ
# ============================================================

estado_voz = {

    "comando": None,

    "texto": "",

    "tiempo": 0.0,

    "salir": False
}


# ============================================================
# PREPARAR MODELO DE MANO
# ============================================================

def preparar_modelo_mano():

    if MODELO_MANO.exists():

        print(
            "Modelo de mano encontrado."
        )

        return True


    print()
    print("==============================================")
    print("DESCARGANDO MODELO DE MANO")
    print("==============================================")
    print()


    try:

        urllib.request.urlretrieve(
            URL_MODELO_MANO,
            MODELO_MANO
        )


        if MODELO_MANO.exists():

            print(
                "Modelo de mano descargado."
            )

            return True


    except Exception as error:

        print(
            "ERROR DESCARGANDO MODELO DE MANO:"
        )

        print(error)


    return False


# ============================================================
# PREPARAR MODELO DE VOZ
# ============================================================

def preparar_modelo_voz():

    if CARPETA_MODELO_VOZ.exists():

        print(
            "Modelo de voz encontrado."
        )

        return True


    print()
    print("==============================================")
    print("DESCARGANDO MODELO DE VOZ")
    print("==============================================")
    print()


    try:

        urllib.request.urlretrieve(
            URL_MODELO_VOZ,
            ZIP_MODELO_VOZ
        )

    except Exception as error:

        print(
            "ERROR DESCARGANDO MODELO DE VOZ:"
        )

        print(error)

        return False


    print()
    print(
        "Extrayendo modelo de voz..."
    )


    try:

        with zipfile.ZipFile(
            ZIP_MODELO_VOZ,
            "r"
        ) as archivo:

            archivo.extractall(
                CARPETA
            )

    except Exception as error:

        print(
            "ERROR EXTRAYENDO MODELO:"
        )

        print(error)

        return False


    try:

        if ZIP_MODELO_VOZ.exists():

            ZIP_MODELO_VOZ.unlink()

    except Exception:

        pass


    if CARPETA_MODELO_VOZ.exists():

        print(
            "Modelo de voz preparado correctamente."
        )

        return True


    return False


# ============================================================
# NORMALIZAR TEXTO
# ============================================================

def normalizar_texto(texto):

    texto = texto.lower().strip()


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

def interpretar_voz(texto):

    texto = normalizar_texto(
        texto
    )


    if not texto:

        return None


    # --------------------------------------------------------
    # SALIR
    # --------------------------------------------------------

    if (
        "salir" in texto
        or
        "cerrar programa" in texto
        or
        "terminar programa" in texto
    ):

        return "X"


    # --------------------------------------------------------
    # ATRAS
    #
    # Se comprueba antes de PARAR para evitar problemas
    # con frases como "para atras".
    # --------------------------------------------------------

    if (
        "atras" in texto
        or
        "retrocede" in texto
        or
        "retroceder" in texto
        or
        "reversa" in texto
    ):

        return "B"


    # --------------------------------------------------------
    # IZQUIERDA
    # --------------------------------------------------------

    if "izquierda" in texto:

        return "L"


    # --------------------------------------------------------
    # DERECHA
    # --------------------------------------------------------

    if "derecha" in texto:

        return "R"


    # --------------------------------------------------------
    # AVANZAR
    # --------------------------------------------------------

    if (
        "avanzar" in texto
        or
        "avanza" in texto
        or
        "adelante" in texto
    ):

        return "F"


    # --------------------------------------------------------
    # DETENER
    # --------------------------------------------------------

    if (
        "detener" in texto
        or
        "detente" in texto
        or
        "parar" in texto
        or
        "parate" in texto
        or
        "alto" in texto
        or
        "frena" in texto
        or
        "frenar" in texto
        or
        texto == "para"
    ):

        return "S"


    return None


# ============================================================
# NOMBRE DEL COMANDO
# ============================================================

def nombre_comando(comando):

    if comando == "F":

        return "AVANZAR"


    if comando == "B":

        return "RETROCEDER"


    if comando == "L":

        return "IZQUIERDA"


    if comando == "R":

        return "DERECHA"


    if comando == "S":

        return "DETENER"


    return "NINGUNO"


# ============================================================
# CALLBACK DEL MICROFONO
# ============================================================

def callback_microfono(
    indata,
    frames,
    tiempo_audio,
    estado
):

    if estado:

        print(
            "MICROFONO:",
            estado
        )


    try:

        cola_audio.put_nowait(
            bytes(indata)
        )

    except queue.Full:

        pass


# ============================================================
# HILO DE RECONOCIMIENTO DE VOZ
# ============================================================

def hilo_reconocimiento_voz(
    modelo_voz
):

    reconocedor = KaldiRecognizer(

        modelo_voz,

        FRECUENCIA_MICROFONO
    )


    try:

        with sd.RawInputStream(

            samplerate=
                FRECUENCIA_MICROFONO,

            blocksize=
                8000,

            dtype=
                "int16",

            channels=
                1,

            callback=
                callback_microfono

        ):


            print()
            print(
                "MICROFONO ACTIVO"
            )

            print(
                "Reconocimiento de voz listo."
            )

            print()


            while not evento_salida.is_set():

                try:

                    datos = cola_audio.get(
                        timeout=0.2
                    )

                except queue.Empty:

                    continue


                if reconocedor.AcceptWaveform(
                    datos
                ):

                    resultado = json.loads(
                        reconocedor.Result()
                    )


                    texto = resultado.get(
                        "text",
                        ""
                    ).strip()


                    if not texto:

                        continue


                    comando = interpretar_voz(
                        texto
                    )


                    print()
                    print(
                        "VOZ ESCUCHADA:",
                        texto.upper()
                    )


                    if comando is None:

                        print(
                            "No corresponde a un comando."
                        )

                        continue


                    # ----------------------------------------
                    # SALIR
                    # ----------------------------------------

                    if comando == "X":

                        with bloqueo_voz:

                            estado_voz["salir"] = True

                            estado_voz["comando"] = "S"

                            estado_voz["texto"] = texto

                            estado_voz["tiempo"] = (
                                time.monotonic()
                            )


                        evento_salida.set()

                        break


                    # ----------------------------------------
                    # GUARDAR COMANDO
                    # ----------------------------------------

                    with bloqueo_voz:

                        estado_voz["comando"] = comando

                        estado_voz["texto"] = texto

                        estado_voz["tiempo"] = (
                            time.monotonic()
                        )


                    print(
                        "COMANDO DE VOZ:",
                        nombre_comando(comando)
                    )


    except Exception as error:

        print()
        print(
            "ERROR EN EL MICROFONO:"
        )

        print(error)

        print()


# ============================================================
# DISTANCIA ENTRE LANDMARKS
# ============================================================

def distancia(a, b):

    return math.sqrt(

        (a.x - b.x) ** 2

        +

        (a.y - b.y) ** 2
    )


# ============================================================
# COMPROBAR DEDO EXTENDIDO
# ============================================================

def dedo_extendido(
    mano,
    punta,
    articulacion
):

    muneca = mano[0]


    distancia_punta = distancia(
        mano[punta],
        muneca
    )


    distancia_articulacion = distancia(
        mano[articulacion],
        muneca
    )


    return (
        distancia_punta
        >
        distancia_articulacion * 1.12
    )


# ============================================================
# ESTADO DE LOS DEDOS
# ============================================================

def obtener_dedos(mano):

    return {

        "indice":
            dedo_extendido(
                mano,
                8,
                6
            ),

        "medio":
            dedo_extendido(
                mano,
                12,
                10
            ),

        "anular":
            dedo_extendido(
                mano,
                16,
                14
            ),

        "menique":
            dedo_extendido(
                mano,
                20,
                18
            )
    }


# ============================================================
# RECONOCER GESTO
# ============================================================

def reconocer_gesto(mano):

    dedos = obtener_dedos(
        mano
    )


    # ========================================================
    # PALMA ABIERTA
    # STOP
    # ========================================================

    if (
        dedos["indice"]
        and
        dedos["medio"]
        and
        dedos["anular"]
        and
        dedos["menique"]
    ):

        return (
            "S",
            "DETENER",
            True
        )


    # ========================================================
    # PUÑO
    # AVANZAR
    # ========================================================

    if (
        not dedos["indice"]
        and
        not dedos["medio"]
        and
        not dedos["anular"]
        and
        not dedos["menique"]
    ):

        return (
            "F",
            "AVANZAR",
            False
        )


    # ========================================================
    # INDICE + MEDIO
    # RETROCEDER
    # ========================================================

    if (
        dedos["indice"]
        and
        dedos["medio"]
        and
        not dedos["anular"]
        and
        not dedos["menique"]
    ):

        return (
            "B",
            "RETROCEDER",
            False
        )


    # ========================================================
    # SOLO INDICE
    # ========================================================

    if (
        dedos["indice"]
        and
        not dedos["medio"]
        and
        not dedos["anular"]
        and
        not dedos["menique"]
    ):

        punta = mano[8]

        base = mano[5]


        dx = (
            punta.x
            -
            base.x
        )


        dy = (
            punta.y
            -
            base.y
        )


        if (
            abs(dx) > abs(dy)
            and
            abs(dx) > 0.05
        ):

            if dx > 0:

                return (
                    "R",
                    "DERECHA",
                    False
                )

            else:

                return (
                    "L",
                    "IZQUIERDA",
                    False
                )


    return (
        None,
        "NO RECONOCIDO",
        False
    )


# ============================================================
# DIBUJAR MANO
# ============================================================

def dibujar_mano(
    frame,
    mano
):

    alto, ancho, _ = frame.shape


    puntos = []


    for landmark in mano:

        x = int(
            landmark.x
            *
            ancho
        )


        y = int(
            landmark.y
            *
            alto
        )


        puntos.append(
            (x, y)
        )


    # ========================================================
    # DIBUJAR LINEAS
    # ========================================================

    for inicio, final in CONEXIONES_MANO:

        cv2.line(

            frame,

            puntos[inicio],

            puntos[final],

            (255, 255, 255),

            3,

            cv2.LINE_AA
        )


    # ========================================================
    # DIBUJAR LANDMARKS
    # ========================================================

    for indice, punto in enumerate(
        puntos
    ):

        x, y = punto


        if indice in PUNTAS_DEDOS:

            cv2.circle(

                frame,

                (x, y),

                10,

                (0, 255, 255),

                -1,

                cv2.LINE_AA
            )


            cv2.circle(

                frame,

                (x, y),

                13,

                (0, 0, 0),

                2,

                cv2.LINE_AA
            )


        else:

            cv2.circle(

                frame,

                (x, y),

                6,

                (0, 255, 0),

                -1,

                cv2.LINE_AA
            )


    # MUÑECA

    cv2.circle(

        frame,

        puntos[0],

        10,

        (255, 0, 255),

        -1,

        cv2.LINE_AA
    )


# ============================================================
# INFORMACION DE MOTORES
# ============================================================

def informacion_motores(
    comando
):

    if comando == "F":

        return (
            f"DERECHO {VELOCIDAD_DERECHO} | "
            f"IZQUIERDO {VELOCIDAD_IZQUIERDO}"
        )


    if comando == "B":

        return (
            f"DERECHO {VELOCIDAD_DERECHO} | "
            f"IZQUIERDO {VELOCIDAD_IZQUIERDO}"
        )


    if comando == "L":

        return (
            f"IZQUIERDO {GIRO_IZQUIERDO}"
        )


    if comando == "R":

        return (
            f"DERECHO {GIRO_DERECHO}"
        )


    return "MOTORES DETENIDOS"


# ============================================================
# DIBUJAR PANEL
# ============================================================

def dibujar_panel(
    frame,
    comando,
    fuente,
    gesto,
    voz,
    mano_detectada
):

    cv2.rectangle(

        frame,

        (15, 15),

        (720, 315),

        (20, 20, 20),

        -1
    )


    # ========================================================
    # TITULO
    # ========================================================

    cv2.putText(

        frame,

        "BLU-I v2.0 - CONTROL HIBRIDO IA",

        (35, 50),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.75,

        (255, 255, 255),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # CAMARA
    # ========================================================

    texto_mano = (
        "DETECTADA"
        if mano_detectada
        else
        "NO DETECTADA"
    )


    cv2.putText(

        frame,

        "MANO: " + texto_mano,

        (35, 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.58,

        (0, 255, 0)
        if mano_detectada
        else
        (120, 120, 120),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # GESTO
    # ========================================================

    cv2.putText(

        frame,

        "GESTO: " + gesto,

        (35, 125),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.58,

        (0, 255, 255),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # VOZ
    # ========================================================

    texto_voz = voz.upper()

    if not texto_voz:

        texto_voz = "---"


    cv2.putText(

        frame,

        "VOZ: " + texto_voz,

        (35, 160),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (255, 200, 100),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # FUENTE
    # ========================================================

    cv2.putText(

        frame,

        "CONTROL ACTIVO: " + fuente,

        (35, 200),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.62,

        (255, 255, 0),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # COMANDO
    # ========================================================

    cv2.putText(

        frame,

        "COMANDO: "
        +
        nombre_comando(
            comando
        )
        +
        " ["
        +
        comando
        +
        "]",

        (35, 240),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (0, 255, 0)
        if comando != "S"
        else
        (0, 0, 255),

        2,

        cv2.LINE_AA
    )


    # ========================================================
    # MOTORES
    # ========================================================

    cv2.putText(

        frame,

        "MOTORES: "
        +
        informacion_motores(
            comando
        ),

        (35, 280),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.52,

        (220, 220, 220),

        1,

        cv2.LINE_AA
    )


# ============================================================
# PREPARAR MODELOS
# ============================================================

print()
print("==============================================")
print("BLU-I v2.0")
print("CONTROL HIBRIDO")
print("CAMARA + VOZ + IA")
print("==============================================")
print()


if not preparar_modelo_mano():

    print(
        "No se pudo preparar MediaPipe."
    )

    raise SystemExit(1)


if not preparar_modelo_voz():

    print(
        "No se pudo preparar Vosk."
    )

    raise SystemExit(1)


# ============================================================
# CONECTAR ARDUINO
# ============================================================

print()
print(
    "Conectando Arduino..."
)


usb = ConexionUSB(

    puerto=None,

    baudios=BAUDIOS
)


if not usb.conectar():

    print()
    print(
        "ERROR: no se pudo conectar con Arduino."
    )

    print()
    print(
        "Cierra el Monitor Serie."
    )

    print(
        "No ejecutes camara_usb.py o voz_usb.py al mismo tiempo."
    )

    raise SystemExit(1)


print(
    "Arduino conectado."
)


# ============================================================
# CARGAR MODELO MEDIAPIPE
# ============================================================

BaseOptions = (
    mp.tasks.BaseOptions
)


HandLandmarker = (
    mp.tasks.vision.HandLandmarker
)


HandLandmarkerOptions = (
    mp.tasks.vision.HandLandmarkerOptions
)


RunningMode = (
    mp.tasks.vision.RunningMode
)


opciones = HandLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=
            str(MODELO_MANO)
    ),

    running_mode=
        RunningMode.VIDEO,

    num_hands=
        1,

    min_hand_detection_confidence=
        0.55,

    min_hand_presence_confidence=
        0.55,

    min_tracking_confidence=
        0.50
)


detector = (
    HandLandmarker
    .create_from_options(
        opciones
    )
)


# ============================================================
# CARGAR MODELO DE VOZ
# ============================================================

print(
    "Cargando modelo de voz..."
)


modelo_voz = Model(
    str(
        CARPETA_MODELO_VOZ
    )
)


# ============================================================
# INICIAR HILO DE VOZ
# ============================================================

hilo_voz = threading.Thread(

    target=
        hilo_reconocimiento_voz,

    args=(
        modelo_voz,
    ),

    daemon=True
)


hilo_voz.start()


# ============================================================
# ABRIR CAMARA
# ============================================================

print(
    "Abriendo camara..."
)


cap = cv2.VideoCapture(

    CAMARA,

    cv2.CAP_DSHOW
)


if not cap.isOpened():

    cap.release()

    cap = cv2.VideoCapture(
        CAMARA
    )


if not cap.isOpened():

    print(
        "ERROR: no se pudo abrir la camara."
    )

    evento_salida.set()

    usb.cerrar()

    detector.close()

    raise SystemExit(1)


cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    ANCHO_CAMARA
)


cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    ALTO_CAMARA
)


# ============================================================
# VARIABLES DE GESTOS
# ============================================================

candidato_gesto = None

contador_gesto = 0

comando_gesto_estable = None

nombre_gesto_estable = (
    "SIN GESTO"
)


ultimo_timestamp = 0

ultimo_envio = 0

ultimo_comando_impreso = None

ultima_fuente_impresa = None


# ============================================================
# DETENER ANTES DE INICIAR
# ============================================================

usb.enviar(
    "S"
)


print()
print("==============================================")
print("SISTEMA LISTO")
print("==============================================")
print()

print("GESTOS:")
print("PUÑO              -> AVANZAR")
print("DOS DEDOS         -> RETROCEDER")
print("INDICE IZQUIERDA  -> IZQUIERDA")
print("INDICE DERECHA    -> DERECHA")
print("PALMA ABIERTA     -> DETENER")
print()

print("VOZ:")
print("AVANZAR")
print("ATRAS")
print("IZQUIERDA")
print("DERECHA")
print("DETENER")
print("SALIR")
print()

print("Q = CERRAR PROGRAMA")
print()


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    while not evento_salida.is_set():

        ok, frame = cap.read()


        if not ok:

            print(
                "ERROR leyendo camara."
            )

            break


        # ====================================================
        # MODO ESPEJO
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )


        # ====================================================
        # CONVERTIR A RGB
        # ====================================================

        rgb = cv2.cvtColor(

            frame,

            cv2.COLOR_BGR2RGB
        )


        imagen_mp = mp.Image(

            image_format=
                mp.ImageFormat.SRGB,

            data=
                rgb
        )


        # ====================================================
        # TIMESTAMP
        # ====================================================

        timestamp = (
            time.monotonic_ns()
            //
            1_000_000
        )


        if timestamp <= ultimo_timestamp:

            timestamp = (
                ultimo_timestamp
                +
                1
            )


        ultimo_timestamp = timestamp


        # ====================================================
        # DETECTAR MANO
        # ====================================================

        resultado = (
            detector.detect_for_video(

                imagen_mp,

                timestamp
            )
        )


        mano_detectada = False

        comando_gesto_actual = None

        nombre_gesto_actual = (
            "SIN MANO"
        )

        stop_gesto_inmediato = False


        # ====================================================
        # MANO ENCONTRADA
        # ====================================================

        if resultado.hand_landmarks:

            mano_detectada = True


            mano = (
                resultado
                .hand_landmarks[0]
            )


            dibujar_mano(
                frame,
                mano
            )


            (
                comando_gesto_actual,
                nombre_gesto_actual,
                stop_gesto_inmediato

            ) = reconocer_gesto(
                mano
            )


        # ====================================================
        # ESTABILIZAR GESTO
        # ====================================================

        if (
            comando_gesto_actual
            ==
            candidato_gesto
        ):

            contador_gesto += 1


        else:

            candidato_gesto = (
                comando_gesto_actual
            )

            contador_gesto = 1


        if (
            contador_gesto
            >=
            FRAMES_ESTABLES
        ):

            comando_gesto_estable = (
                comando_gesto_actual
            )

            nombre_gesto_estable = (
                nombre_gesto_actual
            )


        # ====================================================
        # LEER ESTADO DE VOZ
        # ====================================================

        with bloqueo_voz:

            comando_voz = (
                estado_voz["comando"]
            )

            texto_voz = (
                estado_voz["texto"]
            )

            tiempo_voz = (
                estado_voz["tiempo"]
            )

            salir_voz = (
                estado_voz["salir"]
            )


        if salir_voz:

            break


        # ====================================================
        # ARBITRAJE
        #
        # 1. PALMA ABIERTA = STOP INMEDIATO
        # 2. VOZ RECIENTE = PRIORIDAD
        # 3. GESTO
        # 4. SIN ORDEN = STOP
        # ====================================================

        ahora = time.monotonic()


        if (
            stop_gesto_inmediato
            and
            comando_gesto_actual == "S"
        ):

            comando_final = "S"

            fuente_control = "GESTO / STOP"


        elif (
            comando_voz is not None
            and
            (
                ahora
                -
                tiempo_voz
            )
            <=
            TIEMPO_PRIORIDAD_VOZ
        ):

            comando_final = comando_voz

            fuente_control = "VOZ"


        elif (
            comando_gesto_estable
            in
            [
                "F",
                "B",
                "L",
                "R",
                "S"
            ]
        ):

            comando_final = (
                comando_gesto_estable
            )

            fuente_control = "GESTO"


        else:

            comando_final = "S"

            fuente_control = "SEGURIDAD"


        # ====================================================
        # MOSTRAR CAMBIOS EN CONSOLA
        # ====================================================

        if (
            comando_final
            !=
            ultimo_comando_impreso
            or
            fuente_control
            !=
            ultima_fuente_impresa
        ):

            print()
            print(
                "=============================================="
            )

            print(
                "FUENTE:",
                fuente_control
            )

            print(
                "COMANDO:",
                nombre_comando(
                    comando_final
                )
            )

            print(
                "CODIGO:",
                comando_final
            )

            print(
                "GESTO:",
                nombre_gesto_estable
            )

            print(
                "ULTIMA VOZ:",
                texto_voz
                if texto_voz
                else
                "---"
            )

            print(
                "=============================================="
            )


            ultimo_comando_impreso = (
                comando_final
            )

            ultima_fuente_impresa = (
                fuente_control
            )


        # ====================================================
        # ENVIAR COMANDO A ARDUINO
        # ====================================================

        if (
            ahora
            -
            ultimo_envio
            >=
            INTERVALO_REENVIO
        ):

            usb.enviar(
                comando_final
            )


            respuesta = usb.leer()


            if respuesta:

                # Evitamos llenar demasiado la consola.
                pass


            ultimo_envio = ahora


        # ====================================================
        # DIBUJAR PANEL
        # ====================================================

        dibujar_panel(

            frame,

            comando_final,

            fuente_control,

            nombre_gesto_actual,

            texto_voz,

            mano_detectada
        )


        # ====================================================
        # INSTRUCCION INFERIOR
        # ====================================================

        alto, ancho, _ = (
            frame.shape
        )


        cv2.putText(

            frame,

            "Q = SALIR | PALMA ABIERTA = STOP",

            (
                25,
                alto - 25
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.60,

            (255, 255, 255),

            2,

            cv2.LINE_AA
        )


        # ====================================================
        # MOSTRAR CAMARA
        # ====================================================

        cv2.imshow(

            "BLU-I v2.0 - IA Hibrida",

            frame
        )


        # ====================================================
        # TECLADO
        # ====================================================

        tecla = (
            cv2.waitKey(1)
            &
            0xFF
        )


        if tecla == ord("q"):

            break


# ============================================================
# CTRL + C
# ============================================================

except KeyboardInterrupt:

    print()
    print(
        "Programa detenido manualmente."
    )


# ============================================================
# CERRAR TODO
# ============================================================

finally:

    evento_salida.set()


    print()
    print(
        "Deteniendo BLU-I..."
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


    try:

        cap.release()

    except Exception:

        pass


    try:

        detector.close()

    except Exception:

        pass


    cv2.destroyAllWindows()


    print()
    print(
        "BLU-I detenido correctamente."
    )