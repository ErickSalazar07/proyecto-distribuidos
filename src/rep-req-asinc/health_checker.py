import zmq
import time
import threading

class HealthChecker:

# Atributos de la clase
  ip_puerto_servidor_principal:str
  ip_puerto_servidor_auxiliar:str
  puerto_escuchar_facultades:str
  puerto_publicaciones:str
  context:zmq.Context
  socket_servidor_principal:zmq.Socket
  socket_servidor_auxiliar:zmq.Socket
  socket_publicacion:zmq.Socket
  servidor_activo:str

# Metodos de la clase

  def __init__(self):
    #self.ip_puerto_servidor_principal = "10.43.96.68:5555"
    #self.ip_puerto_servidor_auxiliar = "10.43.96.80:5555"
    self.ip_puerto_servidor_principal = "localhost:5555"
    self.ip_puerto_servidor_auxiliar = "localhost:5555"
    self.puerto_escuchar_facultades = "5552"
    self.puerto_publicaciones = "5553"
    self.context = None
    self.socket_servidor_principal = None
    self.socket_servidor_auxiliar = None
    self.socket_publicacion = None
    self.servidor_activo = "principal"

  def crear_conexion(self):
    self.context = zmq.Context()
    
    # Scoket para recibir ping del servidor (PULL)
    self.socket_servidor_principal = self.context.socket(zmq.PULL)
    self.socket_servidor_principal.bind("tcp://*:5550")

    # Socket para publicar estado facultades (PUB)
    self.socket_publicacion = self.context.socket(zmq.PUB)
    self.socket_publicacion.bind(f"tcp://*:{self.puerto_publicaciones}")

  def publicar_estado(self):
    while True:
      estado = {
        "servidorActivo": self.servidor_activo,
        "ipPuerto": self.ip_puerto_servidor_principal if self.servidor_activo == "principal" else self.ip_puerto_servidor_auxiliar
      }
      self.socket_publicacion.send_json(estado)
      print(f"📢 Publicando estado: {estado}")
      time.sleep(1)

  def escuchar_ping_servidor_central(self):
    print("🩺 Health checker escuchando pings del servidor central o auxiliar...\n")
    poller = zmq.Poller()
    poller.register(self.socket_servidor_principal,zmq.POLLIN)

    threading.Thread(target=self.publicar_estado,daemon=True).start()

    while True:
      # Espera hasta 2 segundos por el ping o respuesta del servidor
      socks = dict(poller.poll(timeout=2000)) # 2000 ms = 2 segundos

      if self.socket_servidor_principal in socks:
        mensaje = self.socket_servidor_principal.recv_json()
        print(f"✅ Ping recibido: {mensaje}")

        if mensaje.get("estado") == "ok":
          self.servidor_activo = "principal"
        else:
          self.servidor_activo = "auxiliar"
        print(f"🔁 Servidor activo: {self.servidor_activo}\n")
      else:
        print("❌ No se recibió ping en 2 segundos. Cambiando de servidor...")
        self.servidor_activo = "auxiliar"
        print(f"⚠️ Nuevo servidor activo: {self.servidor_activo}\n")

# Pseudo codigo:
# 1. Prender el health
# 2. Quedarse escuchando a la facultades, en un hilo
# 3. Ir verificando que servidor esta activo
# 4. tener una variable donde 0 sea servidor central y 1 servidor aux
# 5. mantener este proceso hasta que que los dos servidores se apaguen o no respondan

if __name__ == "__main__":
  health_checker = HealthChecker()
  health_checker.crear_conexion()
  health_checker.escuchar_ping_servidor_central()