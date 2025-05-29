# brokersProxy.py

import sys
import threading
import zmq

# Colores para output en consola
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class Broker:
    def __init__(self):
        # Dirección (IP:PUERTO) del Health Checker
        self.ip_puerto_health_checker = "localhost:5553"
        # Puerto en el que el broker recibirá peticiones de las Facultades
        # (debe coincidir con lo que ellas usan en "-ip-p-s")
        self.puerto_escuchar_facultad = "5555"

        # Contexto y sockets de ZeroMQ
        self.context = None
        self.frontend = None    # ROUTER  ← Facultades
        self.backend = None     # DEALER  → Servidores (Central o Respaldo)
        self.socket_health_checker = None  # SUB   ← Health Checker

        # Para guardar la dirección (IP:PUERTO) del servidor actualmente activo
        self.current_backend_ip = None


    def crear_comunicacion(self) -> None:
        """Inicializa el contexto, el ROUTER (frontend), el SUB (health)
           y arranca el hilo que escucha actualizaciones del Health Checker."""
        self.context = zmq.Context()

        # 1) FRONTEND: ROUTER para recibir de las Facultades
        self.frontend = self.context.socket(zmq.ROUTER)
        # Bind al puerto en el que las Facultades harán REQ → BROKER
        self.frontend.bind(f"tcp://*:{self.puerto_escuchar_facultad}")
        print(f"{GREEN}Broker: frontend ROUTER escuchando en tcp://*:{self.puerto_escuchar_facultad}{RESET}")

        # 2) BACKEND: DEALER para reenviar a los Servidores (inicialmente no conectado)
        #    Esperaremos a que llegue el primer estado del Health Checker para conectar.
        self.backend = self.context.socket(zmq.DEALER)
        # (No hacemos bind ni connect aquí; se hará en actualizar_servidor_activo())

        # 3) HEALTH_CHECKER: SUB para recibir actualizaciones de qué servidor está activo
        self.socket_health_checker = self.context.socket(zmq.SUB)
        self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")
        self.socket_health_checker.setsockopt_string(zmq.SUBSCRIBE, "")
        print(f"{GREEN}Broker: SUB conectado a Health Checker en tcp://{self.ip_puerto_health_checker}{RESET}")

        # 4) Arrancamos hilo para procesar mensajes del Health Checker
        thread = threading.Thread(target=self._escuchar_health_checker, daemon=True)
        thread.start()


    def _escuchar_health_checker(self) -> None:
        """Función que corre en un hilo daemon. Se queda bloqueado recibiendo
           mensajes JSON del Health Checker y llama a actualizar_servidor_activo()."""
        while True:
            try:
                estado = self.socket_health_checker.recv_json()
                # Ejemplo de estado recibido:
                #   { "servidorActivo": "principal", "ipPuerto": "localhost:5560" }
                print(f"{CYAN}Broker: mensaje Health Checker → {estado}{RESET}")
                self.actualizar_servidor_activo(estado)
            except zmq.ZMQError as e:
                print(f"{RED}Broker: ZMQError al leer Health Checker: {e}{RESET}")
                break
            except Exception as e:
                print(f"{RED}Broker: Error inesperado en hilo Health Checker: {e}{RESET}")
                break


    def actualizar_servidor_activo(self, estado: dict) -> None:
        """
        Cada vez que el Health Checker publique un JSON con el servidor activo,
        reconfiguramos el socket DEALER (backend) para conectarse al IP:PUERTO correcto.
        """
        ip_puerto = estado.get("ipPuerto")
        if not ip_puerto:
            return

        # Si ya estábamos conectados a esa misma dirección, no hacemos nada
        if ip_puerto == self.current_backend_ip:
            return

        # Si había una conexión anterior, la cerramos
        if self.current_backend_ip is not None:
            try:
                self.backend.close()
            except Exception:
                pass

            # Creamos un socket NUEVO cada vez que cambia el servidor
            self.backend = self.context.socket(zmq.DEALER)

        # Conectamos el nuevo DEALER al servidor activo
        self.backend.connect(f"tcp://{ip_puerto}")
        self.current_backend_ip = ip_puerto
        print(f"{YELLOW}Broker: conectado (backend DEALER) a → tcp://{ip_puerto}{RESET}")


    def start(self) -> None:
        """
        Una vez que el Health Checker haya enviado al menos un estado,
        podemos arrancar el proxy que interconecta frontend (ROUTER) y backend (DEALER).
        """
        # Si todavía no tenemos backend conectado, esperamos un poco
        if self.current_backend_ip is None:
            print(f"{YELLOW}Broker: esperando que Health Checker indique el servidor activo...{RESET}")
            # Un breve sleep para dar tiempo a que Health Checker publique
            # (en un sistema real, quizá usarías synchronización o poller en ambos sockets)
            import time; time.sleep(1)

        print(f"{GREEN}Broker: iniciando proxy ROUTER ⇄ DEALER{RESET}")
        try:
            zmq.proxy(self.frontend, self.backend)
        except zmq.ContextTerminated:
            # El contexto fue cerrado externamente
            pass
        except Exception as e:
            print(f"{RED}Broker: Proxy interrumpido: {e}{RESET}")
        finally:
            self.frontend.close()
            self.backend.close()
            self.context.term()


def main():
    broker = Broker()
    broker.crear_comunicacion()
    broker.start()


if __name__ == "__main__":
    main()