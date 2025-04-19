import zmq

class ServidorCentral:
  context:zmq.Context
  socket_facultades_pub:zmq.SyncSocket
  socket_facultades_pull:zmq.SyncSocket

  # db: FileIO

  def __init__(this): pass

  def crear_comunicacion(this) -> None:
    this.context = zmq.Context()
    this.socket_facultades_pub = this.context.socket(zmq.PUB)
    this.socket_facultades_pull = this.context.socket(zmq.PULL)
    this.socket_facultades_pub.bind("tcp://localhost:5557")
    this.socket_facultades_pull.bind("tcp://*:5556")

  def escuchar_peticiones(this) -> None: 
    print("Escuchando peticiones de las facultades...")
    peticion:dict
    while True:
      peticion = this.socket_facultades_pull.recv_json()
      print(f"Facultad \"{peticion['nombreFacultad']}\" programa f{peticion['nombrePrograma']} realizo un peticion.")
      print(peticion)
      if peticion["numLaboratorios"] >= 1e2:
        print("Se ordenaron mas de 100 laboratorios, imposible.")
      this.socket_facultades_pub.send_string(f"{peticion['nombrePrograma']}: y")

  def cerrar_comunicacion(this) -> None:
    this.socket_facultades_pub.close()
    this.socket_facultades_sub.close()
    this.context.term()

if __name__ == "__main__":
  servidor_central:ServidorCentral = ServidorCentral()
  servidor_central.crear_comunicacion()
  servidor_central.escuchar_peticiones()
  servidor_central.cerrar_comunicacion()