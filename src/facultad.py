import zmq
from datetime import datetime,date

class Facultad:
  
# Atributos de la clase

  nombre:str
  semestre:date
  ip_puerto_servidor:str
  context:zmq.Context
  socket_servidor_push:zmq.SyncSocket
  socket_servidor_sub:zmq.SyncSocket
  socket_programas:zmq.SyncSocket

# Metodos de la clase

  def __init__(this):
    this.nombre = input("Dijite el nombre de la facultad: ")
    this.semestre = datetime.strptime(input("Dijite el semestre en formato (mm-yyyy): "),"%m-%Y").date()
    this.ip_puerto_servidor = input("Dijite la ip y el puerto del servidor con el formato(ip:puerto): ")

  def crear_comunicacion(this) -> None:
    this.context = zmq.Context()
    this.socket_programas = this.context.socket(zmq.REP)
    this.socket_servidor_push = this.context.socket(zmq.PUSH) # Socket publica al servidor.
    this.socket_servidor_sub = this.context.socket(zmq.SUB) # Socket recibe respuesta del servidor. 
    this.socket_programas.bind("tcp://*:5555")
    this.socket_servidor_push.connect("tcp://localhost:5556")
    this.socket_servidor_sub.connect("tcp://localhost:5557")

  def recibir_peticion(this) -> dict:
    print("Recibiendo peticion...")
    peticion:dict = this.socket_programas.recv_json() # Recibe la peticion de algun programa academico
    print("Peticion recibida.\n")
    print("Peticion: ",peticion)
    this.socket_programas.send_string("y") # Responde al programa academico con (y,n) si o no
    peticion["nombreFacultad"] = this.nombre
    return peticion

  # TODO: Realizar implementacion
  def enviar_peticion_servidor(this,peticion_enviar:dict) -> bool:
    respuesta:str = str()
    print("Peticion enviada al servidor...")
    this.socket_servidor_push.send_json(peticion_enviar)
    respuesta = this.socket_servidor_sub.setsockopt_string(zmq.SUBSCRIBE,f"{peticion_enviar['nombrePrograma']}")
    print(f"Respuesta del servidor: {respuesta}")
    return True if respuesta.lower() == "y" else False

  def comunicar_peticiones(this) -> None:
    print("Escuchando peticiones de los programas academicos.")
    peticion_programa:dict = dict()
    while (peticion_programa := this.recibir_peticion()) != None:
      this.enviar_peticion_servidor(peticion_programa)

  def cerrar_comunicacion(this) -> None:
    this.socket_programas.close()
    this.socket_servidor_push.close()
    this.socket_servidor_sub.close()
    this.context.term()

# Seccion main del programa

if __name__ == "__main__":
  facultad:Facultad = Facultad()
  facultad.crear_comunicacion()
  facultad.comunicar_peticiones()
  facultad.cerrar_comunicacion()