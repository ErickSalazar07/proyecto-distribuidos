import zmq
import sys
import time
import threading
import json

# Colores para visualizar mejor la salida estandar.
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

CANT_WORKERS = 10
HEALTH_CHECKER_ADDR = "tcp://localhost:5516"

class ServidorCentral:

  num_salones:int
  num_laboratorios:int
  solicitudes_fallidas:list
  peticiones:list
  context:zmq.Context
  context_workers:zmq.Context
  url_worker:str
  workers:list

  def __init__(self):

    self.db = None
    self.num_salones = 380
    self.num_laboratorios = 60
    self.solicitudes_fallidas = list()
    self.context = None
    self.context_workers = None
    self.url_worker = "tcp://localhost:5555"
    self.workers = []
    # self.ip_puerto_health_checker = "10.43.96.80:5550"
    
    self.cargar_db("db.txt")
    print("Informacion del servidor.\n\n")
    print(self)
    self.db = open("db.txt","+w")
    

  def cargar_db(self,nombre_db:str):
    try:
      with open(nombre_db,"r") as db:
        for linea in db:
          if linea.startswith("Salones:"):
            self.num_salones = int(linea.split(":")[1].strip())
          elif linea.startswith("Laboratorios:"):
            self.num_laboratorios = int(linea.split(":")[1].strip())
          else:
            if linea.strip():
              try:
                partes = [p.strip() for p in linea.split(",")]
                peticion = {
                  "nombreFacultad": partes[0].split(":")[1].strip(),
                  "nombrePrograma": partes[1].split(":")[1].strip(),
                  "numSalones": int(partes[2].split(":")[1].strip()),
                  "numLaboratorios": int(partes[3].split(":")[1].strip())
                }
                self.peticiones.append(peticion)
              except Exception as e:
                print(f"{YELLOW}Advertencia: No se puedo leer un registro: {e}{RESET}")

        db.close()
    except Exception as e:
      print(f"{RED}Hubo un error leyendo el archivo: Error: {e}{RESET}")

  def __str__(self) -> str:
    return\
    f"Numero salones: {self.num_salones}\n"\
    f"Numero laboratorios: {self.num_laboratorios}\n\n"

  def crear_comunicacion(self) -> None:
    self.context = zmq.Context()
    self.context_workers = zmq.Context()

  
  def crear_workers(self, stop_event):
    for i in range(CANT_WORKERS):
        thread = threading.Thread(
            target=self.laburo,
            args=(self.url_worker, self.context_workers, i, stop_event)
        )
        thread.start()
        self.workers.append(thread)

  def laburo(self, worker_url, context, i,stop_event):
    socket_worker:zmq.Socket = None
    """ Worker using REQ socket to do LRU routing """
    socket_worker = context.socket(zmq.REQ)

    # set worker identity
    socket_worker.identity = (u"Worker-%d" % (i)).encode('ascii')
    socket_worker.connect(worker_url)

    # Tell the broker we are ready for work
    socket_worker.send(b"READY")

    while not stop_event.is_set():
      try:
          while True:
            address, empty, request_bytes = socket_worker.recv_multipart()
            request:dict = json.loads(request_bytes)
            print("%s: %s\n" % (socket_worker.identity.decode('ascii'),
                                request), end='')
            if isinstance(request, dict) and 'nombreFacultad' in request and 'nombrePrograma' in request:
              print(f"{YELLOW}Petición de {request['nombreFacultad']} - Programa {request['nombrePrograma']}{RESET}")
            else:
              print(f"{RED}Petición recibida malformada o incompleta: {request}{RESET}")
              continue  
            print(f"{MAGENTA}Contenido: {request}{RESET}")

            reserva_exitosa:bool = self.reservar_peticion(request)
            respuesta = {
              "respuesta": "y" if reserva_exitosa else "n",
              "salonesDisponibles": self.num_salones,
              "laboratoriosDisponibles": self.num_laboratorios
            }
            respuesta_codificada = json.dumps(respuesta).encode('utf-8')
            socket_worker.send_multipart([address, b'', respuesta_codificada])

            if reserva_exitosa:
              # Esperar confirmación de aceptación de la facultad
              _, raw_confirmacion = socket_worker.recv_multipart()
              confirmacion = zmq.utils.jsonapi.loads(raw_confirmacion)
            if confirmacion.get("confirmacion") == True:
              print(f"{GREEN}La facultad confirmó la reserva.{RESET}")
              self.guardar_peticion_db(request)
              self.peticiones.append(request)
            else:
              print(f"{RED}El broker rechazó la reserva.{RESET}") # Devolvemos recursos asignados
              self.num_salones += request.get("numSalones",0)
              self.num_laboratorios += request.get("numLaboratorios",0)
      except zmq.Again:
          time.sleep(0.1)  # Espera activa no bloqueante
          continue

      except Exception as e:
        print(f"{RED}[Worker id:{i}] Error al trabajar: {e}{RESET}")

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

  def cerrar_comunicacion(self) -> None:
    self.context.term()

  def guardar_peticion_db(self,peticion):
    peticion_txt = f"Nombre Facultad: {peticion['nombreFacultad']}, Nombre Programa: {peticion['nombrePrograma']}," \
      + f"Num Salones: {peticion['numSalones']}, Num Laboratorios: {peticion['numLaboratorios']}\n"
    self.db.write(peticion_txt)

  def cerrar_db(self):
    for peticion in self.peticiones:
      peticion_txt = f"Nombre Facultad: {peticion['nombreFacultad']}, Nombre Programa: {peticion['nombrePrograma']},"\
      + f"Num Salones: {peticion['numSalones']}, Num Laboratorios: {peticion['numLaboratorios']}\n"
      self.db.write(peticion_txt)

    self.db.write(f"Salones: {self.num_salones}\n")
    self.db.write(f"Laboratorios: {self.num_laboratorios}\n")
    self.db.close()

