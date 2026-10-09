# BLU-I v2.0 — Inteligencia Artificial aplicada a la Robótica

## 1. Descripción general

**BLU-I v2.0** es un robot móvil controlado desde una computadora mediante USB y Arduino UNO. El sistema integra dos formas de interacción inteligente:

- **Visión artificial con MediaPipe HandLandmarker** para detectar la mano y reconocer gestos.
- **Reconocimiento de voz con Vosk** para transformar órdenes habladas en texto y posteriormente en comandos de movimiento.

El Arduino recibe los comandos por puerto serial USB y controla los motores del robot.

---

## 2. Arquitectura del sistema

```text
                    BLU-I v2.0

          ┌──────────────────────────┐
          │       COMPUTADORA        │
          └────────────┬─────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
     CÁMARA                       MICRÓFONO
        │                             │
        ▼                             ▼
 MediaPipe IA                    Vosk IA
        │                             │
        ▼                             ▼
 Detección de mano            Reconocimiento
 y 21 landmarks                 de voz
        │                             │
        └──────────────┬──────────────┘
                       ▼
              CONTROL HÍBRIDO
                       │
                 F / B / L / R / S
                       │
                       ▼
                 USB SERIAL
                       │
                       ▼
                 ARDUINO UNO
                       │
                       ▼
               DRIVER DE MOTORES
                       │
                       ▼
                    BLU-I
```

---

## 3. Tecnologías utilizadas

### Hardware

- Arduino UNO
- Shield/controlador de motores
- Dos motores DC
- Chasis BLU-I v2.0
- Cámara web o integrada
- Micrófono
- Cable USB

### Software

- Python 3
- Arduino IDE
- OpenCV
- MediaPipe
- Vosk
- SoundDevice
- PySerial

---

## 4. Archivos principales

```text
BluI_v2_CORREGIDO/
│
├── blui_control_usb.ino
├── conexion_usb.py
├── camara_usb.py
├── voz_usb.py
├── control_hibrido.py
├── hand_landmarker.task
└── vosk-model-small-es-0.42/
```

| Archivo | Función |
|---|---|
| `blui_control_usb.ino` | Control físico de motores |
| `conexion_usb.py` | Comunicación serial Python-Arduino |
| `camara_usb.py` | Control únicamente por gestos |
| `voz_usb.py` | Control únicamente por voz |
| `control_hibrido.py` | Cámara + micrófono simultáneamente |
| `hand_landmarker.task` | Modelo de MediaPipe |
| `vosk-model-small-es-0.42` | Modelo de voz en español |

---

## 5. IA de visión artificial

MediaPipe HandLandmarker analiza cada imagen de la cámara y detecta **21 puntos de referencia de la mano**.

Puntos importantes:

```text
0  = muñeca
4  = punta del pulgar
8  = punta del índice
12 = punta del dedo medio
16 = punta del anular
20 = punta del meñique
```

La inferencia se realiza con:

```python
resultado = detector.detect_for_video(
    imagen_mp,
    timestamp
)
```

Y los landmarks se obtienen con:

```python
if resultado.hand_landmarks:
    mano = resultado.hand_landmarks[0]
```

Luego el programa aplica reglas geométricas sobre esos puntos para determinar qué dedos están extendidos y qué gesto realiza el usuario.

### Gestos

| Gesto | Acción | Comando |
|---|---|---|
| Puño cerrado | Avanzar | `F` |
| Índice + medio | Retroceder | `B` |
| Índice hacia izquierda | Izquierda | `L` |
| Índice hacia derecha | Derecha | `R` |
| Palma abierta | Detener | `S` |
| Sin mano | Detener por seguridad | `S` |

---

## 6. IA de reconocimiento de voz

Vosk procesa el audio capturado por el micrófono y lo convierte en texto.

```python
reconocedor = KaldiRecognizer(
    modelo,
    FRECUENCIA_MICROFONO
)
```

El audio reconocido se obtiene con:

```python
if reconocedor.AcceptWaveform(datos):
    resultado = json.loads(
        reconocedor.Result()
    )
```

Ejemplo:

```text
Usuario dice: "AVANZAR"
        ↓
Vosk
        ↓
Texto: "avanzar"
        ↓
Python
        ↓
Comando F
        ↓
Arduino
        ↓
Motores
```

