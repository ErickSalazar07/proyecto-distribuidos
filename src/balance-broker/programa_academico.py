import zmq
from datetime import datetime,date

class ProgramaAcademico:

# Atributos de la clase
  nombre:str
  semestre:date
  num_salones:int
  num_laboratorios:int
  ip_puerto_facultad:str
  context:zmq.Context # Crea sockets para el proceso actual.
  socket_facultad:zmq.Socket # Socket para comunicarse con las facultades.

# Metodos de la clase

  def __init__(self):
    self.nombre = input("Dijite el nombre: ")
    self.semestre = datetime.strptime(input("Dijite el semestre con formato (mm-yyyy): "),"%m-%Y").date()
    self.num_salones = int(input("Dijite el numero de salones: "))
    self.num_laboratorios = int(input("Dijite el numero de laboratorios: "))
    self.ip_puerto_facultad = input("Dijite la ip y el puerto de la facultad, con el formato(ip:puerto): ")

  def mostrar_info_programa(self) -> None:
    print(
      f"""
      Nombre: {self.nombre}
      Semestre: {self.semestre}
      Numero Salones: {self.num_salones}
      Numero Laboratorios: {self.num_laboratorios}
      Ip y Puerto de Facultad: {self.ip_puerto_facultad}
      """)

  def obtener_info_programa_string(self) -> str:
    return f"""
      Nombre: {self.nombre}
      Semestre: {self.semestre}
      Numero Salones: {self.num_salones}
      Numero Laboratorios: {self.num_laboratorios}
      Ip y Puerto de Facultad: {self.ip_puerto_facultad}
      """

  def crear_conexion(self) -> None:
    self.context = zmq.Context()
    self.socket_facultad = self.context.socket(zmq.REQ)
    self.socket_facultad.connect(f"tcp://{self.ip_puerto_facultad}") # tcp://direccion_facultad:5555

  def enviar_info_programa_a_facultad(self) -> None:
    print("Enviando informacion del programa en formato JSON...")
    self.socket_facultad.send_json(self.transformar_info_diccionario())
    print("Informacion enviada.")
    respuesta:str = self.socket_facultad.recv_string();
    print("Respuesta: %s\n"%respuesta)

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
  programa_academico:ProgramaAcademico = ProgramaAcademico()
  programa_academico.crear_conexion()
  programa_academico.enviar_info_programa_a_facultad()
  programa_academico.cerrar_conexion()
