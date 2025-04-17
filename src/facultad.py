import zmq

class Facultad:
  
# Atributos de la clase

  nombre:str
  semestre:str
  ip_puerto_servidor:str
  context:zmq.Context
  socket:zmq.SyncSocket

# Metodos de la clase

  def __init__(this):
    this.nombre = input("Dijite el nombre de la facultad: ")
    this.semestre = input("Dijite el semestre: ")
    this.ip_puerto_servidor = input("Dijite la ip y el puerto del servidor con el formato(ip:puerto): ")

  def crear_bind(this) -> None:
    this.context = zmq.Context()
    this.socket = this.context.socket(zmq.REP)
    this.socket.bind("tcp://*:5555")

  def recibir_mensajes(this) -> None:
    print("Esperando a recibir mensajes...")
    mensaje:str = this.socket.recv_string()
    print("Mensaje recibido.\n")
    print(f"El mensaje que se recibio es:\n{mensaje}")

  def cerrar_bind(this) -> None:
    this.socket.close()
    this.context.term()

# Seccion main del programa

if __name__ == "__main__":
  facultad:Facultad = Facultad()
  facultad.crear_bind()
  facultad.recibir_mensajes()
  facultad.cerrar_bind()