from datetime import datetime,date
import zmq
import sys
from cryptography.fernet import Fernet
import json


class ProgramaAcademico:

# Atributos de la clase
  # Atributos del usuario
  usuario:str
  contrasena:str

  nombre:str
  semestre:date
  num_salones:int
  num_laboratorios:int
  ip_puerto_facultad:str
  ip_puerto_facultad_autenticacion:str # IP puerto para autenticar al usuario
  context:zmq.Context # Crea sockets para el proceso actual.
  context_autenticacion:zmq.Context # Sockets para la autenticacion
  socket_facultad:zmq.Socket # Socket para comunicarse con las facultades.
  socket_facultad_autenticacion:zmq.Socket # Socket para comunicarse con la autenticacion de las facultades.
  fernet:Fernet #Encriptador

# Metodos de la clase

  def __init__(self):
    self.nombre = ""
    self.semestre = None
    self.num_salones = 0
    self.num_laboratorios = 0
    self.ip_puerto_facultad = ""
    self.ip_puerto_facultad_autenticacion = ""
    self.context = None
    self.context_autenticacion = None
    self.socket_facultad = None

    if len(sys.argv) != 13:
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
      elif sys.argv[i] == "-ip-p-f-a":
        self.ip_puerto_facultad_autenticacion = sys.argv[i+1]

    if not self.campos_validos():
      print(self)
      print(f"Error: Ingreso una opcion/bandera erronea")
      self.error_args()
      sys.exit(-2)
    
    print("Informacion del programa academico.\n\n")
    print(self)

    self.leer_clave()
  
  def leer_clave(self):
    with open("clave.key", "rb") as archivo:
      clave = archivo.read()
    self.fernet = Fernet(clave)

  def autenticar_usuario(self):
    while(True):
      print("Ingrese sus datos para entrar al aplicativo")
      self.usuario = input("Usuario: ")
      self.contrasena = input("Contrasena: ")
      self.crear_conexion_autenticacion()
      es_usuario_valido = self.enviar_autenticacion_del_usuario_a_facultad()
      self.cerrar_conexion_autenticacion()
      if es_usuario_valido:
        break
      print("Usuario o contraseña incorrectos, intentelo de nuevo o contacte con su facultad")

  def campos_validos(self) -> bool:
    return self.nombre != "" and self.semestre is not None and 7 <= self.num_salones <= 10\
    and 2 <= self.num_laboratorios <= 4 and self.ip_puerto_facultad != "" and self.ip_puerto_facultad_autenticacion	!= ""

  def error_args(self):
    print(f"Recuerde ingresar todos los argumentos incluidas las banderas:\n\n")
    print(f"-n \"nombre_programa\": Es el nombre del programa academico")
    print(f"-s \"mm-yyyy\": Es la fecha del semestre")
    print(f"-num-s \"numero_salones\": Es el numero de salones(entre 7 y 10)")
    print(f"-num-l \"numero_laboratorios\": Es el numero de laboratorios(entre 2 y 4)")
    print(f"-ip-p-f \"ip_facultad:puerto_facultad\": Es la ip y el puerto de la facultad")
    print(f"-ip-p-f-a \"ip_facultad:puerto_de_autenticacion\": Es la ip y el puerto designado por la facultad para autenticar")

  def __str__(self) -> str:
    return\
      f"Nombre: {self.nombre}\n"\
      f"Semestre: {self.semestre}\n"\
      f"Numero Salones: {self.num_salones}\n"\
      f"Numero Laboratorios: {self.num_laboratorios}\n"\
      f"Ip y Puerto de Facultad: {self.ip_puerto_facultad}\n"\
      f"Ip y Puerto de la conexion de autenticacion de la facultad: {self.ip_puerto_facultad_autenticacion}\n\n"\

  def crear_conexion(self) -> None:
    self.context = zmq.Context()
    self.socket_facultad = self.context.socket(zmq.REQ)
    self.socket_facultad.connect(f"tcp://{self.ip_puerto_facultad}") # tcp://direccion_facultad:5555

  def crear_conexion_autenticacion(self) -> None:
    self.context_autenticacion = zmq.Context()
    self.socket_facultad_autenticacion = self.context_autenticacion.socket(zmq.REQ)
    self.socket_facultad_autenticacion.connect(f"tcp://{self.ip_puerto_facultad_autenticacion}") # tcp://direccion_facultad:5566

  def enviar_info_programa_a_facultad(self) -> None:
    print("Construyendo informacion en formato JSON...")
    mensaje_json = json.dumps(self.transformar_info_diccionario()).encode()
    print("Encriptando informacion...")
    mensaje_cifrado = self.fernet.encrypt(mensaje_json)
    print(f"Mensaje encriptado: {mensaje_cifrado}")
    print("Enviando informacion encriptada...")
    self.socket_facultad.send(mensaje_cifrado)
    print("informacion enviada.")

    respuesta_cifrada = self.socket_facultad.recv() 
    print(f"Respuesta encriptada: {respuesta_cifrada}")
    respuesta_descifrada:str = self.fernet.decrypt(respuesta_cifrada).decode()
    print("Respuesta: %s\n"%respuesta_descifrada)

  def enviar_autenticacion_del_usuario_a_facultad(self) -> bool:
    
    print("Construyendo usuario en formato JSON...")
    mensaje_json = json.dumps(self.transformar_autenticacion_en_diccionario()).encode()
    print("Encriptando usuario...")
    mensaje_cifrado = self.fernet.encrypt(mensaje_json)
    print(f"Mensaje encriptado: {mensaje_cifrado}")
    print("Enviando usuario encriptado...")
    self.socket_facultad_autenticacion.send(mensaje_cifrado)
    print("usuario enviado.")
    respuesta_cifrada = self.socket_facultad_autenticacion.recv() # La facultad responde si el usuario existe o no
    print(f"Respuesta encriptada: {respuesta_cifrada}")
    respuesta_descifrada:str = self.fernet.decrypt(respuesta_cifrada).decode()
    print("Respuesta: %s\n"%respuesta_descifrada)
    if respuesta_descifrada == "y":
      return True
    return False

  def cerrar_conexion(self) -> None:
    self.socket_facultad.close()
    self.context.term()
    print("Comunicacion cerrada.")

  def cerrar_conexion_autenticacion(self) -> None:
    self.socket_facultad_autenticacion.close()
    self.context_autenticacion.term()

  def transformar_info_diccionario(self) -> dict:
    return {
      "nombrePrograma":self.nombre,
      "semestre":self.semestre.strftime("%d-%m-%Y"),
      "numSalones":self.num_salones,
      "numLaboratorios":self.num_laboratorios
    }
  
  def transformar_autenticacion_en_diccionario(self) -> dict:
    return {
      "usuario":self.usuario,
      "contrasena":self.contrasena
    }

# Seccion main del programa

if __name__ == "__main__":
  programa_academico:ProgramaAcademico = ProgramaAcademico()
  programa_academico.autenticar_usuario() # Se autentica al usuario
  programa_academico.crear_conexion()
  programa_academico.enviar_info_programa_a_facultad()
  programa_academico.cerrar_conexion()
