# broker_proxy.py

import zmq

class Broker:
  
# Atributos de la clase

    ip_puerto_health_checker :str
    socket_health_checker:zmq.Socket
    ip_puerto_servidor :str
    socket_broker:zmq.Socket
    puerto_escuchar_facultad:str
    socket_facultades = None



    def __init__(self):
        #self.ip_puerto_health_checker = "10.43.96.80:5553"
        self.ip_puerto_health_checker = "localhost:5553"
        self.socket_health_checker = None
        self.ip_puerto_servidor = ""
        self.socket_broker = None


    def actualizar_servidor_activo(self,estado): #CREO QUE ESTO IRIA EN EL BROCKER MAS QUE EN EL CLIENTE PREGUNTAR A LAS 8
        ip_puerto = estado["ipPuerto"]
        if hasattr(self,"ip_puerto_servidor") and self.ip_puerto_servidor == ip_puerto:
          return
    
        try:
          if hasattr(self,"socket_servidor"):
            self.socket_servidor.close()
          
          self.socket_servidor = self.context.socket(zmq.DEALER)
          self.socket_servidor.connect(f"tcp://{ip_puerto}")
          self.ip_puerto_servidor = ip_puerto
          print(f"{GREEN}✅ Conectado al servidor {estado['servidor_activo']} ({ip_puerto}){RESET}")
        except Exception as e:
          print(f"{RED}Error al conectar al servidor {ip_puerto}: {e}{RESET}")
    
    def iniciar_escucha_health_checker(self):
        import threading
        def escuchar_actualizaciones():
          while True:
            try:
              estado = self.socket_health_checker.recv_json()
              print(f"{CYAN}Actualizacion recibida del health_checker: {estado}{RESET}")
              self.actualizar_servidor_activo(estado)
            except Exception as e:
              print(f"{RED}Error al recibir actualizacion: {e}{RESET}")
        threading.Thread(target=escuchar_actualizaciones,daemon=True).start()
    
    def crear_comunicacion(self) -> None:
        # Se crea el context(clase para manejar instancias de los diferentes sockets)
        self.context = zmq.Context()
    
    
        # Se inicializa el canal para comunicarse con facultades
    
        frontend = context.socket(zmq.ROUTER)
        frontend.bind(f"tcp://{self.puerto_escuchar_facultad}")  # broker frontend
    
        # Se inicializa el canal para comunicarse con el health_checker
        self.socket_health_checker = self.context.socket(zmq.SUB)
        self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")
        self.socket_health_checker.setsockopt_string(zmq.SUBSCRIBE,"")
    
        # Se crea un canal y se inicializa en el ip y puerto que se ingresan por comando
        self.socket_broker = self.context.socket(zmq.ROUTER)
        self.socket_broker.connect(f"tcp://{self.ip_puerto_servidor}")
        self.iniciar_escucha_health_checker()
    
        # Inicia hilo para escuchar actualizaciones
    
    def recibir_peticion(self) -> dict:
        print(f"{CYAN}Recibiendo peticion en el puerto: {self.puerto_escuchar_facultad}...{RESET}")
        peticion:dict = self.socket_facultades.recv_json() # Recibe la peticion de algun programa academico
        print(f"{GREEN}Peticion recibida.\n{RESET}")
        print(f"{YELLOW}Peticion: {peticion}{RESET}")
        self.socket_facultades.send_string("y") # Responde al programa academico con (y,n) si o no
        return peticion
    
    def enviar_peticion_servidor(self, peticion_enviar: dict) -> bool:
        if not hasattr(self, 'socket_servidor') or self.socket_servidor.closed:
            print(f"{RED}Error: No hay conexión activa con el servidor{RESET}")
            return False
        print(f"{MAGENTA}Enviando petición al servidor...{RESET}")
        try:
            self.socket_servidor.send_json(peticion_enviar)
            if self.socket_servidor.poll(timeout=5000):  # Timeout de 5 segundos
                respuesta = self.socket_servidor.recv_json()
                print(f"{BLUE}Respuesta del servidor: {respuesta}{RESET}")
                return respuesta.get("respuesta", "").lower() == "y"
            else:
                print(f"{RED}Timeout: No se recibió respuesta del servidor{RESET}")
                return False
        except Exception as e:
            print(f"{RED}Error al enviar petición al servidor: {e}{RESET}")
            return False
        

    def comunicar_peticiones(self) -> None:
        print("Escuchando peticiones de los programas academicos.")
        while True:
           peticion_programa = self.recibir_peticion()
           self.enviar_peticion_servidor(peticion_programa)

    def cerrar_comunicacion(self) -> None:
        self.socket_servidor.close()
        self.socket_broker.close()
        self.socket_health_checker.close()
        self.context.term()

def main():

    broker:Broker = Broker()
    broker.crear_comunicacion()

    context = zmq.Context()

    try:
        broker.comunicar_peticiones()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}broker detenido manualmente.{RESET}")
    finally:
        broker.cerrar_comunicacion()


if __name__ == "__main__":
    main()
