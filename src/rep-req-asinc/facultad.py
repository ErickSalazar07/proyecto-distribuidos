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
  ip_puerto_servidor:str
  puerto_escuchar_programas:str
  context:zmq.Context
  socket_servidor:zmq.Socket
  socket_programas:zmq.Socket

# Metodos de la clase

  def __init__(self):

    if len(sys.argv) != 9:
      print(f"Error: El numero de argumentos no es valido. Recuerde.\n\n")
      self.error_args()
      sys.exit(-1)

    self.nombre = ""
    self.semestre = None
    self.ip_puerto_servidor = ""
    self.puerto_escuchar_programas = ""

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
    self.context = zmq.Context()
    self.socket_programas = self.context.socket(zmq.REP) # Socket sincrono. 
    self.socket_servidor = self.context.socket(zmq.DEALER) # Socket asincrono.
    self.socket_programas.bind(f"tcp://*:{self.puerto_escuchar_programas}")
    self.socket_servidor.connect(f"tcp://{self.ip_puerto_servidor}")

  def recibir_peticion(self) -> dict:
    print(f"{CYAN}Recibiendo peticion en el puerto: {self.puerto_escuchar_programas}...{RESET}")
    peticion:dict = self.socket_programas.recv_json() # Recibe la peticion de algun programa academico
    print(f"{GREEN}Peticion recibida.\n{RESET}")
    print(f"{YELLOW}Peticion: {peticion}{RESET}")
    self.socket_programas.send_string("y") # Responde al programa academico con (y,n) si o no
    peticion["nombreFacultad"] = self.nombre
    return peticion

  def enviar_peticion_servidor(self, peticion_enviar: dict) -> bool:
    print(f"{MAGENTA}Peticion enviada al servidor (comunicacion asincrona)...{RESET}")
    self.socket_servidor.send_json(peticion_enviar)
    respuesta = self.socket_servidor.recv_json()
    print(f"{BLUE}Respuesta del servidor: {respuesta}{RESET}")

    if respuesta.get("respuesta", "").lower() == "y":
      # Por ahora se acepta automáticamente
      print(f"{GREEN}Reserva aceptada por la facultad.{RESET}")
      confirmacion = {"confirmacion": "aceptada"}
    else:
      print(f"{RED}La reserva no fue aprobada por el servidor.{RESET}")
      confirmacion = {"confirmacion": "rechazada"}

    self.socket_servidor.send_json(confirmacion)
    return respuesta.get("respuesta", "").lower() == "y"


  def comunicar_peticiones(self) -> None:
    print("Escuchando peticiones de los programas academicos.")
    while True:
      peticion_programa = self.recibir_peticion()
      self.enviar_peticion_servidor(peticion_programa)

  def cerrar_comunicacion(self) -> None:
    self.socket_programas.close()
    self.socket_servidor.close()
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
