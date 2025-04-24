import zmq

# Colores para visualizar mejor la salida estandar.
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

class ServidorCentral:

  num_salones:int
  num_laboratorios:int
  context:zmq.Context
  socket_facultades:zmq.Socket

  def __init__(self):
    self.num_salones = int(input("Dijite el numero de salones: "))
    self.num_laboratorios = int(input("Dijite el numero de laboratorios: "))
    self.solicitudes_fallidas = []

  def crear_comunicacion(self) -> None:
    self.context = zmq.Context()
    self.socket_facultades = self.context.socket(zmq.ROUTER)
    self.socket_facultades.bind("tcp://*:5555")

  def escuchar_peticiones(self) -> None:
    print(f"{CYAN}Escuchando peticiones de las facultades en el puerto: 5555...{RESET}")
    while True:
      identity, raw_msg = self.socket_facultades.recv_multipart()
      peticion = zmq.utils.jsonapi.loads(raw_msg)

      if isinstance(peticion, dict) and 'nombreFacultad' in peticion and 'nombrePrograma' in peticion:
        print(f"{YELLOW}Petición de {peticion['nombreFacultad']} - Programa {peticion['nombrePrograma']}{RESET}")
      else:
        print(f"{RED}Petición recibida malformada o incompleta: {peticion}{RESET}")
        continue  
      print(f"{MAGENTA}Contenido: {peticion}{RESET}")

      num_salones_pedido = peticion.get("numSalones", 0)
      num_laboratorios_pedido = peticion.get("numLaboratorios", 0)

      reserva_exitosa = False
      if self.num_salones >= num_salones_pedido and self.num_laboratorios >= num_laboratorios_pedido:
        self.num_salones -= num_salones_pedido
        self.num_laboratorios -= num_laboratorios_pedido
        reserva_exitosa = True
      else:
        self.solicitudes_fallidas.append(peticion)
        print(f"{RED}Solicitud no atendida guardada en lista de peticiones fallidas.{RESET}")

      respuesta = {
        "respuesta": "y" if reserva_exitosa else "n",
        "salonesDisponibles": self.num_salones,
        "laboratoriosDisponibles": self.num_laboratorios
      }

      self.socket_facultades.send_multipart([
        identity,
        zmq.utils.jsonapi.dumps(respuesta)
      ])

      if reserva_exitosa:
        # Esperar confirmación de aceptación de la facultad
        _, raw_confirmacion = self.socket_facultades.recv_multipart()
        confirmacion = zmq.utils.jsonapi.loads(raw_confirmacion)
        if confirmacion.get("confirmacion") == "aceptada":
          print(f"{GREEN}La facultad confirmó la reserva.{RESET}")
        else:
          print(f"{RED}La facultad rechazó la reserva.{RESET}") # Devolvemos recursos asignados
          self.num_salones += num_salones_pedido
          self.num_laboratorios += num_laboratorios_pedido


  def cerrar_comunicacion(self) -> None:
    self.socket_facultades.close();
    self.context.term()

if __name__ == "__main__":
  servidor_central = ServidorCentral()
  servidor_central.crear_comunicacion()
  try:
    servidor_central.escuchar_peticiones()
  except KeyboardInterrupt:
    print(f"\n{RED}Servidor detenido manualmente.{RESET}")
    print(f"{YELLOW}Solicitudes fallidas almacenadas:{RESET}")
    for idx, solicitud in enumerate(servidor_central.solicitudes_fallidas, 1):
      print(f"{idx}. {solicitud}")
  finally:
    servidor_central.cerrar_comunicacion()
