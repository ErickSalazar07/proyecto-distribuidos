import zmq
from datetime import datetime,date

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
    self.nombre = input("Dijite el nombre de la facultad: ")
    self.semestre = datetime.strptime(input("Dijite el semestre en formato (mm-yyyy): "),"%m-%Y").date()
    self.ip_puerto_servidor = input("Dijite la ip y el puerto del servidor con el formato(ip:puerto): ")
    self.puerto_escuchar_programas = input("Dijite el puerto por el cual escuchar a los programas(puerto > 5555): ")

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
  facultad.comunicar_peticiones()
  facultad.cerrar_comunicacion()