def run_server(stop_event: threading.Event):
  servidor_central = ServidorCentral()
  servidor_central.crear_comunicacion()
  time.sleep(2) # Esperar 2 segundos
  servidor_central.crear_workers(stop_event)
  print("[server-Respaldo] Iniciado ")
  try:
    while not stop_event.is_set():
      
      time.sleep(1)
      
  except KeyboardInterrupt:
    print(f"\n{RED}Servidor detenido manualmente.{RESET}")
    print(f"{YELLOW}Solicitudes fallidas almacenadas:{RESET}")
    for idx, solicitud in enumerate(servidor_central.solicitudes_fallidas, 1):
      print(f"{idx}. {solicitud}")
  finally:
    servidor_central.cerrar_comunicacion()
    servidor_central.cerrar_db()
    print("[server-Respaldo] Detenido")

def traer_archivo_central():
  i = 1


def main():
    # REQ socket hacia el Health Checker
    ctx_hc = zmq.Context()
    sub = ctx_hc.socket(zmq.SUB)
    sub.connect(HEALTH_CHECKER_ADDR)
    sub.setsockopt_string(zmq.SUBSCRIBE, "")  # recibe todo

    server_thread = None
    stop_event = threading.Event()

    print("[Respaldo] Comenzando ciclo de espera de arranque...")
    while True:
        # 1) Preguntamos al Health Checker
        respuesta = sub.recv_string()
        print(f"[Respaldo] HealthChecker respondió: {respuesta}")

        if respuesta == "START":
            # Si no está corriendo, arrancamos el broker
            if server_thread is None or not server_thread.is_alive():
                print("[Respaldo] Autorizado: iniciando server de respaldo...")
                stop_event.clear()
                server_thread = threading.Thread(
                    target=run_server,
                    args=(stop_event,),
                    daemon=True
                )
                server_thread.start()
        else:  # respuesta == "WAIT"
            # Si el broker está corriendo, lo detenemos
            if server_thread is not None and server_thread.is_alive():
                print("[Respaldo] Indicaron WAIT: deteniendo broker de respaldo...")
                stop_event.set()
                server_thread.join()
                server_thread = None

        # Esperamos antes de volver a preguntar
        time.sleep(1)
      

if __name__ == "__main__":
    main()
