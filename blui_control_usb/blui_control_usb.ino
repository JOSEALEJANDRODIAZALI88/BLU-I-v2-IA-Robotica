/*
   ============================================================
   BLU-I v2.0
   CONTROL USB + MOTORES
   CALIBRACION INDEPENDIENTE
   ============================================================

   AVANZAR:
   DERECHO   = 220
   IZQUIERDO = 182

   RETROCEDER:
   DERECHO   = 175
   IZQUIERDO = 165

   GIROS:
   DERECHO   = 220
   IZQUIERDO = 235

   COMANDOS:

   F = AVANZAR
   B = RETROCEDER
   L = IZQUIERDA
   R = DERECHA
   S = DETENER

   ============================================================
*/


// ============================================================
// PINES
// ============================================================

// MOTOR DERECHO
const int DIR_D = 13;
const int PWM_D = 11;

// MOTOR IZQUIERDO
const int DIR_I = 12;
const int PWM_I = 6;


// ============================================================
// VELOCIDADES PARA AVANZAR
// ============================================================

const int AVANCE_DERECHO = 220;

const int AVANCE_IZQUIERDO = 182;


// ============================================================
// VELOCIDADES PARA RETROCEDER
// ============================================================

// Bajado de 190 a 175
const int RETROCESO_DERECHO = 175;

const int RETROCESO_IZQUIERDO = 165;


// ============================================================
// VELOCIDADES PARA GIROS
// ============================================================

const int GIRO_DERECHO = 220;

const int GIRO_IZQUIERDO = 235;


// ============================================================
// SEGURIDAD
// ============================================================

const unsigned long TIMEOUT_SEGURIDAD = 1200;

unsigned long ultimoComando = 0;

bool timeoutAplicado = false;


// ============================================================
// DETENER
// ============================================================

void detenerMotores() {

  analogWrite(
    PWM_D,
    0
  );

  analogWrite(
    PWM_I,
    0
  );
}


// ============================================================
// AVANZAR
// ============================================================

void avanzar() {

  // DERECHO ADELANTE
  digitalWrite(
    DIR_D,
    HIGH
  );


  // IZQUIERDO ADELANTE
  digitalWrite(
    DIR_I,
    LOW
  );


  // DERECHO = 220
  analogWrite(
    PWM_D,
    AVANCE_DERECHO
  );


  // IZQUIERDO = 182
  analogWrite(
    PWM_I,
    AVANCE_IZQUIERDO
  );
}


// ============================================================
// RETROCEDER
// ============================================================

void retroceder() {

  // DERECHO ATRAS
  digitalWrite(
    DIR_D,
    LOW
  );


  // IZQUIERDO ATRAS
  digitalWrite(
    DIR_I,
    HIGH
  );


  // DERECHO = 175
  // AHORA MAS LENTO EN RETROCESO
  analogWrite(
    PWM_D,
    RETROCESO_DERECHO
  );


  // IZQUIERDO = 165
  analogWrite(
    PWM_I,
    RETROCESO_IZQUIERDO
  );
}


// ============================================================
// IZQUIERDA
// ============================================================

void izquierda() {

  /*
     DERECHO DETENIDO
     IZQUIERDO = 235
  */

  digitalWrite(
    DIR_D,
    HIGH
  );


  digitalWrite(
    DIR_I,
    LOW
  );


  analogWrite(
    PWM_D,
    0
  );


  analogWrite(
    PWM_I,
    GIRO_IZQUIERDO
  );
}


// ============================================================
// DERECHA
// ============================================================

void derecha() {

  /*
     DERECHO = 220
     IZQUIERDO DETENIDO
  */

  digitalWrite(
    DIR_D,
    HIGH
  );


  digitalWrite(
    DIR_I,
    LOW
  );


  analogWrite(
    PWM_D,
    GIRO_DERECHO
  );


  analogWrite(
    PWM_I,
    0
  );
}


// ============================================================
// PROCESAR COMANDO
// ============================================================

