import zmq
from datetime import datetime, date
import sys

class ProgramaAcademico:

    # Atributos de la clase
    nombre: str
    semestre: date
    num_salones: int
    num_laboratorios: int
    ip_puerto_facultad: str
    context: zmq.Context            # Crea sockets para el proceso actual.
    socket_facultad: zmq.Socket     # Socket para comunicarse con las facultades.

    # Métodos de la clase

    def __init__(self):
        self.nombre = ""
        self.semestre = None
        self.num_salones = 0
        self.num_laboratorios = 0
        self.ip_puerto_facultad = ""
        self.context = None
        self.socket_facultad = None
        # python3 programa_academico.py -n programa -s 05-2025 -num-s 6 -num-l 2 -ip-p-f localhost:6000
        if len(sys.argv) != 11:
            print("Error: Ingresó un número inválido de argumentos. Verifique.\n")
            self.error_args()
            sys.exit(-3)

        for i in range(1, len(sys.argv)):
            if sys.argv[i] == "-n":
                self.nombre = sys.argv[i + 1]
            elif sys.argv[i] == "-s":
                try:
                    # Parsear "mm-YYYY" a date (usa día=1 por defecto)
                    self.semestre = datetime.strptime(sys.argv[i + 1], "%m-%Y").date()
                except ValueError:
                    print(f"Error: Formato de fecha inválido '{sys.argv[i+1]}'. Use mm-YYYY.\n")
                    self.error_args()
                    sys.exit(-4)
            elif sys.argv[i] == "-num-s":
                self.num_salones = int(sys.argv[i + 1])
            elif sys.argv[i] == "-num-l":
                self.num_laboratorios = int(sys.argv[i + 1])
            elif sys.argv[i] == "-ip-p-f":
                self.ip_puerto_facultad = sys.argv[i + 1]

        if not self.campos_validos():
            print(self)
            print("Error: Ingresó una opción/bandera errónea o algún campo fuera de rango.")
            self.error_args()
            sys.exit(-2)

        print("Información del programa académico:\n")
        self.mostrar_info_programa()

    def campos_validos(self) -> bool:
        return (
            self.nombre != ""
            and self.semestre is not None
            and 7 <= self.num_salones <= 10
            and 2 <= self.num_laboratorios <= 4
            and self.ip_puerto_facultad != ""
        )

    def error_args(self):
        print("Recuerde ingresar todos los argumentos incluidas las banderas:\n")
        print("-n \"nombre_programa\": Es el nombre del programa académico")
        print("-s \"mm-YYYY\": Es la fecha del semestre (por ejemplo, 05-2025)")
        print("-num-s \"numero_salones\": Es el número de salones (entre 7 y 10)")
        print("-num-l \"numero_laboratorios\": Es el número de laboratorios (entre 2 y 4)")
        print("-ip-p-f \"ip_facultad:puerto_facultad\": Es la IP y el puerto de la facultad")

    def mostrar_info_programa(self) -> None:
        print(
            f"""
    Nombre: {self.nombre}
    Semestre: {self.semestre.strftime("%m-%Y")}
    Número Salones: {self.num_salones}
    Número Laboratorios: {self.num_laboratorios}
    IP y Puerto de Facultad: {self.ip_puerto_facultad}
    """
        )

    def obtener_info_programa_string(self) -> str:
        return f"""
    Nombre: {self.nombre}
    Semestre: {self.semestre.strftime("%m-%Y")}
    Número Salones: {self.num_salones}
    Número Laboratorios: {self.num_laboratorios}
    IP y Puerto de Facultad: {self.ip_puerto_facultad}
    """

    def crear_conexion(self) -> None:
        self.context = zmq.Context()
        self.socket_facultad = self.context.socket(zmq.REQ)
        # Conecta al servidor de la facultad
        self.socket_facultad.connect(f"tcp://{self.ip_puerto_facultad}")

    def enviar_info_programa_a_facultad(self) -> None:
        print("Enviando información del programa en formato JSON...")
        self.socket_facultad.send_json(self.transformar_info_diccionario())
        print("Información enviada. Esperando respuesta del servidor…")

        respuesta: str = self.socket_facultad.recv_string()
        print(f"Respuesta Servidor: '{respuesta}'\n")

        # Aquí determinamos si la petición se consideró "satisfecha" o no.
        # En este ejemplo, interpretamos que el servidor devuelve "OK" (o "ok", 
        # no sensible a mayúsculas) para indicar éxito (exit code = 0). Cualquier 
        # otra respuesta se toma como "no satisfecha" (exit code = 1).
        if respuesta.strip().lower() == "ok":
            print("Petición satisfecha. Saliendo con código 0.\n")
            sys.exit(0)
        else:
            print("Petición NO satisfecha. Saliendo con código 1.\n")
            sys.exit(1)

    def cerrar_conexion(self) -> None:
        # Aunque con sys.exit nunca llega aquí, lo dejamos por si se modifica la lógica.
        self.socket_facultad.close()
        self.context.term()
        print("Comunicación cerrada.")

    def transformar_info_diccionario(self) -> dict:
        # Convertimos la fecha a "dd-mm-YYYY" (día=01 por defecto)
        fecha_str = self.semestre.strftime("%d-%m-%Y")
        return {
            "nombrePrograma": self.nombre,
            "semestre": fecha_str,
            "numSalones": self.num_salones,
            "numLaboratorios": self.num_laboratorios,
        }


# Sección main del programa
if __name__ == "__main__":
    programa_academico: ProgramaAcademico = ProgramaAcademico()
    programa_academico.crear_conexion()
    programa_academico.enviar_info_programa_a_facultad()
    programa_academico.cerrar_conexion()

