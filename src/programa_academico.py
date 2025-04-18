import zmq

class ProgramaAcademico:

# Atributos de la clase
  nombre:str
  semestre:str
  num_salones:int
  num_laboratorios:int
  ip_puerto_facultad:str
  context:zmq.Context
  socket:zmq.SyncSocket

# Metodos de la clase

  def __init__(this):
    this.nombre = input("Dijite el nombre: ")
    this.semestre = input("Dijite el semestre: ")
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
    this.socket = this.context.socket(zmq.REQ)
    this.socket.connect(f"tcp://{this.ip_puerto_facultad}")

  def enviar_info_programa_a_facultad(this) -> None:
    print("Enviando informacion de programa...")
    this.socket.send_string(this.obtener_info_programa_string())
    print("Informacion enviada.")

  def cerrar_conexion(this) -> None:
    this.socket.close()
    this.context.term()

# Seccion main del programa

if __name__ == "__main__":
  programa_academico:ProgramaAcademico = ProgramaAcademico()
  programa_academico.crear_conexion()
  programa_academico.enviar_info_programa_a_facultad()
  programa_academico.cerrar_conexion()
