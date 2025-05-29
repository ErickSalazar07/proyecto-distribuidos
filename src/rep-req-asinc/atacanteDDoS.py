import zmq
import time
import json

context = zmq.Context()
socket = context.socket(zmq.DEALER)  # DEALER para que coincida con ROUTER en el servidor
socket.identity = b"facultad_atacante"  # identidad fija
socket.connect("tcp://localhost:5555")

# Mensaje válido de prueba
mensaje = {
    "nombreFacultad": "Facultad Maliciosa",
    "nombrePrograma": "Programa Spam",
    "numSalones": 1,
    "numLaboratorios": 1
}
confirmacion = {
    "confirmacion":False
}

# Enviar muchas peticiones seguidas
for i in range(30):
    print(f"[{i+1}] Enviando petición maliciosa...")
    socket.send_json(mensaje)
    socket.send_json(confirmacion)
    time.sleep(0.1)  # Espera muy corta (ajusta para que dispare el umbral)
