import math
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp

from conexion_usb import ConexionUSB


# ============================================================
# BLU-I v2.0
# CAMARA + GESTOS + USB + IDENTIFICACION DE MOTORES
# ============================================================


# ============================================================
# CONFIGURACION
# ============================================================

CAMARA = 0

ANCHO_CAMARA = 1280
ALTO_CAMARA = 720

FRAMES_ESTABLES = 4

INTERVALO_REENVIO = 0.25


# ============================================================
# VELOCIDADES ACTUALES DEL ARDUINO
# SOLO PARA MOSTRAR EN PANTALLA
# ============================================================

VELOCIDAD_DERECHO = 185
VELOCIDAD_IZQUIERDO = 255

GIRO_DERECHO = 170
GIRO_IZQUIERDO = 255


# ============================================================
# MODELO MEDIAPIPE
# ============================================================

CARPETA = Path(__file__).resolve().parent

MODELO = CARPETA / "hand_landmarker.task"


URL_MODELO = (
    "https://storage.googleapis.com/"
    "mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/"
    "hand_landmarker.task"
)


# ============================================================
# CONEXIONES DE LA MANO
# ============================================================

CONEXIONES_MANO = [

    # Pulgar
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    # Indice
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    # Medio
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    # Anular
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    # Menique
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),

    # Palma
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
# PREPARAR MODELO
# ============================================================

def preparar_modelo():

    if MODELO.exists():

        print("Modelo MediaPipe encontrado.")

        return True


    print()
    print("Descargando modelo MediaPipe...")


    try:

        urllib.request.urlretrieve(
            URL_MODELO,
            MODELO
        )

        return MODELO.exists()


    except Exception as error:

        print("ERROR DESCARGANDO MODELO:")
        print(error)

        return False


if not preparar_modelo():

    raise SystemExit(1)


# ============================================================
# CONEXION USB
# ============================================================

print()
print("==========================================")
print("BLU-I v2.0")
print("CONECTANDO POR USB")
print("==========================================")
print()


usb = ConexionUSB(
    puerto=None,
    baudios=9600
)


if not usb.conectar():

    print()
    print("No se pudo conectar con BLU-I.")
    print()
    print("Comprueba:")
    print("- Arduino conectado por USB")
    print("- Monitor Serie cerrado")
    print("- Arduino encendido")

    raise SystemExit(1)


# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions

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
        model_asset_path=str(MODELO)
    ),

    running_mode=RunningMode.VIDEO,

    num_hands=1,

    min_hand_detection_confidence=0.55,

    min_hand_presence_confidence=0.55,

    min_tracking_confidence=0.50
)


detector = (
    HandLandmarker
    .create_from_options(
        opciones
    )
)


# ============================================================
# CAMARA
# ============================================================

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

    print("No se pudo abrir la camara.")

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
# DISTANCIA
# ============================================================

def distancia(a, b):

    return math.sqrt(
        (a.x - b.x) ** 2
        +
        (a.y - b.y) ** 2
    )


# ============================================================
# DEDO EXTENDIDO
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
# OBTENER DEDOS
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
    # DETENER
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
            "DETENER"
        )


    # ========================================================
    # PUÑO CERRADO
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
            "AVANZAR"
        )


    # ========================================================
    # DOS DEDOS
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
            "RETROCEDER"
        )


    # ========================================================
    # SOLO INDICE
    # IZQUIERDA / DERECHA
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


        # Solo aceptar movimiento horizontal

        if (
            abs(dx) > abs(dy)
            and
            abs(dx) > 0.05
        ):

            if dx > 0:

                return (
                    "R",
                    "DERECHA"
                )

            else:

                return (
                    "L",
                    "IZQUIERDA"
                )


    # ========================================================
    # GESTO NO RECONOCIDO
    # SEGURIDAD = STOP
    # ========================================================

    return (
        "S",
        "GESTO NO RECONOCIDO"
    )


# ============================================================
# ESTADO DE MOTORES
# ============================================================

