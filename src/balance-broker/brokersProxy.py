# broker_proxy.py

import zmq

def main():
    context = zmq.Context()

    # Socket que recibe las solicitudes de clientes (facultades)
    frontend = context.socket(zmq.ROUTER)
    frontend.bind("tcp://*:6000")  # broker frontend

    # Socket que se comunica con los servidores backend
    backend = context.socket(zmq.ROUTER)
    backend.bind("tcp://*:7000")  # broker backend

    print("🔄 Broker enrutando entre frontend (6000) y backend (7000)...")

    zmq.proxy(frontend, backend)

if __name__ == "__main__":
    main()
