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
  socket_facultad:zmq.SyncSocket # Socket para comunicarse con las facultades.

# Metodos de la clase

  def __init__(this):
    this.nombre = input("Dijite el nombre: ")
    this.semestre = datetime.strptime(input("Dijite el semestre con formato (mm-yyyy): "),"%m-%Y").date()
    this.num_salones = int(input("Dijite el numero de salones: "))
    this.num_laboratorios = int(input("Dijite el numero de laboratorios: "))
    this.ip_puerto_facultad = input("Dijite la ip y el puerto de la facultad, con el formato(ip:puerto): ")

  def mostrar_info_programa(this) -> None:
    print(
      f"""
      Nombre: {this.nombre}
      Semestre: {this.semestre}
      Numero Salones: {this.num_salones}
      Numero Laboratorios: {this.num_laboratorios}
      Ip y Puerto de Facultad: {this.ip_puerto_facultad}
      """)

  def obtener_info_programa_string(this) -> str:
    return f"""
      Nombre: {this.nombre}
      Semestre: {this.semestre}
      Numero Salones: {this.num_salones}
      Numero Laboratorios: {this.num_laboratorios}
      Ip y Puerto de Facultad: {this.ip_puerto_facultad}
      """

  def crear_conexion(this) -> None:
    this.context = zmq.Context()
    this.socket_facultad = this.context.socket(zmq.REQ)
    this.socket_facultad.connect(f"tcp://{this.ip_puerto_facultad}")

  def enviar_info_programa_a_facultad(this) -> None:
    print("Enviando informacion del programa en formato JSON...")
    this.socket_facultad.send_json(this.transformar_info_diccionario())
    print("Informacion enviada.")
    respuesta:str = this.socket_facultad.recv_string();
    print("Respuesta: %s\n"%respuesta)

  def cerrar_conexion(this) -> None:
    this.socket_facultad.close()
    this.context.term()
    print("Comunicacion cerrada.")

  def transformar_info_diccionario(this) -> dict:
    return {
      "nombre":this.nombre,
      "semestre":this.semestre.strftime("%d-%m-%Y"),
      "numSalones":this.num_salones,
      "numLaboratorios":this.num_laboratorios
    }

# Seccion main del programa

if __name__ == "__main__":
  programa_academico:ProgramaAcademico = ProgramaAcademico()
  programa_academico.crear_conexion()
  programa_academico.enviar_info_programa_a_facultad()
  programa_academico.cerrar_conexion()
