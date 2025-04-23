import zmq

class ServidorCentral:

  num_salones:int
  num_laboratorios:int
  context:zmq.Context
  socket_facultades:zmq.Socket

  def __init__(self):
    self.num_salones = int(input("Dijite el numero de salones: "))
    self.num_laboratorios = int(input("Dijite el numero de laboratorios: "))

  def crear_comunicacion(self) -> None:
    self.context = zmq.Context()
    self.socket_facultades = self.context.socket(zmq.ROUTER)
    self.socket_facultades.bind("tcp://*:5556")

  def escuchar_peticiones(self) -> None:
    print("Escuchando peticiones de las facultades...")
    while True:
      identity, raw_msg = self.socket_facultades.recv_multipart()
      peticion = zmq.utils.jsonapi.loads(raw_msg)

      print(f"Petición de {peticion['nombreFacultad']} - Programa {peticion['nombrePrograma']}")
      print(peticion)

      num_salones_pedido = peticion.get("numSalones", 0)
      num_laboratorios_pedido = peticion.get("numLaboratorios", 0)

      reserva_exitosa = False
      if self.num_salones >= num_salones_pedido and self.num_laboratorios >= num_laboratorios_pedido:
        self.num_salones -= num_salones_pedido
        self.num_laboratorios -= num_laboratorios_pedido
        reserva_exitosa = True

      respuesta = {
        "respuesta": "y" if reserva_exitosa else "n",
        "salonesDisponibles": self.num_salones,
        "laboratoriosDisponibles": self.num_laboratorios
      }

      self.socket_facultades.send_multipart([
        identity,
        zmq.utils.jsonapi.dumps(respuesta)
      ])

  def cerrar_comunicacion(self) -> None:
    self.socket_facultades_pub.close()
    self.socket_facultades_sub.close()
    self.context.term()

if __name__ == "__main__":
  servidor_central:ServidorCentral = ServidorCentral()
  servidor_central.crear_comunicacion()
  servidor_central.escuchar_peticiones()
  servidor_central.cerrar_comunicacion()