def obtener_estado_motores(comando):

    # ========================================================
    # AVANZAR
    # ========================================================

    if comando == "F":

        return {

            "motor_derecho": True,
            "motor_izquierdo": True,

            "derecho":
                f"ADELANTE - PWM {VELOCIDAD_DERECHO}",

            "izquierdo":
                f"ADELANTE - PWM {VELOCIDAD_IZQUIERDO}",

            "motores":
                "DERECHO + IZQUIERDO"
        }


    # ========================================================
    # RETROCEDER
    # ========================================================

    if comando == "B":

        return {

            "motor_derecho": True,
            "motor_izquierdo": True,

            "derecho":
                f"ATRAS - PWM {VELOCIDAD_DERECHO}",

            "izquierdo":
                f"ATRAS - PWM {VELOCIDAD_IZQUIERDO}",

            "motores":
                "DERECHO + IZQUIERDO"
        }


    # ========================================================
    # IZQUIERDA
    # ========================================================

    if comando == "L":

        return {

            "motor_derecho": False,
            "motor_izquierdo": True,

            "derecho":
                "DETENIDO",

            "izquierdo":
                f"ACTIVO - PWM {GIRO_IZQUIERDO}",

            "motores":
                "MOTOR IZQUIERDO"
        }


    # ========================================================
    # DERECHA
    # ========================================================

    if comando == "R":

        return {

            "motor_derecho": True,
            "motor_izquierdo": False,

            "derecho":
                f"ACTIVO - PWM {GIRO_DERECHO}",

            "izquierdo":
                "DETENIDO",

            "motores":
                "MOTOR DERECHO"
        }


    # ========================================================
    # DETENER
    # ========================================================

    return {

        "motor_derecho": False,
        "motor_izquierdo": False,

        "derecho":
            "DETENIDO",

        "izquierdo":
            "DETENIDO",

        "motores":
            "NINGUNO"
    }


# ============================================================
# DIBUJAR MANO
# ============================================================

def dibujar_mano(
    frame,
    mano
):

    alto, ancho, _ = frame.shape


    puntos = []


    # ========================================================
    # CONVERTIR COORDENADAS
    # ========================================================

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
    # LINEAS
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
    # PUNTOS
    # ========================================================

    for indice, punto in enumerate(puntos):

        x, y = punto


        # PUNTAS

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


        # RESTO DE PUNTOS

        else:

            cv2.circle(
                frame,
                (x, y),
                6,
                (0, 255, 0),
                -1,
                cv2.LINE_AA
            )


            cv2.circle(
                frame,
                (x, y),
                8,
                (0, 0, 0),
                1,
                cv2.LINE_AA
            )


    # ========================================================
    # MUÑECA
    # ========================================================

    cv2.circle(
        frame,
        puntos[0],
        10,
        (255, 0, 255),
        -1,
        cv2.LINE_AA
    )


# ============================================================
# PANEL
# ============================================================