### Comandos de voz

| Voz | Comando |
|---|---|
| Avanzar / Adelante | `F` |
| Atrás / Retroceder | `B` |
| Izquierda | `L` |
| Derecha | `R` |
| Detener / Parar / Alto | `S` |
| Salir | Detiene y cierra el programa |

---

## 7. Qué parte es IA y qué parte no

### IA

- **MediaPipe:** interpreta imágenes y detecta la estructura de la mano.
- **Vosk:** interpreta audio y reconoce el habla.

### Programación tradicional

El código transforma el resultado de los modelos en comandos:

```text
Puño detectado → F
"avanzar" reconocido → F
```

### Robótica

Arduino recibe el comando y controla físicamente los motores:

```text
F → Arduino → driver → motores
```

---

## 8. Comunicación USB

El protocolo utilizado es:

```text
F = Avanzar
B = Retroceder
L = Izquierda
R = Derecha
S = Detener
? = Verificar conexión
```

Arduino responde:

```text
ACK:F
ACK:B
ACK:L
ACK:R
ACK:S
ACK:BLUI_USB
```

La velocidad serial utilizada es:

```text
9600 baudios
```

---

## 9. Pines de motores

### Motor derecho

```text
DIR = 13
PWM = 11
```

### Motor izquierdo

```text
DIR = 12
PWM = 6
```

---

## 10. Calibración final actual

La velocidad de ambos motores se ajustó de forma independiente debido a que físicamente no responden igual.

### Avanzar

```text
Motor derecho   = 220
Motor izquierdo = 182
```

### Retroceder

```text
Motor derecho   = 175
Motor izquierdo = 165
```

### Giros

```text
Giro derecho   = 220
Giro izquierdo = 235
```

---

## 11. Código final del Arduino

Archivo: `blui_control_usb.ino`

```cpp
/*
   BLU-I v2.0
   CONTROL USB + MOTORES
*/

const int DIR_D = 13;
const int PWM_D = 11;
const int DIR_I = 12;
const int PWM_I = 6;

const int AVANCE_DERECHO = 220;
const int AVANCE_IZQUIERDO = 182;

const int RETROCESO_DERECHO = 175;
const int RETROCESO_IZQUIERDO = 165;

const int GIRO_DERECHO = 220;
const int GIRO_IZQUIERDO = 235;

const unsigned long TIMEOUT_SEGURIDAD = 1200;
unsigned long ultimoComando = 0;
bool timeoutAplicado = false;

void detenerMotores() {
  analogWrite(PWM_D, 0);
  analogWrite(PWM_I, 0);
}

void avanzar() {
  digitalWrite(DIR_D, HIGH);
  digitalWrite(DIR_I, LOW);
  analogWrite(PWM_D, AVANCE_DERECHO);
  analogWrite(PWM_I, AVANCE_IZQUIERDO);
}

void retroceder() {
  digitalWrite(DIR_D, LOW);
  digitalWrite(DIR_I, HIGH);
  analogWrite(PWM_D, RETROCESO_DERECHO);
  analogWrite(PWM_I, RETROCESO_IZQUIERDO);
}

void izquierda() {
  digitalWrite(DIR_D, HIGH);
  digitalWrite(DIR_I, LOW);
  analogWrite(PWM_D, 0);
  analogWrite(PWM_I, GIRO_IZQUIERDO);
}

void derecha() {
  digitalWrite(DIR_D, HIGH);
  digitalWrite(DIR_I, LOW);
  analogWrite(PWM_D, GIRO_DERECHO);
  analogWrite(PWM_I, 0);
}

void procesarComando(char comando) {
  switch (comando) {
    case 'F':
      avanzar();
      Serial.println("ACK:F");
      break;

    case 'B':
      retroceder();
      Serial.println("ACK:B");
      break;

    case 'L':
      izquierda();
      Serial.println("ACK:L");
      break;

    case 'R':
      derecha();
      Serial.println("ACK:R");
      break;

    case 'S':
      detenerMotores();
      Serial.println("ACK:S");
      break;

    case '?':
      Serial.println("ACK:BLUI_USB");
      break;

    default:
      detenerMotores();
      Serial.print("ERROR:");
      Serial.println(comando);
      break;
  }
}

void setup() {
  pinMode(DIR_D, OUTPUT);
  pinMode(PWM_D, OUTPUT);
  pinMode(DIR_I, OUTPUT);
  pinMode(PWM_I, OUTPUT);

  detenerMotores();

  Serial.begin(9600);
  delay(1000);

  Serial.println();
  Serial.println("======================================");
  Serial.println("BLU-I V2.0");
  Serial.println("CONTROL USB LISTO");
  Serial.println("======================================");

  Serial.println();
  Serial.println("AVANZAR:");
  Serial.print("DERECHO: ");
  Serial.println(AVANCE_DERECHO);
  Serial.print("IZQUIERDO: ");
  Serial.println(AVANCE_IZQUIERDO);

  Serial.println();
  Serial.println("RETROCEDER:");
  Serial.print("DERECHO: ");
  Serial.println(RETROCESO_DERECHO);
  Serial.print("IZQUIERDO: ");
  Serial.println(RETROCESO_IZQUIERDO);

  Serial.println();
  Serial.println("GIROS:");
  Serial.print("DERECHO: ");
  Serial.println(GIRO_DERECHO);
  Serial.print("IZQUIERDO: ");
  Serial.println(GIRO_IZQUIERDO);

  Serial.println();
  Serial.println("F = AVANZAR");
  Serial.println("B = RETROCEDER");
  Serial.println("L = IZQUIERDA");
  Serial.println("R = DERECHA");
  Serial.println("S = DETENER");
  Serial.println();

  ultimoComando = millis();
}

void loop() {
  while (Serial.available() > 0) {
    char comando = Serial.read();

    if (
      comando == '\r' ||
      comando == '\n' ||
      comando == ' '
    ) {
      continue;
    }

    if (
      comando >= 'a' &&
      comando <= 'z'
    ) {
      comando = comando - 32;
    }

    ultimoComando = millis();
    timeoutAplicado = false;
    procesarComando(comando);
  }

  if (
    millis() - ultimoComando >
    TIMEOUT_SEGURIDAD
  ) {
    if (!timeoutAplicado) {
      detenerMotores();
      timeoutAplicado = true;
    }
  }
}
```