void procesarComando(char comando) {

  switch (comando) {

    // ========================================================
    // AVANZAR
    // ========================================================

    case 'F':

      avanzar();

      Serial.println(
        "ACK:F"
      );

      break;


    // ========================================================
    // RETROCEDER
    // ========================================================

    case 'B':

      retroceder();

      Serial.println(
        "ACK:B"
      );

      break;


    // ========================================================
    // IZQUIERDA
    // ========================================================

    case 'L':

      izquierda();

      Serial.println(
        "ACK:L"
      );

      break;


    // ========================================================
    // DERECHA
    // ========================================================

    case 'R':

      derecha();

      Serial.println(
        "ACK:R"
      );

      break;


    // ========================================================
    // DETENER
    // ========================================================

    case 'S':

      detenerMotores();

      Serial.println(
        "ACK:S"
      );

      break;


    // ========================================================
    // COMPROBAR CONEXION
    // ========================================================

    case '?':

      Serial.println(
        "ACK:BLUI_USB"
      );

      break;


    // ========================================================
    // ERROR
    // ========================================================

    default:

      detenerMotores();

      Serial.print(
        "ERROR:"
      );

      Serial.println(
        comando
      );

      break;
  }
}


// ============================================================
// SETUP
// ============================================================

void setup() {

  // PINES

  pinMode(
    DIR_D,
    OUTPUT
  );

  pinMode(
    PWM_D,
    OUTPUT
  );

  pinMode(
    DIR_I,
    OUTPUT
  );

  pinMode(
    PWM_I,
    OUTPUT
  );


  // SEGURIDAD INICIAL

  detenerMotores();


  // SERIAL USB

  Serial.begin(
    9600
  );


  delay(
    1000
  );


  // ==========================================================
  // INFORMACION
  // ==========================================================

  Serial.println();

  Serial.println(
    "======================================"
  );

  Serial.println(
    "BLU-I V2.0"
  );

  Serial.println(
    "CALIBRACION INDEPENDIENTE"
  );

  Serial.println(
    "======================================"
  );


  // AVANCE

  Serial.println();

  Serial.println(
    "AVANZAR:"
  );

  Serial.print(
    "DERECHO: "
  );

  Serial.println(
    AVANCE_DERECHO
  );

  Serial.print(
    "IZQUIERDO: "
  );

  Serial.println(
    AVANCE_IZQUIERDO
  );


  // RETROCESO

  Serial.println();

  Serial.println(
    "RETROCEDER:"
  );

  Serial.print(
    "DERECHO: "
  );

  Serial.println(
    RETROCESO_DERECHO
  );

  Serial.print(
    "IZQUIERDO: "
  );

  Serial.println(
    RETROCESO_IZQUIERDO
  );


  // GIROS

  Serial.println();

  Serial.println(
    "GIROS:"
  );

  Serial.print(
    "DERECHO: "
  );

  Serial.println(
    GIRO_DERECHO
  );

  Serial.print(
    "IZQUIERDO: "
  );

  Serial.println(
    GIRO_IZQUIERDO
  );


  // COMANDOS

  Serial.println();

  Serial.println(
    "F = AVANZAR"
  );

  Serial.println(
    "B = RETROCEDER"
  );

  Serial.println(
    "L = IZQUIERDA"
  );

  Serial.println(
    "R = DERECHA"
  );

  Serial.println(
    "S = DETENER"
  );

  Serial.println();


  ultimoComando = millis();
}


// ============================================================
// LOOP
// ============================================================

void loop() {

  while (
    Serial.available() > 0
  ) {

    char comando = Serial.read();


    // IGNORAR ENTER Y ESPACIOS

    if (
      comando == '\r'
      ||
      comando == '\n'
      ||
      comando == ' '
    ) {

      continue;
    }


    // MINUSCULA -> MAYUSCULA

    if (
      comando >= 'a'
      &&
      comando <= 'z'
    ) {

      comando = comando - 32;
    }


    // ACTUALIZAR SEGURIDAD

    ultimoComando = millis();

    timeoutAplicado = false;


    // EJECUTAR

    procesarComando(
      comando
    );
  }


  // ==========================================================
  // TIMEOUT DE SEGURIDAD
  // ==========================================================

  if (
    millis() - ultimoComando
    >
    TIMEOUT_SEGURIDAD
  ) {

    if (
      !timeoutAplicado
    ) {

      detenerMotores();

      timeoutAplicado = true;
    }
  }
}