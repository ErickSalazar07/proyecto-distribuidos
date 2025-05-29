import zmq
import zmq.utils.jsonapi
import time
import sys
import threading

class ServidorCentralWorker:

    def __init__(self, id_worker: int, num_salones: int, num_laboratorios: int):
        self.id_worker = id_worker
        self.num_salones = num_salones
        self.num_laboratorios = num_laboratorios
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)
        self.socket.identity = f"worker-{id_worker}".encode("ascii")
        self.socket.connect("tcp://localhost:5557")  # Conexión al backend del broker

    def atender_peticiones(self):
        print(f"[Worker {self.id_worker}] Escuchando peticiones del broker...")
        while True:
            try:
                msg = self.socket.recv_multipart()
                if len(msg) == 2:
                    identity, raw_msg = msg
                else:
                    # DEALER-DEALER puede tener más frames, simplificación:
                    identity, raw_msg = msg[0], msg[-1]

                peticion = zmq.utils.jsonapi.loads(raw_msg)

                print(f"[Worker {self.id_worker}] Petición recibida: {peticion}")

                num_salones_pedido = peticion.get("numSalones", 0)
                num_laboratorios_pedido = peticion.get("numLaboratorios", 0)

                reserva_exitosa = False
                if self.num_salones >= num_salones_pedido and self.num_laboratorios >= num_laboratorios_pedido:
                    self.num_salones -= num_salones_pedido
                    self.num_laboratorios -= num_laboratorios_pedido
                    reserva_exitosa = True

                respuesta = {
                    "respuesta": "y" if reserva_exitosa else "n",
                    "salonesDisponibles": self.num_salones,
                    "laboratoriosDisponibles": self.num_laboratorios
                }

                self.socket.send_multipart([identity, zmq.utils.jsonapi.dumps(respuesta)])
            except Exception as e:
                print(f"[Worker {self.id_worker}] Error: {e}")

    def cerrar(self):
        self.socket.close()
        self.context.term()

# Main
if __name__ == "__main__":
    num_salones = int(input("Ingrese el número de salones: "))
    num_laboratorios = int(input("Ingrese el número de laboratorios: "))
    cantidad_workers = int(input("¿Cuántos workers desea lanzar?: "))

    for i in range(cantidad_workers):
        worker = ServidorCentralWorker(i, num_salones, num_laboratorios)
        threading.Thread(target=worker.atender_peticiones, daemon=True).start()

    print("Workers lanzados. Presione Ctrl+C para salir.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Apagando workers.")