---

## 12. `conexion_usb.py`

Este módulo centraliza la conexión con Arduino.

Funciones principales:

- Detectar automáticamente puertos COM asociados a Arduino/USB Serial.
- Abrir el puerto a 9600 baudios.
- Esperar el reinicio del Arduino.
- Enviar `?` y validar `ACK:BLUI_USB`.
- Enviar los comandos `F`, `B`, `L`, `R` y `S`.
- Cerrar el puerto enviando antes un STOP.

El programa principal usa:

```python
from conexion_usb import ConexionUSB

usb = ConexionUSB(
    puerto=None,
    baudios=9600
)

if usb.conectar():
    usb.enviar("F")
```

---

## 13. `camara_usb.py`

Este archivo implementa el modo de visión artificial independiente.

Responsabilidades:

- Abrir la cámara con OpenCV.
- Convertir cada frame a RGB.
- Procesarlo con MediaPipe.
- Dibujar los 21 landmarks.
- Reconocer gestos.
- Estabilizar los gestos durante varios frames.
- Convertir el gesto a `F/B/L/R/S`.
- Enviar el comando por USB.
- Detener el robot si desaparece la mano.

---

## 14. `voz_usb.py`

Este archivo implementa el control únicamente por voz.

Responsabilidades:

- Abrir el micrófono con SoundDevice.
- Procesar audio con Vosk.
- Convertir voz a texto.
- Normalizar palabras y eliminar acentos.
- Traducir palabras a comandos.
- Enviar el comando al Arduino.
- Aplicar STOP automático de seguridad.

---

## 15. `control_hibrido.py`

Es el archivo principal recomendado para la demostración final.

Integra simultáneamente:

```text
OpenCV
+
MediaPipe
+
SoundDevice
+
Vosk
+
PySerial
```

El sistema utiliza **una sola conexión USB** al Arduino para evitar conflictos de puerto.

### Prioridad recomendada

