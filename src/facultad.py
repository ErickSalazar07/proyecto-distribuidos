import zmq
from datetime import datetime,date

class Facultad:
  
# Atributos de la clase

  nombre:str
  semestre:date
  ip_puerto_servidor:str
  context:zmq.Context
  socket_servidor_pub:zmq.SyncSocket
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
    #this.socket_servidor_pub = this.context.socket(zmq.PUB) # Socket publica al servidor.
    #this.socket_servidor_sub = this.context.socket(zmq.SUB) # Socket recibe respuesta del servidor. 
    this.socket_programas.bind("tcp://*:5555")
    #this.socket_servidor_pub.connect(f"tcp://{this.ip_puerto_servidor}")
    #this.socket_servidor_sub.connect(f"tcp://{this.ip_puerto_servidor}")
    #this.socket_servidor_sub.setsockopt(zmq.SUBSCRIBE,b"") # Se suscribe a todas las noticias.

  def comunicar_peticiones(this) -> bool:
    print("Escuchando peticiones de los programas academicos...",end="")
    peticion:dict = this.socket_programas.recv_json()
    print("\n\nPeticion recibida.\n")
    #this.socket_servidor_pub.send_json(peticion)
    #respuesta:str = this.socket_servidor_sub.recv_string()
    #if(respuesta.strip().lower() == "end"): return False
    #print(f"Asignacion: {'Exitosa' if respuesta.lower() == 'si' else 'Fallida'}.\n")
    print("Peticion:\n",peticion)
    this.socket_programas.send_string("y")
    return True

  def cerrar_comunicacion(this) -> None:
    this.socket_programas.close()
    this.socket_servidor_pub.close()
    this.socket_servidor_sub.close()
    this.context.term()

# Seccion main del programa

if __name__ == "__main__":
  facultad:Facultad = Facultad()
  facultad.crear_comunicacion()
  while facultad.comunicar_peticiones(): pass
  facultad.cerrar_comunicacion()