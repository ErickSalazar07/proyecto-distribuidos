#!/usr/bin/env python3
import subprocess
import time
import random
import signal
import sys

def arrancar_facultades(num_facultades, base_port, broker_ip, semestre):
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
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procesos.append(p)
        print(f"→ Arrancada {nombre_fac} en puerto {puerto}")
    return procesos

def lanzar_programas(num_programas_por_facultad, num_facultades, base_port, semestre):
    procesos = []
    tiempos_individuales = []

    for i in range(num_facultades):
        puerto_fac = base_port + i
        for _ in range(num_programas_por_facultad):
            num_s = random.randint(7, 10)
            num_l = random.randint(2, 4)
            cmd = [
                "python3", "programa_academico.py",
                "-n", "programa",
                "-s", semestre,
                "-num-s", str(num_s),
                "-num-l", str(num_l),
                "-ip-p-f", f"localhost:{puerto_fac}"
            ]

            inicio = time.time()
            # Usamos run() para medir el tiempo individual de cada proceso
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            procesos.append((p, inicio))

        print(f"   • Facultad {i+1} recibió {num_programas_por_facultad} solicitudes (puerto {puerto_fac})")

    # Esperar todos los procesos, midiendo tiempos de finalización
    for p, inicio in procesos:
        p.wait()
        fin = time.time()
        tiempos_individuales.append(fin - inicio)

    return tiempos_individuales

def main():
    NUM_FACULTADES = 10
    BASE_PORT = 6000
    BROKER_IP = "10.43.96.80:5553"
    SEMESTRE = "05-2025"
    ESCENARIOS = [50, 100, 200, 500]

    print("\n=== Orquestador de simulación de solicitudes ===\n")

    facultad_procs = arrancar_facultades(NUM_FACULTADES, BASE_PORT, BROKER_IP, SEMESTRE)
    time.sleep(2)  # Esperamos a que las facultades estén listas

    resultados = {}

    for total_programas in ESCENARIOS:
        progs_por_fac = total_programas // NUM_FACULTADES

        print(f"\n--- Escenario: {total_programas} programas ({progs_por_fac} por facultad) ---")

        start = time.time()
        tiempos_individuales = lanzar_programas(progs_por_fac, NUM_FACULTADES, BASE_PORT, SEMESTRE)
        total_elapsed = time.time() - start

        tiempo_medio = sum(tiempos_individuales) / len(tiempos_individuales)
        tiempo_max = max(tiempos_individuales)

        resultados[total_programas] = {
            "tiempo_total": total_elapsed,
            "tiempo_medio": tiempo_medio,
            "tiempo_max": tiempo_max,
            "programas_usados": total_programas,
            "facultades_usadas": NUM_FACULTADES
        }

        print(f">> Tiempo total: {total_elapsed:.2f} s")
        print(f">> Tiempo medio por programa: {tiempo_medio:.2f} s")
        print(f">> Tiempo máximo individual: {tiempo_max:.2f} s")

    # Finalizar procesos de facultades
    print("\nTerminando procesos de facultad …")
    for p in facultad_procs:
        try:
            p.send_signal(signal.SIGINT)
            time.sleep(0.2)
            if p.poll() is None:
                p.terminate()
        except Exception:
            pass

    print("\n=== Resultados finales por escenario ===")
    for total, datos in resultados.items():
        print(f"\nEscenario con {total} programas académicos:")
        print(f"  • Facultades utilizadas     : {datos['facultades_usadas']}")
        print(f"  • Tiempo total              : {datos['tiempo_total']:.2f} s")
        print(f"  • Tiempo medio por programa: {datos['tiempo_medio']:.2f} s")
        print(f"  • Tiempo máximo observado  : {datos['tiempo_max']:.2f} s")

    print("\n¡Simulación completada!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Ejecución interrumpida por el usuario.")
        sys.exit(1)