```text
1. STOP de seguridad
2. Comando reciente de voz
3. Gesto reconocido
4. Sin comando válido = STOP
```

La palma abierta puede utilizarse como parada de emergencia desde la cámara.

---

## 16. Instalación de dependencias

Ejecutar en PowerShell:

```powershell
python -m pip install pyserial opencv-python mediapipe vosk sounddevice
```

---

## 17. Preparación del Arduino

1. Conectar Arduino UNO por USB.
2. Abrir Arduino IDE.
3. Seleccionar Arduino UNO.
4. Seleccionar el puerto COM correcto.
5. Cargar `blui_control_usb.ino`.
6. Esperar que aparezca `Done uploading`.
7. Cerrar el Monitor Serie antes de ejecutar Python.

---

## 18. Ejecución

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\DIAZ\Desktop\BluI_v2_CORREGIDO"
```

Para usar el sistema completo:

```powershell
python control_hibrido.py
```

No ejecutar simultáneamente:

```powershell
python camara_usb.py
```

o:

```powershell
python voz_usb.py
```

mientras `control_hibrido.py` está activo.

---

## 19. Seguridad

El Arduino incluye un timeout:

```cpp
const unsigned long TIMEOUT_SEGURIDAD = 1200;
```

Si deja de recibir comandos durante aproximadamente 1.2 segundos, detiene los motores.

Además, el comando:

```text
S
```

es utilizado para detener el robot.

Se recomienda realizar las primeras pruebas con las ruedas levantadas o en un área despejada.

---

## 20. Explicación para exposición

> **BLU-I v2.0 implementa inteligencia artificial aplicada a la robótica mediante dos sistemas de percepción. MediaPipe HandLandmarker analiza las imágenes capturadas por una cámara para detectar 21 puntos de referencia de la mano y permitir el reconocimiento de gestos. Vosk procesa el audio capturado por el micrófono para reconocer instrucciones habladas. Los resultados de estos modelos son interpretados por un programa en Python, convertidos en comandos y enviados mediante USB a un Arduino UNO, encargado de controlar físicamente los motores del robot.**

---

## 21. Flujo completo

```text
                         USUARIO
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
          GESTOS                        VOZ
             │                           │
             ▼                           ▼
          CÁMARA                     MICRÓFONO
             │                           │
             ▼                           ▼
        MEDIAPIPE                      VOSK
             │                           │
             ▼                           ▼
      21 LANDMARKS               TEXTO RECONOCIDO
             │                           │
             └─────────────┬─────────────┘
                           ▼
                  PROGRAMA PYTHON
                           │
                           ▼
                    F B L R S
                           │
                           ▼
                     USB SERIAL
                           │
                           ▼
                     ARDUINO UNO
                           │
                           ▼
                   CONTROL MOTORES
                           │
                           ▼
                       BLU-I v2.0
```

---

## 22. Estado actual del proyecto

BLU-I v2.0 cuenta actualmente con:

- Control por gestos.
- Detección de 21 landmarks de la mano.
- Reconocimiento de voz en español.
- Control híbrido cámara + micrófono.
- Comunicación serial USB.
- Detección automática del Arduino.
- Avance.
- Retroceso.
- Giro a izquierda.
- Giro a derecha.
- Detención.
- Timeout de seguridad.
- Velocidades independientes para avance, retroceso y giro.
- Calibración individual de ambos motores.

---

## 23. Resumen de calibración

```text
=========================================
BLU-I v2.0
CALIBRACIÓN ACTUAL
=========================================

AVANZAR
Derecho:    220
Izquierdo:  182

RETROCEDER
Derecho:    175
Izquierdo:  165

GIROS
Derecho:    220
Izquierdo:  235

=========================================
```

---

## 24. Conclusión

BLU-I v2.0 integra **visión artificial, reconocimiento de voz, programación en Python, comunicación serial, Arduino y control de motores** dentro de un mismo sistema robótico.

La computadora realiza las tareas de percepción inteligente y el Arduino realiza el control físico de bajo nivel. Esto permite una interacción humano-robot mediante gestos y órdenes habladas.

```text
IA DE VISIÓN
+
IA DE VOZ
+
PYTHON
+
USB SERIAL
+
ARDUINO
+
MOTORES
+
ROBÓTICA
```
