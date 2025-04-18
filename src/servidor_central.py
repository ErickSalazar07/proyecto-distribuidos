import zmq

class ServidorCentral:
  context:zmq.Context
  socket_facultades_pub:zmq.SyncSocket
  socket_facultades_sub:zmq.SyncSocket

  # db: FileIO

  def __init__(this): pass

  def crear_comunicacion(this) -> None:
    this.socket_facultades_pub = this.context.socket(zmq.PUB)
    this.socket_facultades_sub = this.context.socket(zmq.SUB)
    this.socket_facultades_pub.bind("tcp://localhost:5556")
    this.socket_facultades_pub.bind("tcp://localhost:5556")

  def escuchar_peticiones(this) -> None: pass

  def cerrar_comunicacion(this) -> None:
    this.socket_facultades_pub.close()
    this.socket_facultades_sub.close()
    this.context.term()

if __name__ == "__main__":
  servidor_central:ServidorCentral = ServidorCentral()
  servidor_central.crear_comunicacion()
  servidor_central.escuchar_peticiones()
  servidor_central.cerrar_comunicacion()