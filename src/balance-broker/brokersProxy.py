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


    def __init__(self):
        print("init")
        # Dirección (IP:PUERTO) del Health Checker
        self.ip_puerto_health_checker = "localhost:5553"
        # Puerto en el que el broker recibirá peticiones de las Facultades
        # (debe coincidir con lo que ellas usan en "-ip-p-s")
        self.puerto_escuchar_facultad = "5513"
        self.puerto_escuchar_workers = "5555"

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

        # 1) FRONTEND: ROUTER para recibir de las Facultades
        self.frontend = self.context.socket(zmq.ROUTER)
        # Bind al puerto en el que las Facultades harán REQ → BROKER
        self.frontend.bind(f"tcp://*:{self.puerto_escuchar_facultad}")
        print(f"{GREEN}Broker: frontend ROUTER escuchando en tcp://*:{self.puerto_escuchar_facultad}{RESET}")

        # 2) BACKEND: ROUTER para recivir a los workers
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.bind(f"tcp://*:{self.puerto_escuchar_workers}")
        print(f"{GREEN}Broker: backend ROUTER escuchando en tcp://*:{self.puerto_escuchar_workers}{RESET}")

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
            self.socket_health_checker.recv_string()
            print("Me dijeron que cambio el servidor")

            self.workers_list = []
            self.available_workers = 0

            '''
            try:
                self.socket_health_checker.send_json({"estadoServidor":True})
                estado = self.socket_health_checker.recv_json()
                # Ejemplo de estado recibido:
                #   { "servidorActivo": "principal", "ipPuerto": "localhost:5560" }
                print(f"{CYAN}Broker: mensaje Health Checker → {estado}{RESET}")
                servidor_Activo = self.actualizar_servidor_activo(estado, servidor_actual=servidor_Activo)
                time.sleep(1) # Esperar 1 segundos
            except zmq.ZMQError as e:
                print(f"{RED}Broker: ZMQError al leer Health Checker: {e}{RESET}")
                break
            except Exception as e:
                print(f"{RED}Broker: Error inesperado en hilo Health Checker: {e}{RESET}")
                break
                '''
    '''
    def actualizar_servidor_activo(self, estado: dict, servidor_actual) -> str:

        if(servidor_actual == estado.get("servidorActivo")): # Si el servidor activo del broker es igual al del healthcheker
            return # No cambia nada
        # En caso de haber un cambio en el servidor activo 
        self.workers_list = []
        self.available_workers = 0
        servidor_actual = estado.get("servidorActivo")



        ip_puerto = estado.get("ipPuerto")
        if not ip_puerto or ip_puerto == self.current_backend_ip:
            return

        # Cerramos socket anterior si existía
        if self.current_backend_ip is not None:
            try:
                self.backend.close()
            except Exception as e:
                print(f"Error cerrando backend anterior: {e}")

            # Limpiar lista de workers
            self.available_workers = 0
            self.workers_list.clear()

        # 🔧 Aquí el cambio clave
        self.backend = self.context.socket(zmq.ROUTER)
        self.backend.connect(f"tcp://{ip_puerto}")
        self.current_backend_ip = ip_puerto

        print(f"{YELLOW}Broker: conectado (backend ROUTER) a → tcp://{ip_puerto}{RESET}")
        '''

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

                        self.available_workers += 1
                        self.workers_list.append(worker_id)
                        print(f"{GREEN}Worker {worker_id} registrado como disponible{RESET}")

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
