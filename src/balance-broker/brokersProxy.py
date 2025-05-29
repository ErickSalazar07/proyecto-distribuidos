# brokersProxy.py

import sys
import threading
import zmq
import time

# Colores para output en consola
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class Broker:
    available_workers:int
    workers_list:list
    context_cambio:zmq.Context

    def __init__(self):
        print("init")
        # Dirección (IP:PUERTO) del Health Checker
        self.ip_puerto_health_checker = "localhost:5553"
        # Puerto en el que el broker recibirá peticiones de las Facultades
        # (debe coincidir con lo que ellas usan en "-ip-p-s")
        self.puerto_escuchar_facultad = "5513"

        # Contexto y sockets de ZeroMQ
        self.context = None
        self.context_cambio = None
        self.frontend = None    # ROUTER  ← Facultades
        self.backend = None     # DEALER  → Servidores (Central o Respaldo)
        self.socket_health_checker = None  # SUB   ← Health Checker

        # Para guardar la dirección (IP:PUERTO) del servidor actualmente activo
        self.current_backend_ip = None

        self.available_workers = 0
        self.workers_list = []


    def crear_comunicacion(self) -> None:
        """Inicializa el contexto, el ROUTER (frontend), el SUB (health)
           y arranca el hilo que escucha actualizaciones del Health Checker."""
        self.context = zmq.Context()
        self.context_cambio = zmq.Context()

        # 1) FRONTEND: ROUTER para recibir de las Facultades
        self.frontend = self.context.socket(zmq.ROUTER)
        # Bind al puerto en el que las Facultades harán REQ → BROKER
        self.frontend.bind(f"tcp://*:{self.puerto_escuchar_facultad}")
        print(f"{GREEN}Broker: frontend ROUTER escuchando en tcp://*:{self.puerto_escuchar_facultad}{RESET}")

        # 2) BACKEND: DEALER para reenviar a los Servidores (inicialmente no conectado)
        #    Esperaremos a que llegue el primer estado del Health Checker para conectar.
        self.backend = self.context.socket(zmq.ROUTER)
        # (No hacemos bind ni connect aquí; se hará en actualizar_servidor_activo())

        # 3) HEALTH_CHECKER: SUB para recibir actualizaciones de qué servidor está activo
        self.socket_health_checker = self.context.socket(zmq.REQ)
        self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")
        print(f"{GREEN}Broker: REQ conectado a Health Checker en tcp://{self.ip_puerto_health_checker}{RESET}")

        # 4) Arrancamos hilo para procesar mensajes del Health Checker
        thread = threading.Thread(target=self._escuchar_health_checker, daemon=True)
        thread.start()


    def _escuchar_health_checker(self) -> None:
        """Función que corre en un hilo daemon. Se queda bloqueado recibiendo
           mensajes JSON del Health Checker y llama a actualizar_servidor_activo()."""
        while True:
            try:
                self.socket_health_checker.send_json({"estadoServidor":True})
                estado = self.socket_health_checker.recv_json()
                # Ejemplo de estado recibido:
                #   { "servidorActivo": "principal", "ipPuerto": "localhost:5560" }
                print(f"{CYAN}Broker: mensaje Health Checker → {estado}{RESET}")
                self.actualizar_servidor_activo(estado)
                time.sleep(1) # Esperar 1 segundos
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
            context_cambio = zmq.Context()
            self.backend = context_cambio.socket(zmq.ROUTER)
            context_cambio.term()

        # Conectamos el nuevo DEALER al servidor activo
        self.backend.bind(f"tcp://{ip_puerto}")
        self.current_backend_ip = ip_puerto
        print(f"{YELLOW}Broker: conectado (backend DEALER) a → tcp://{ip_puerto}{RESET}")

    def start(self) -> None:
        poller = zmq.Poller()
        poller.register(self.backend, zmq.POLLIN)
        poller.register(self.frontend, zmq.POLLIN)

        try:
            if self.current_backend_ip is None:
                print(f"{YELLOW}Broker: esperando que Health Checker indique el servidor activo...{RESET}")
                time.sleep(1)

            while True:
                socks = dict(poller.poll())

                # Manejar mensajes del backend (workers)
                if self.backend in socks and socks[self.backend] == zmq.POLLIN:
                    message = self.backend.recv_multipart()
                    worker_id = message[0]

                    # Caso: worker se registra con READY
                    if len(message) == 3 and message[2] == b'READY':
                        self.available_workers += 1
                        self.workers_list.append(worker_id)
                        print(f"{GREEN}Worker {worker_id} registrado como disponible{RESET}")
                        continue

                    # Caso: respuesta del worker a un cliente
                    if len(message) >= 5:
                        client_id = message[2]
                        reply = message[4]
                        self.frontend.send_multipart([client_id, b"", reply])
                        print(f"{GREEN}Respuesta enviada al cliente {client_id}{RESET}")

                # Manejar mensajes del frontend (facultades/clients)
                if self.frontend in socks and socks[self.frontend] == zmq.POLLIN:
                    if self.available_workers > 0:
                        client_msg = self.frontend.recv_multipart()
                        client_id = client_msg[0]
                        request = client_msg[2]
                        print(f"{CYAN}Petición recibida de cliente {client_id}{RESET}")

                        # Obtener un worker disponible
                        worker_id = self.workers_list.pop(0)
                        self.available_workers -= 1

                        # Enviar trabajo al worker: [worker_id][empty][client_id][empty][request]
                        self.backend.send_multipart([worker_id, b"", client_id, b"", request])
                        print(f"{YELLOW}Petición enviada al worker {worker_id}{RESET}")
                    else:
                        print(f"{RED}No hay workers disponibles actualmente. Cliente en espera.{RESET}")

        except Exception as e:
            print(f"{RED}Error en el broker: {e}{RESET}")
        finally:
            self.frontend.close()
            self.backend.close()
            self.context.term()

def main():
    print("Broker")
    broker = Broker()
    print("Crear comunicacion")
    broker.crear_comunicacion()
    print("Start")
    broker.start()

if __name__ == "__main__":
    main()