import subprocess
import random
import time
import os
import matplotlib.pyplot as plt

# Configuración
FACULTADES = 10
PROGRAMAS_POR_FACULTAD = 5
PUERTO_BASE = 6000

# Limpiar archivo de resultados
if os.path.exists("resultados.txt"):
    os.remove("resultados.txt")

# Iniciar facultades
facultades_procs = []
for i in range(FACULTADES):
    puerto = PUERTO_BASE + i
    cmd = [
        "python", "facultad.py",
        "-n", f"facultad_{i}",
        "-s", "05-2025",
        "-ip-p-b", "localhost:5553",
        "-puerto-escuchar", str(puerto)
    ]
    p = subprocess.Popen(cmd)
    facultades_procs.append(p)

# Esperar que facultades inicien
time.sleep(2)

# Iniciar programas académicos
programas_procs = []
for i in range(FACULTADES):
    for j in range(PROGRAMAS_POR_FACULTAD):
        puerto = PUERTO_BASE + i
        num_salones = random.randint(7, 10)
        num_labs = random.randint(2, 4)
        cmd = [
            "python", "programa_academico.py",
            "-n", f"programa_{i}_{j}",
            "-s", "05-2025",
            "-num-s", str(num_salones),
            "-num-l", str(num_labs),
            "-ip-p-f", f"localhost:{puerto}"
        ]
        p = subprocess.Popen(cmd)
        programas_procs.append(p)

# Esperar que todos los programas terminen
for p in programas_procs:
    p.wait()

# Terminar facultades
for p in facultades_procs:
    p.terminate()

# Procesar resultados
def procesar_resultados():
    tiempos = []
    satisfechas = 0
    total = 0
    
    if not os.path.exists("resultados.txt"):
        print("No se encontró el archivo de resultados")
        return
    
    with open("resultados.txt", "r") as f:
        for line in f:
            partes = line.strip().split(',')
            if len(partes) == 2:
                tiempo = float(partes[0])
                satisfecha = partes[1] == "True"
                tiempos.append(tiempo)
                total += 1
                if satisfecha:
                    satisfechas += 1
    
    no_satisfechas = total - satisfechas
    
    if total > 0:
        tiempo_medio = sum(tiempos) / total
        tiempo_max = max(tiempos)
    else:
        tiempo_medio = 0
        tiempo_max = 0
    
    print("\n" + "="*50)
    print("RESULTADOS DE LA SIMULACIÓN")
    print("="*50)
    print(f"Total de peticiones: {total}")
    print(f"Tiempo medio de respuesta: {tiempo_medio:.6f} segundos")
    print(f"Tiempo máximo de respuesta: {tiempo_max:.6f} segundos")
    print(f"Peticiones satisfechas: {satisfechas}")
    print(f"Peticiones no satisfechas: {no_satisfechas}")
    print("="*50)
    
    # Gráfico de tiempos
    plt.figure(figsize=(10, 6))
    plt.plot(tiempos, 'o-')
    plt.axhline(y=tiempo_medio, color='r', linestyle='--', label=f'Tiempo medio: {tiempo_medio:.4f}s')
    plt.title('Tiempos de Respuesta de los Programas Académicos')
    plt.xlabel('Número de Programa')
    plt.ylabel('Tiempo (segundos)')
    plt.legend()
    plt.grid(True)
    plt.savefig('tiempos_respuesta.png')
    plt.show()

procesar_resultados()
