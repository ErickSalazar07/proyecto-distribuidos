import zmq
import threading
import time

class HealthChecker:
    """
    Este componente:
      - Recibe pings de los servidores en PULL(5550)
      - Atiende consultas de las facultades en REP(5553)
      - Mantiene self.servidor_activo = "principal"|"auxiliar"
    """
    def __init__(self, contexto):
        self.ctx = contexto

        # Dirección de pings entrantes desde servidores
        self.puerto_ping = 5550
        # Puerto donde facultades preguntan estado
        self.puerto_estado = 5553

        # Socket que recibe pings de servidores
        self.sock_ping = self.ctx.socket(zmq.PULL)
        self.sock_ping.bind(f"tcp://*:{self.puerto_ping}")

        # Socket que responde a consultas de facultades
        self.sock_estado = self.ctx.socket(zmq.REP)
        self.sock_estado.bind(f"tcp://*:{self.puerto_estado}")

        # Estado inicial
        self.servidor_activo = "principal"

    def _gestionar_estado(self):
        """ Hilo que atiende preguntas de facultades. """
        while True:
            msg = self.sock_estado.recv_json()
            if msg.get("estadoServidor") is True:
                respuesta = {
                    "servidorActivo": self.servidor_activo,
                    # Aquí asumes mismo puerto para ambos; podrías variar según tu infra
                    "ipPuerto": "localhost:5555"  
                }
                self.sock_estado.send_json(respuesta)
            else:
                # Mensaje mal formado
                self.sock_estado.send_json({"error": "formato inválido"})

    def _escanear_pings(self):
        """ Hilo que actualiza self.servidor_activo según llegada de pings. """
        poll = zmq.Poller()
        poll.register(self.sock_ping, zmq.POLLIN)

        while True:
            eventos = dict(poll.poll(timeout=2000))  # 2s
            if self.sock_ping in eventos:
                datos = self.sock_ping.recv_json()
                # Se espera {'estado': 'ok'} o similar
                if datos.get("estado") == "ok":
                    self.servidor_activo = "principal"
                else:
                    self.servidor_activo = "auxiliar"
            else:
                # No llegó ping en 2s → considerar caída principal
                self.servidor_activo = "auxiliar"

    def arrancar(self):
        """ Lanza hilos de ping y consultas. """
        threading.Thread(target=self._gestionar_estado, daemon=True).start()
        threading.Thread(target=self._escanear_pings, daemon=True).start()
        print(f"🩺 HealthChecker iniciado (ping en {self.puerto_ping}, estado en {self.puerto_estado})")


def main():
    ctx = zmq.Context()

    # --- Inicializar y arrancar HealthChecker ---
    hc = HealthChecker(ctx)
    hc.arrancar()

    # --- Sockets del broker (proxy) ---
    frontend = ctx.socket(zmq.ROUTER)
    frontend.bind("tcp://*:6000")    # Peticiones de facultades

    backend = ctx.socket(zmq.ROUTER)
    backend.bind("tcp://*:7000")     # Conexión de workers

    print("🔄 Broker escuchando:")
    print("    - Clientes en tcp://*:6000")
    print("    - Workers en tcp://*:7000")
    print("    - HealthChecker en puertos 5550/5553")
    # Ejecuta el proxy que enruta todo entre frontend ↔ backend
    zmq.proxy(frontend, backend)

    # (Nunca llega aquí salvo interrupción)
    frontend.close()
    backend.close()
    ctx.term()


if __name__ == "__main__":
    main()
