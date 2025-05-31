import zmq
from datetime import datetime,date
import sys
import time  # Importamos el módulo time

class ProgramaAcademico:

# Atributos de la clase
  nombre:str
  semestre:date
  num_salones:int
  num_laboratorios:int
  ip_puerto_facultad:str
  context:zmq.Context # Crea sockets para el proceso actual.
  socket_facultad:zmq.Socket # Socket para comunicarse con las facultades.
  tiempo_respuesta: float  # Nuevo atributo para almacenar el tiempo de respuesta

# Metodos de la clase

  def __init__(self):
    self.nombre = ""
    self.semestre = None
    self.num_salones = 0
    self.num_laboratorios = 0
    self.ip_puerto_facultad = ""
    self.context = None
    self.socket_facultad = None
    self.tiempo_respuesta = 0.0
    #python3 programa_academico.py -n programa -s 05-2025 -num-s 6 -num-l 2 -ip-p-f localhost:6000
    if len(sys.argv) != 11:
      print("Error: Ingreso un numero invalido de argumentos. Verifique.\n")
      self.error_args()
      sys.exit(-3)

    for i in range(1,len(sys.argv)):
      if sys.argv[i] == "-n":
        self.nombre = sys.argv[i+1]
      elif sys.argv[i] == "-s":
        self.semestre = datetime.strptime(sys.argv[i+1],"%m-%Y").date()
      elif sys.argv[i] == "-num-s":
        self.num_salones = int(sys.argv[i+1])
      elif sys.argv[i] == "-num-l":
        self.num_laboratorios = int(sys.argv[i+1])
      elif sys.argv[i] == "-ip-p-f":
        self.ip_puerto_facultad = sys.argv[i+1]
      

    if not self.campos_validos():
      print(self)
      print(f"Error: Ingreso una opcion/bandera erronea")
      self.error_args()
      sys.exit(-2)
    
    print("Informacion del programa academico.\n\n")
    print(self)

  def campos_validos(self) -> bool:
    return self.nombre != "" and self.semestre is not None and 7 <= self.num_salones <= 10\
    and 2 <= self.num_laboratorios <= 4 and self.ip_puerto_facultad != "" 

  def error_args(self):
    print(f"Recuerde ingresar todos los argumentos incluidas las banderas:\n\n")
    print(f"-n \"nombre_programa\": Es el nombre del programa academico")
    print(f"-s \"mm-yyyy\": Es la fecha del semestre")
    print(f"-num-s \"numero_salones\": Es el numero de salones(entre 7 y 10)")
    print(f"-num-l \"numero_laboratorios\": Es el numero de laboratorios(entre 2 y 4)")
    print(f"-ip-p-f \"ip_facultad:puerto_facultad\": Es la ip y el puerto de la facultad")
  
  def crear_conexion(self) -> None:
    self.context = zmq.Context()
    self.socket_facultad = self.context.socket(zmq.REQ)
    self.socket_facultad.connect(f"tcp://{self.ip_puerto_facultad}") # tcp://direccion_facultad:5555

  def enviar_info_programa_a_facultad(self) -> bool:
    print("Enviando informacion del programa en formato JSON...")
    
    # Medimos el tiempo de respuesta
    start_time = time.perf_counter()
    self.socket_facultad.send_json(self.transformar_info_diccionario())
    print("Informacion enviada.")
    respuesta:str = self.socket_facultad.recv_string()
    end_time = time.perf_counter()
    
    self.tiempo_respuesta = end_time - start_time
    print(f"Tiempo de respuesta: {self.tiempo_respuesta:.6f} segundos")
    print("Respuesta Servidor: %s\n"%respuesta)
    
    satisfecha = "aceptada" in respuesta
    # Guardamos el resultado en un archivo
    with open("resultados.txt", "a") as f:
        f.write(f"{self.tiempo_respuesta:.6f},{satisfecha}\n")
    
    return satisfecha

  def cerrar_conexion(self) -> None:
    self.socket_facultad.close()
    self.context.term()
    print("Comunicacion cerrada.")

  def transformar_info_diccionario(self) -> dict:
    return {
      "nombrePrograma":self.nombre,
      "semestre":self.semestre.strftime("%d-%m-%Y"),
      "numSalones":self.num_salones,
      "numLaboratorios":self.num_laboratorios
    }

# Seccion main del programa

if __name__ == "__main__":
  programa_academico = ProgramaAcademico()
  programa_academico.crear_conexion()
  satisfecha = programa_academico.enviar_info_programa_a_facultad()
  programa_academico.cerrar_conexion()
  
  # Código de salida para indicar éxito o fracaso
  sys.exit(0 if satisfecha else 1)
