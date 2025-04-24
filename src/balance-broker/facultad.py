import zmq
from datetime import datetime,date

class Facultad:
  
# Atributos de la clase

  nombre:str
  semestre:date
  ip_puerto_servidor:str
  context:zmq.Context
  socket_servidor:zmq.Socket
  socket_programas:zmq.Socket

# Metodos de la clase

  def __init__(self):
    self.nombre = input("Dijite el nombre de la facultad: ")
    self.semestre = datetime.strptime(input("Dijite el semestre en formato (mm-yyyy): "),"%m-%Y").date()
    self.ip_puerto_servidor = input("Dijite la ip y el puerto del servidor con el formato(ip:puerto): ")

  def crear_comunicacion(self) -> None:
    self.context = zmq.Context()
    self.socket_programas = self.context.socket(zmq.REP) # Socket sincrono. 
    self.socket_servidor = self.context.socket(zmq.DEALER) # Socket asincrono.
    self.socket_programas.bind("tcp://*:5555")
    self.socket_servidor.connect(f"tcp://{self.ip_puerto_servidor}")

  def recibir_peticion(self) -> dict:
    print("Recibiendo peticion...")
    peticion:dict = self.socket_programas.recv_json() # Recibe la peticion de algun programa academico
    print("Peticion recibida.\n")
    print("Peticion: ",peticion)
    self.socket_programas.send_string("y") # Responde al programa academico con (y,n) si o no
    peticion["nombreFacultad"] = self.nombre
    return peticion

  def enviar_peticion_servidor(self,peticion_enviar:dict) -> bool:
    print("Peticion enviada al servidor (comunicacion asincrona)...")
    self.socket_servidor.send_json(peticion_enviar)
    respuesta = self.socket_servidor.recv_json();
    print(f"Respuesta del servidor: {respuesta}")
    return respuesta.get("respuesta","").lower() == "y"

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