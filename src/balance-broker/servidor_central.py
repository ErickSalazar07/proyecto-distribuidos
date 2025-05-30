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

class ServidorCentral:

  num_salones:int
  num_laboratorios:int
  solicitudes_fallidas:list
  peticiones:list
  context:zmq.Context
  context_workers:zmq.Context
  context_persistencia:zmq.Context
  socket_health_checker:zmq.Socket
  socket_persistencia:zmq.Socket
  ip_puerto_health_checker:str
  ip_puerto_persistencia:str
  hilo_health:threading.Thread
  hilo_persistencia:threading.Thread
  url_worker:str
  workers:list

  def __init__(self,stop_event: threading.Event):

    self.stop_event = stop_event
    self.db = None
    self.num_salones = 0
    self.num_laboratorios = 0
    self.solicitudes_fallidas = list()
    self.context = None
    self.context_workers = None
    self.context_persistencia = None
    self.socket_health_checker = None
    self.socket_persistencia = None
    self.hilo_health = None
    self.hilo_persistencia = None
    self.ip_puerto_health_checker = "localhost:5550"
    self.ip_puerto_persistencia = "localhost:6000"
    self.url_worker = "tcp://localhost:5555"
    self.workers = []
    self.peticiones = []
    # self.ip_puerto_health_checker = "10.43.96.80:5550"
    
    self.cargar_db("db.txt")
    print("Informacion del servidor.\n\n")
    print(self)
    self.db = open("db.txt","a+")
    
  def cargar_db(self,nombre_db:str):
    try:
      with open(nombre_db,"r") as db:
        for linea in db:
          if linea.startswith("Salones:"):
            self.num_salones = int(linea.split(":")[1].strip())
            print(f"{CYAN}Valores cargados: salones={self.num_salones}, labs={self.num_laboratorios}{RESET}")
          elif linea.startswith("Laboratorios:"):
            self.num_laboratorios = int(linea.split(":")[1].strip())
            print(f"{CYAN}Valores cargados: salones={self.num_salones}, labs={self.num_laboratorios}{RESET}")
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
    self.context_persistencia = zmq.Context()
    
    # Comunicacion con health checker
    self.socket_health_checker = self.context.socket(zmq.PUSH)
    self.socket_health_checker.connect(f"tcp://{self.ip_puerto_health_checker}")

    # Crear hilo para comunicacion con health checker
    self.hilo_health = threading.Thread(target=self.comunicar_estado_health_checker, daemon=True)
    self.hilo_health.start()

    # Comunicacion con base de respaldo
    self.socket_persistencia = self.context_persistencia.socket(zmq.REQ)
    self.socket_persistencia.connect(f"tcp://{self.ip_puerto_persistencia}")

    # Crear hilo para comunicacion con respaldo
    #self.hilo_persistencia = threading.Thread(target=self.comunicar_servidor_respaldo, daemon=True)
    #self.hilo_persistencia.start()
  
  #def comunicar_servidor_respaldo():
    #Esperar a que existe un cambio en db
    #Enviarle archivo al servidor
    #Esperar respuesta

  def crear_workers(self):
    for i in range(CANT_WORKERS):
        thread = threading.Thread(target=self.laburo,
                                  args=(self.url_worker, self.context_workers, i, ))
        thread.start()
        self.workers.append(thread)

  def laburo(self, worker_url, context, i):
    socket_worker:zmq.Socket = None
    """ Worker using REQ socket to do LRU routing """
    socket_worker = context.socket(zmq.REQ)

    # set worker identity
    socket_worker.identity = (u"Worker-%d" % (i)).encode('ascii')
    socket_worker.connect(worker_url)

    # Tell the broker we are ready for work
    socket_worker.send(b"READY")
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

        respuesta = self.reservar_peticion(request)
        reserva_exitosa:bool = respuesta.get("estatus")
        respuesta = {
          "respuesta": "y" if reserva_exitosa else "n",
          "salonesDisponibles": self.num_salones,
          "laboratoriosDisponibles": self.num_laboratorios
        }
        respuesta_codificada = json.dumps(respuesta).encode('utf-8')
        socket_worker.send_multipart([address, b'', respuesta_codificada])

        if reserva_exitosa:
          print(f"{GREEN}Reserva exitosa.{RESET}")
          self.num_salones -= request.get("numSalones",0)
          self.num_laboratorios -= request.get("numLaboratorios",0)
          self.guardar_peticion_db(request)
          self.peticiones.append(request)
          # Esperar confirmación de aceptación de la facultad
          '''
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
          '''

    except Exception as e:
      print(f"{RED}[Worker id:{i}] Error al trabajar: {e}{RESET}")

  def comunicar_estado_health_checker(self):
    while not self.stop_event.is_set():
        mensaje = {"estado": "ok"}
        try:
            self.socket_health_checker.send_json(mensaje)
            print(f"{BLUE}[Health Check] Estado enviado al health_checker.{RESET}")
        except zmq.ZMQError as e:
            print(f"{RED}[Health Check] Error al enviar estado: {e}{RESET}")
            break  # Detenemos el hilo si el socket fue cerrado
        time.sleep(2)# Espera 2 segundo a enviar el siguiente ping o estado

  def reservar_peticion(self,peticion:dict) -> dict:
    numero_salones = peticion.get("numSalones",0)
    numero_laboratorios = peticion.get("numLaboratorios",0)

    if self.num_salones >= numero_salones and self.num_laboratorios >= numero_laboratorios:
      return {"estatus": True, "laboratoriosDisponibles": True}
    '''
    elif self.num_salones >= numero_salones:
      self.num_salones -= numero_salones
      return {"estatus": True, "laboratoriosDisponibles": False}
    self.solicitudes_fallidas.append(peticion)
    '''
    print(f"{RED}Solicitud no atendida guardada en lista de peticiones fallidas.{RESET}")
    return {"estatus": False, "laboratoriosDisponibles": False}

  def cerrar_comunicacion(self) -> None:
    self.stop_event.set()  # Señal para detener los hilos

    # Esperamos a que el hilo termine (opcional, si no es daemon)
    if self.hilo_health and self.hilo_health.is_alive():
        self.hilo_health.join()

    if self.socket_health_checker:
        self.socket_health_checker.close()

    # No termines el contexto si planeas reiniciar este objeto
    # self.context.term()


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

if __name__ == "__main__":
    stop_event = threading.Event()  # ← Nuevo

    servidor_central = ServidorCentral(stop_event)  # ← Pásalo al constructor
    servidor_central.crear_comunicacion()

    try:
        time.sleep(2) # Esperar 2 segundos
        servidor_central.crear_workers()
        for worker in servidor_central.workers:
            worker.join()
    except KeyboardInterrupt:
        print(f"\n{RED}Servidor detenido manualmente.{RESET}")
        print(f"{YELLOW}Solicitudes fallidas almacenadas:{RESET}")
        for idx, solicitud in enumerate(servidor_central.solicitudes_fallidas, 1):
            print(f"{idx}. {solicitud}")
        stop_event.set()  # ← Esto hace que el hilo de health checker termine
    finally:
        servidor_central.cerrar_comunicacion()
        servidor_central.cerrar_db()

