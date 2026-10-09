import time
import serial
import serial.tools.list_ports


class ConexionUSB:

    def __init__(
        self,
        puerto=None,
        baudios=9600
    ):

        self.puerto = puerto
        self.baudios = baudios

        self.serial_usb = None


    # ========================================================
    # BUSCAR ARDUINO
    # ========================================================

    def buscar_arduino(self):

        puertos = list(
            serial.tools.list_ports.comports()
        )


        print()
        print("Puertos encontrados:")
        print()


        for puerto in puertos:

            print(
                puerto.device,
                "-",
                puerto.description
            )


        print()


        # ----------------------------------------------------
        # BUSCAR ARDUINO UNO
        # ----------------------------------------------------

        palabras = [
            "arduino",
            "uno",
            "ch340",
            "wch",
            "usb serial",
            "usb-serial"
        ]


        for puerto in puertos:

            descripcion = (
                puerto.description
                or ""
            ).lower()


            for palabra in palabras:

                if palabra in descripcion:

                    print(
                        "Arduino detectado:",
                        puerto.device
                    )

                    return puerto.device


        return None


    # ========================================================
    # CONECTAR
    # ========================================================

    def conectar(self):

        if self.puerto is None:

            self.puerto = self.buscar_arduino()


        if self.puerto is None:

            print()
            print("No se encontró automáticamente el Arduino.")
            print()

            return False


        print()
        print("========================================")
        print("BLU-I v2.0")
        print("CONEXION USB")
        print("========================================")
        print()

        print(
            f"Conectando a {self.puerto} "
            f"a {self.baudios} baudios..."
        )


        try:

            self.serial_usb = serial.Serial(
                port=self.puerto,
                baudrate=self.baudios,
                timeout=0.2,
                write_timeout=1
            )


            # Arduino UNO suele reiniciarse
            # cuando Python abre el puerto.

            time.sleep(2.5)


            self.serial_usb.reset_input_buffer()
            self.serial_usb.reset_output_buffer()


            print(
                "Arduino conectado por USB."
            )

            print()


            # Comprobar comunicación.

            self.serial_usb.write(b"?")

            self.serial_usb.flush()


            time.sleep(0.2)


            limite = (
                time.monotonic()
                +
                2
            )


            while (
                time.monotonic()
                <
                limite
            ):

                if (
                    self.serial_usb.in_waiting
                    >
                    0
                ):

                    respuesta = (
                        self.serial_usb
                        .readline()
                        .decode(
                            "ascii",
                            errors="ignore"
                        )
                        .strip()
                    )


                    if respuesta:

                        print(
                            "Arduino:",
                            respuesta
                        )


                        if (
                            "ACK:BLUI_USB"
                            in respuesta
                        ):

                            print()
                            print(
                                "BLU-I v2.0 "
                                "confirmado."
                            )

                            return True


                time.sleep(0.02)


            print()
            print(
                "El puerto abrió, "
                "pero BLU-I no respondió."
            )

            self.cerrar()

            return False


        except Exception as error:

            print()
            print(
                "ERROR ABRIENDO USB:"
            )

            print(error)

            return False


    # ========================================================
    # ENVIAR
    # ========================================================

    def enviar(self, comando):

        if self.serial_usb is None:

            return False


        if not self.serial_usb.is_open:

            return False


        comando = (
            str(comando)
            .strip()
            .upper()
        )


        if comando not in (
            "F",
            "B",
            "L",
            "R",
            "S"
        ):

            return False


        try:

            self.serial_usb.write(
                comando.encode("ascii")
            )

            self.serial_usb.flush()

            return True


        except Exception as error:

            print(
                "ERROR ENVIANDO:",
                error
            )

            return False


    # ========================================================
    # LEER
    # ========================================================

    def leer(self):

        if self.serial_usb is None:

            return None


        try:

            if (
                self.serial_usb.in_waiting
                >
                0
            ):

                respuesta = (
                    self.serial_usb
                    .readline()
                    .decode(
                        "ascii",
                        errors="ignore"
                    )
                    .strip()
                )


                if respuesta:

                    return respuesta


        except Exception:

            pass


        return None


    # ========================================================
    # CERRAR
    # ========================================================

    def cerrar(self):

        try:

            if (
                self.serial_usb is not None
                and
                self.serial_usb.is_open
            ):

                self.serial_usb.write(b"S")

                self.serial_usb.flush()

                time.sleep(0.1)

                self.serial_usb.close()


                print(
                    "Conexion USB cerrada."
                )


        except Exception:

            pass