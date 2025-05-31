import socket
import threading
import time
import random
import argparse
from multiprocessing import Process, Queue
import sys

# Configuración de recursos por facultad
AULAS_TOTALES = 30
LABORATORIOS_TOTALES = 15

def run_facultad_server(puerto_escuchar):
    aulas_disponibles = list(range(1, AULAS_TOTALES + 1))
    laboratorios_disponibles = list(range(1, LABORATORIOS_TOTALES + 1))
    lock = threading.Lock()

    def handle_client(conn):
        data = conn.recv(1024).decode()
        try:
            partes = data.split(';')
            num_aulas = int(partes[0].split('=')[1])
            num_labs = int(partes[1].split('=')[1])
        except:
            conn.send("rechazado".encode())
            conn.close()
            return

        with lock:
            if len(aulas_disponibles) >= num_aulas and len(laboratorios_disponibles) >= num_labs:
                aulas_asignadas = aulas_disponibles[:num_aulas]
                del aulas_disponibles[:num_aulas]
                labs_asignados = laboratorios_disponibles[:num_labs]
                del laboratorios_disponibles[:num_labs]
                conn.send(f"asignadas: {aulas_asignadas} aulas, {labs_asignados} labs".encode())
            else:
                conn.send("rechazado".encode())
        conn.close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', puerto_escuchar))
        s.listen()
        while True:
            conn, _ = s.accept()
            threading.Thread(target=handle_client, args=(conn,)).start()

def programa_academico(nombre, ip_p_f, result_queue):
    num_aulas = random.randint(7, 10)
    num_labs = random.randint(2, 4)
    
    try:
        ip, port = ip_p_f.split(':')
        port = int(port)
    except:
        result_queue.put((0.0, False))
        return

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    start_time = time.perf_counter()
    try:
        s.connect((ip, port))
        mensaje = f"aulas={num_aulas};laboratorios={num_labs}"
        s.send(mensaje.encode())
        respuesta = s.recv(1024).decode()
        end_time = time.perf_counter()
        duracion = end_time - start_time
        satisfecha = "rechazado" not in respuesta
        result_queue.put((duracion, satisfecha))
    except:
        result_queue.put((0.0, False))
    finally:
        s.close()

def main():
    # Configurar servidores
    puertos = [6000 + i for i in range(10)]
    servidores = []
    for puerto in puertos:
        p = Process(target=run_facultad_server, args=(puerto,))
        p.daemon = True
        p.start()
        servidores.append(p)
    
    time.sleep(1)  # Esperar que servidores inicien

    # Ejecutar clientes
    resultados = Queue()
    clientes = []
    for i in range(50):
        facultad_idx = i // 5
        puerto = puertos[facultad_idx]
        cliente = threading.Thread(
            target=programa_academico,
            args=(f"programa_{i}", f"localhost:{puerto}", resultados)
        )
        cliente.start()
        clientes.append(cliente)
    
    for cliente in clientes:
        cliente.join()
    
    # Recopilar resultados
    tiempos = []
    satisfechas = 0
    total_peticiones = 50
    
    while not resultados.empty():
        duracion, satisfecha = resultados.get()
        tiempos.append(duracion)
        if satisfecha:
            satisfechas += 1
    
    no_satisfechas = total_peticiones - satisfechas
    tiempo_medio = sum(tiempos) / total_peticiones
    tiempo_max = max(tiempos)
    
    print("\n" + "="*50)
    print("RESULTADOS DE LA SIMULACIÓN")
    print("="*50)
    print(f"Tiempo medio de respuesta: {tiempo_medio:.6f} segundos")
    print(f"Tiempo máximo de respuesta: {tiempo_max:.6f} segundos")
    print(f"Peticiones satisfechas: {satisfechas}")
    print(f"Peticiones no satisfechas: {no_satisfechas}")
    print("="*50)

if __name__ == '__main__':
    main()
