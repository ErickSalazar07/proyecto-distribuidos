#!/usr/bin/env python3
import subprocess
import time
import random
import signal
import sys

def arrancar_facultades(num_facultades, base_port, broker_ip, semestre):
    """
    Lanza num_facultades instancias de 'facultad.py', una por cada puerto 
    consecutivo a partir de base_port. Devuelve la lista de objetos Popen.
    """
    procesos = []
    for i in range(num_facultades):
        puerto = base_port + i
        nombre_fac = f"facultad{i+1}"
        cmd = [
            "python3", "facultad.py",
            "-n", nombre_fac,
            "-s", semestre,
            "-ip-p-b", broker_ip,
            "-puerto-escuchar", str(puerto)
        ]
        # Arrancamos la facultad en background
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procesos.append(p)
        print(f"→ Arrancada {nombre_fac} en puerto {puerto}")
    return procesos

def lanzar_programas(num_programas_por_facultad, num_facultades, base_port, semestre):
    """
    Por cada facultad (en total num_facultades), lanza num_programas_por_facultad 
    instancias de 'programa_academico.py', con parámetros aleatorios en rango,
    apuntando al puerto correspondiente de cada facultad.
    Devuelve la lista de objetos Popen.
    """
    procesos = []
    for i in range(num_facultades):
        puerto_fac = base_port + i
        for _ in range(num_programas_por_facultad):
            num_s = random.randint(7, 10)   # aulas entre 7 y 10
            num_l = random.randint(2, 4)    # laboratorios entre 2 y 4
            cmd = [
                "python3", "programa_academico.py",
                "-n", "programa",
                "-s", semestre,
                "-num-s", str(num_s),
                "-num-l", str(num_l),
                "-ip-p-f", f"localhost:{puerto_fac}"
            ]
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            procesos.append(p)
        print(f"   • Facultades {i+1} recibió {num_programas_por_facultad} solicitudes " 
              f"(puerto {puerto_fac})")
    return procesos

def main():
    # Parámetros generales
    NUM_FACULTADES = 10
    BASE_PORT       = 6000
    BROKER_IP       = "10.43.96.80:5513"
    SEMESTRE        = "05-2025"
    # Escenarios: total de procesos de 'programa_academico.py'
    ESCENARIOS = [50, 100, 200, 500]

    print("\n=== Orquestador de simulación de solicitudes ===\n")

    # 1) Arrancar todas las facultades (puertos 6000..6009)
    facultad_procs = arrancar_facultades(NUM_FACULTADES, BASE_PORT, BROKER_IP, SEMESTRE)

    # Pequeño delay para asegurarnos de que los servidores de facultades estén escuchando
    time.sleep(2)

    resultados = {}  # para guardar tiempos por escenario

    for total_programas in ESCENARIOS:
        # Calcular cuántos programas por facultad (entero)
        progs_por_fac = total_programas // NUM_FACULTADES

        print(f"\n--- Escenario: {total_programas} programas ("
              f"{progs_por_fac} por facultad) ---")

        # 2) Lanzar todos los programas simultáneamente y medir tiempo
        start = time.time()
        prog_procs = lanzar_programas(progs_por_fac, NUM_FACULTADES, BASE_PORT, SEMESTRE)

        # Esperar a que todos los procesos de 'programa_academico.py' terminen
        for p in prog_procs:
            p.wait()
        elapsed = time.time() - start

        resultados[total_programas] = elapsed
        print(f">> Tiempo transcurrido para {total_programas} procesos: {elapsed:.2f} segundos")

    # 3) Después de todos los escenarios, terminar procesos de facultad
    print("\nTerminando procesos de facultad …")
    for p in facultad_procs:
        try:
            # Enviar SIGINT primero para que cierren adecuadamente (si tienen handler)
            p.send_signal(signal.SIGINT)
            # Darles un momento para que cierren, si no, forzar
            time.sleep(0.2)
            if p.poll() is None:
                p.terminate()
        except Exception:
            pass

    print("\n=== Resultados finales ===")
    for total, t in resultados.items():
        print(f"  • {total:>3d} programas → {t:.2f} segundos")

    print("\n¡Simulación completada!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Ejecución interrumpida por el usuario.")
        sys.exit(1)
