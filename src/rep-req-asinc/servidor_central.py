import zmq
import sys
import time
import threading

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
  solicitudes_fallidas:list
  context:zmq.Context
  socket_facultades:zmq.Socket
  socket_health_checker:zmq.Socket
  ip_puerto_health_checker:str
  hilo_health:threading.Thread

  def __init__(self):

    self.num_salones = 0
    self.num_laboratorios = 0
    self.solicitudes_fallidas = list()
    self.context = None
    self.socket_facultades = None
    self.socket_health_checker = None
    self.hilo_health = None
    self.ip_puerto_health_checker = "localhost:5550"
    # self.ip_puerto_health_checker = "10.43.96.80:5550"
    
    self.cargar_db("db.txt")

    print("Informacion del servidor.\n\n")
    print(self)
    

  def cargar_db(self,nombre_db:str):

    try:
      with open(nombre_db,"r") as db:
        for linea in db:
          if linea.startswith("Salones:"):
            self.num_salones = int(linea.split(":")[1].strip())
          elif linea.startswith("Laboratorios:"):
            self.num_laboratorios = int(linea.split(":")[1].strip())
    except Exception as e:
      print(f"{RED}Hubo un error leyendo el archivo: Error: {e}{RESET}")

  def __str__(self) -> str:
    return\
    f"Numero salones: {self.num_salones}\n"\
    f"Numero laboratorios: {self.num_laboratorios}\n\n"

  def crear_comunicacion(self) -> None:
    self.context = zmq.Context()
    
    # Comunicacion con facultades
    self.socket_facultades = self.context.socket(zmq.ROUTER)
    self.socket_facultades.bind("tcp://*:5555")
    
    # Comunicacion con health checker
    self.socket_health_checker = self.context.socket(zmq.PUSH)
    self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")

    # Crear hilo para comunicacion con health checker
    self.hilo_health = threading.Thread(target=self.comunicar_estado_health_checker, daemon=True)
    self.hilo_health.start()


  def comunicar_estado_health_checker(self):
    while True:
      mensaje = {"estado": "ok"}

      try:
        self.socket_health_checker.send_json(mensaje)
        print(f"{BLUE}[Health Check] Estado enviado al health_checker.{RESET}")
      except Exception as e:
        print(f"{RED}[Health Check] Error al enviar estado: {e}{RESET}")
      time.sleep(2) # Espera 5 segundo a enviar el siguiente ping o estado

  def reservar_peticion(self,peticion:dict) -> dict:
    num_salones = peticion.get("numSalones",0)
    num_laboratorios = peticion.get("numLaboratorios",0)

    if self.num_salones >= num_salones and self.num_laboratorios >= num_laboratorios:
      self.num_salones -= num_salones
      self.num_laboratorios -= num_laboratorios
      return {"estatus": True, "laboratoriosDisponibles": True}
    elif self.num_salones >= num_salones:
      self.num_salones -= num_salones
      return {"estatus": True, "laboratoriosDisponibles": False}

    self.solicitudes_fallidas.append(peticion)
    print(f"{RED}Solicitud no atendida guardada en lista de peticiones fallidas.{RESET}")
    return {"estatus": False, "laboratoriosDisponibles": False}

  def escuchar_peticiones(self) -> None:
    print(f"{CYAN}Escuchando peticiones de las facultades en el puerto: 5555...{RESET}")
    
    with open("db.txt","a") as db:
      while True:
        identity, raw_msg = self.socket_facultades.recv_multipart()
        peticion = zmq.utils.jsonapi.loads(raw_msg)

        if isinstance(peticion, dict) and 'nombreFacultad' in peticion and 'nombrePrograma' in peticion:
          print(f"{YELLOW}Petición de {peticion['nombreFacultad']} - Programa {peticion['nombrePrograma']}{RESET}")
        else:
          print(f"{RED}Petición recibida malformada o incompleta: {peticion}{RESET}")
          continue  
        print(f"{MAGENTA}Contenido: {peticion}{RESET}")

        reserva_exitosa:bool = self.reservar_peticion(peticion)

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
            self.guardar_peticion_db(peticion,db)
          else:
            print(f"{RED}La facultad rechazó la reserva.{RESET}") # Devolvemos recursos asignados
            self.num_salones += peticion.get("numSalones",0)
            self.num_laboratorios += peticion.get("numLaboratorios",0)

  def cerrar_comunicacion(self) -> None:
    self.socket_facultades.close()
    self.socket_health_checker.close()
    self.context.term()

  def guardar_peticion_db(self,peticion,db):
    peticion_txt = f"Nombre Facultad: {peticion['nombreFacultad']}, Nombre Programa: {peticion['nombrePrograma']}," \
      + f"Num Salones: {peticion['numSalones']}, Num Laboratorios: {peticion['numLaboratorios']}\n"
    db.write(peticion_txt)

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