def dibujar_panel(
    frame,
    gesto,
    comando,
    mano_detectada
):

    estado = obtener_estado_motores(
        comando
    )


    # ========================================================
    # PANEL NEGRO
    # ========================================================

    cv2.rectangle(
        frame,
        (15, 15),
        (620, 300),
        (20, 20, 20),
        -1
    )


    # ========================================================
    # TITULO
    # ========================================================

    cv2.putText(
        frame,
        "BLU-I v2.0",
        (35, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.85,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )


    cv2.putText(
        frame,
        "CONTROL POR GESTOS + USB",
        (35, 80),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (200, 200, 200),
        1,
        cv2.LINE_AA
    )


    # ========================================================
    # MANO
    # ========================================================

    if mano_detectada:

        texto_mano = "MANO DETECTADA"

        color_mano = (
            0,
            255,
            0
        )

    else:

        texto_mano = "SIN MANO"

        color_mano = (
            0,
            0,
            255
        )


    cv2.putText(
        frame,
        texto_mano,
        (35, 115),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.60,
        color_mano,
        2,
        cv2.LINE_AA
    )


    # ========================================================
    # GESTO
    # ========================================================

    cv2.putText(
        frame,
        "GESTO: " + gesto,
        (35, 150),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (0, 255, 255),
        2,
        cv2.LINE_AA
    )


    # ========================================================
    # COMANDO
    # ========================================================

    cv2.putText(
        frame,
        "COMANDO: " + comando,
        (35, 180),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.62,
        (255, 255, 0),
        2,
        cv2.LINE_AA
    )


    # ========================================================
    # MOTORES
    # ========================================================

    cv2.putText(
        frame,
        "MOTORES: " + estado["motores"],
        (35, 215),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.58,
        (255, 200, 100),
        2,
        cv2.LINE_AA
    )


    # MOTOR DERECHO

    cv2.putText(
        frame,
        "DERECHO: " + estado["derecho"],
        (35, 250),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (
            0,
            255,
            0
        )
        if estado["motor_derecho"]
        else
        (
            100,
            100,
            100
        ),
        2,
        cv2.LINE_AA
    )


    # MOTOR IZQUIERDO

    cv2.putText(
        frame,
        "IZQUIERDO: " + estado["izquierdo"],
        (35, 280),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.52,
        (
            0,
            255,
            0
        )
        if estado["motor_izquierdo"]
        else
        (
            100,
            100,
            100
        ),
        2,
        cv2.LINE_AA
    )


# ============================================================
# VARIABLES
# ============================================================

ultimo_gesto = None

contador_gesto = 0

comando_activo = "S"

ultimo_envio = 0

ultimo_timestamp = 0

ultimo_comando_impreso = None


# ============================================================
# INFORMACION
# ============================================================

print()
print("==========================================")
print("BLU-I v2.0")
print("CONTROL GESTUAL")
print("==========================================")
print()

print("GESTOS:")
print()

print("PUÑO CERRADO")
print("  -> AVANZAR")
print()

print("DOS DEDOS")
print("INDICE + MEDIO")
print("  -> RETROCEDER")
print()

print("INDICE HACIA IZQUIERDA")
print("  -> IZQUIERDA")
print()

print("INDICE HACIA DERECHA")
print("  -> DERECHA")
print()

print("PALMA ABIERTA")
print("  -> DETENER")
print()

print("Q = SALIR")
print()


# ============================================================
# DETENER AL INICIAR
# ============================================================

usb.enviar(
    "S"
)


# ============================================================
# LOOP PRINCIPAL
# ============================================================

try:

    while True:

        ok, frame = cap.read()


        if not ok:

            usb.enviar(
                "S"
            )

            break


        # ====================================================
        # ESPEJO
        # ====================================================

        frame = cv2.flip(
            frame,
            1
        )


        # ====================================================
        # RGB
        # ====================================================

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        imagen_mp = mp.Image(

            image_format=
                mp.ImageFormat.SRGB,

            data=rgb
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
        # DETECCION
        # ====================================================

        resultado = (
            detector.detect_for_video(
                imagen_mp,
                timestamp
            )
        )


        comando = "S"

        gesto = "DETENER"

        mano_detectada = False


        # ====================================================
        # MANO
        # ====================================================

        if resultado.hand_landmarks:

            mano_detectada = True


            mano = (
                resultado
                .hand_landmarks[0]
            )


            # Puntos de mano

            dibujar_mano(
                frame,
                mano
            )


            # Reconocer gesto

            comando, gesto = reconocer_gesto(
                mano
            )


        # ====================================================
        # SIN MANO
        # ====================================================

        else:

            comando = "S"

            gesto = "DETENER"


        # ====================================================
        # ESTABILIZACION
        # ====================================================

        if comando == ultimo_gesto:

            contador_gesto += 1


        else:

            ultimo_gesto = comando

            contador_gesto = 1


        if contador_gesto >= FRAMES_ESTABLES:

            comando_activo = comando


        # ====================================================
        # MOSTRAR CAMBIO EN TERMINAL
        # ====================================================

        if (
            comando_activo
            !=
            ultimo_comando_impreso
        ):

            estado = obtener_estado_motores(
                comando_activo
            )


            print()
            print("==========================================")
            print("GESTO:", gesto)
            print("COMANDO:", comando_activo)
            print("MOTORES:", estado["motores"])
            print("DERECHO:", estado["derecho"])
            print("IZQUIERDO:", estado["izquierdo"])
            print("==========================================")


            ultimo_comando_impreso = (
                comando_activo
            )


        # ====================================================
        # ENVIAR AL ARDUINO
        # ====================================================

        ahora = time.monotonic()


        if (
            ahora
            -
            ultimo_envio
            >=
            INTERVALO_REENVIO
        ):

            usb.enviar(
                comando_activo
            )


            respuesta = usb.leer()


            if respuesta:

                print(
                    "BLU-I:",
                    respuesta
                )


            ultimo_envio = ahora


        # ====================================================
        # PANEL
        # ====================================================

        dibujar_panel(
            frame,
            gesto,
            comando_activo,
            mano_detectada
        )


        # ====================================================
        # SALIR
        # ====================================================

        alto, ancho, _ = frame.shape


        cv2.putText(
            frame,
            "Q = SALIR",
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
        # VENTANA
        # ====================================================

        cv2.imshow(
            "BLU-I v2.0 - Control Gestual",
            frame
        )


        tecla = (
            cv2.waitKey(1)
            &
            0xFF
        )


        if tecla == ord("q"):

            break


# ============================================================
# CTRL+C
# ============================================================

except KeyboardInterrupt:

    print()
    print("Programa detenido.")


# ============================================================
# CERRAR
# ============================================================

finally:

    print()
    print("Deteniendo BLU-I...")


    try:

        usb.enviar(
            "S"
        )

        time.sleep(
            0.2
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


    print(
        "Programa terminado."
    )