from datetime import datetime,date
import zmq
import sys

# Colores para visualizar mejor la salida estandar.
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class Facultad:
  
# Atributos de la clase

  nombre:str
  semestre:date
  ip_puerto_broker:str
  puerto_escuchar_programas:str
  context:zmq.Context
  socket_broker:zmq.Socket
  socket_programas:zmq.Socket
  socket_health_checker:zmq.Socket

# Metodos de la clase

  def __init__(self):

    if len(sys.argv) != 9:
      print(f"Error: El numero de argumentos no es valido. Recuerde.\n\n")
      self.error_args()
      sys.exit(-1)

    self.nombre = ""
    self.semestre = None
    self.ip_puerto_servidor = ""
    #self.ip_puerto_health_checker = "10.43.96.80:5553"
    self.ip_puerto_health_checker = "localhost:5553"
    self.puerto_escuchar_programas = ""
    self.context = None
    self.socket_broker = None
    self.socket_programas = None
    self.socket_health_checker = None

    for i in range(1,len(sys.argv)):
      if sys.argv[i] == "-n":
        self.nombre = sys.argv[i+1]
      elif sys.argv[i] == "-s":
        self.semestre = datetime.strptime(sys.argv[i+1],"%m-%Y").date()
      elif sys.argv[i] == "-ip-p-s":
        self.ip_puerto_servidor = sys.argv[i+1]
      elif sys.argv[i] == "-puerto-escuchar":
        self.puerto_escuchar_programas = sys.argv[i+1]

    if not self.campos_validos():
      print(f"Error: Los campos no son validos. Recuerde.\n\n")
      self.error_args()
      sys.exit(-2)

    print("Informacion de la facultad:\n")
    print(self)
  
  def guardar_peticion_archivo(self,peticion:dict):
    nombre_archivo = f"{peticion['semestre']}.txt"
    peticion_txt = f"Programa Academico: {peticion['nombrePrograma']}, Salones: {peticion['numSalones']}, Laboratorios: {peticion['numLaboratorios']}\n"

    try:
      with open(nombre_archivo,"a") as archivo:
        archivo.write(peticion_txt)
      print(f"Petición guardada en {nombre_archivo}")
    except Exception as e:
      print(f"Error al guardar la petición: {e}")

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

  def error_args(self):
    print(f"Debe ingresar las banderas/opciones y sus argumentos correspondientes.\n")
    print(f"-n \"nombre_facultad\": Es el nombre de la facultad")
    print(f"-s \"mm-yyyy\": Es el semestre, el cual debe seguir el formato propuesto")
    print(f"-ip-p-s \"ip_servidor:puerto_servidor\": Es la ip y el puerto del servidor separados por ':'")
    print(f"-puerto-escuchar \"puerto_escuchar_programas\": Es el puerto por el cual la facultad va a escuchar las peticiones de los programas")

  def campos_validos(self) -> bool:
    return self.nombre != "" and self.semestre != None and self.ip_puerto_servidor != "" \
    and self.puerto_escuchar_programas != ""

  def __str__(self) -> str:
    return\
      f"Nombre: {self.nombre}\n"\
    + f"Semestre: {self.semestre}\n"\
    + f"Ip servidor: Puerto servidor => {self.ip_puerto_servidor}\n"\
    + f"Puerto escuchar peticions programas: {self.puerto_escuchar_programas}\n\n"

  def crear_comunicacion(self) -> None:
    # Se crea el context(clase para manejar instancias de los diferentes sockets)
    self.context = zmq.Context()
    
    # Se inicializa el canal para la comunicacion con programas
    self.socket_programas = self.context.socket(zmq.REP) # Socket sincrono. 
    self.socket_programas.bind(f"tcp://*:{self.puerto_escuchar_programas}")
    
    # Se inicializa el canal para comunicarse con el health_checker
    self.socket_health_checker = self.context.socket(zmq.SUB)
    self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")
    self.socket_health_checker.setsockopt_string(zmq.SUBSCRIBE,"")

    # Se crea un canal y se inicializa en el ip y puerto que se ingresan por comando
    self.socket_broker = self.context.socket(zmq.REQ)
    self.socket_broker.connect(f"tcp://{self.ip_puerto_broker}")
    self.iniciar_escucha_health_checker()

    # Inicia hilo para escuchar actualizaciones

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

  def recibir_peticion(self) -> dict:
    print(f"{CYAN}Recibiendo peticion en el puerto: {self.puerto_escuchar_programas}...{RESET}")
    peticion:dict = self.socket_programas.recv_json() # Recibe la peticion de algun programa academico
    print(f"{GREEN}Peticion recibida.\n{RESET}")
    print(f"{YELLOW}Peticion: {peticion}{RESET}")
    self.socket_programas.send_string("y") # Responde al programa academico con (y,n) si o no
    self.guardar_peticion_archivo(peticion)
    peticion["nombreFacultad"] = self.nombre
    return peticion

  # aca esta la peticion del broker ESTO NO SE CAMBIAAA DE ACAAAAAAAAAAAAA
  def enviar_peticion_broker(self, peticion_enviar: dict) -> bool:
    if not hasattr(self, 'socket_broker') or self.socket_broker.closed:
        print(f"{RED}Error: No hay conexión activa con el broker{RESET}")
        return False
    print(f"{MAGENTA}Enviando petición al broker...{RESET}")
    try:
        self.socket_broker.send_json(peticion_enviar)
        if self.socket_broker.poll(timeout=5000):  # Timeout de 5 segundos
            respuesta = self.socket_broker.recv_json()
            print(f"{BLUE}Respuesta del broker: {respuesta}{RESET}")
            return respuesta.get("respuesta", "").lower() == "y"
        else:
            print(f"{RED}Timeout: No se recibió respuesta del broker{RESET}")
            return False
    except Exception as e:
        print(f"{RED}Error al enviar petición al broker: {e}{RESET}")
        return False


  def comunicar_peticiones(self) -> None:
    print("Escuchando peticiones de los programas academicos.")
    while True:
      peticion_programa = self.recibir_peticion()
      self.enviar_peticion_servidor(peticion_programa)

  def cerrar_comunicacion(self) -> None:
    self.socket_programas.close()
    self.socket_broker.close()
    self.socket_health_checker.close()
    self.context.term()

# Seccion main del programa

if __name__ == "__main__":
  facultad:Facultad = Facultad()
  facultad.crear_comunicacion()
  try:
    facultad.comunicar_peticiones()
  except KeyboardInterrupt:
    print(f"\n{YELLOW}Facultad detenido manualmente.{RESET}")
  finally:
    facultad.cerrar_comunicacion()
