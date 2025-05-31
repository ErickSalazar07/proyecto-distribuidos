#!/usr/bin/env python3
import subprocess
import time
import random
import signal
import sys

def arrancar_facultades(num_facultades, base_port, semestre):
    """
    Lanza num_facultades instancias de 'facultad.py', una por cada puerto
    consecutivo a partir de base_port. Devuelve la lista de objetos Popen
    y también la lista de nombres de facultades.
    """
    procesos = []
    nombres = []
    for i in range(num_facultades):
        puerto = base_port + i
        nombre_fac = f"facultad{i+1}"
        nombres.append(nombre_fac)
        cmd = [
            "python3", "facultad.py",
            "-n", nombre_fac,
            "-s", semestre,
            "-ip-p-b", "IGNORADO",           # Ojo: en este ejemplo no se usa
            "-puerto-escuchar", str(puerto)
        ]
        # Arrancamos la facultad en background (silenciamos salida)
        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        procesos.append(p)
        print(f"→ Arrancada {nombre_fac} en puerto {puerto}")
    return procesos, nombres

def lanzar_programas(num_programas_por_facultad, num_facultades, base_port, semestre, facultades):
    """
    Por cada facultad (num_facultades), lanza num_programas_por_facultad
    instancias de 'programa_academico.py', con parámetros aleatorios en rango,
    apuntando al puerto correspondiente de cada facultad.
    Devuelve una lista de diccionarios, cada uno con:
      - 'proc': el objeto Popen
      - 'start': timestamp de inicio
      - 'facultad': nombre de la facultad a la que apunta
      # 'end' se agregará cuando termine cada proceso
    """
    procesos_info = []
    for i in range(num_facultades):
        puerto_fac = base_port + i
        nombre_fac = facultades[i]
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
            start_time = time.time()
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            procesos_info.append({
                "proc":     p,
                "start":    start_time,
                "facultad": nombre_fac,
            })
        print(f"   • Facultad '{nombre_fac}' (puerto {puerto_fac}) recibió "
              f"{num_programas_por_facultad} solicitudes.")
    return procesos_info

def main():
    # Parámetros generales
    NUM_FACULTADES = 10
    BASE_PORT       = 6000
    SEMESTRE        = "05-2025"

    # Solo un escenario: 50 procesos en total → 5 por facultad
    TOTAL_PROGRAMAS = 50
    PROGS_POR_FAC   = TOTAL_PROGRAMAS // NUM_FACULTADES  # = 5

    print("\n=== Orquestador: escenario único de 50 procesos ===\n")

    # 1) Arrancar todas las facultades (puertos 6000..6009)
    facultad_procs, lista_facultades = arrancar_facultades(
        NUM_FACULTADES, BASE_PORT, SEMESTRE
    )

    # Pequeño delay para asegurarnos de que los servidores de facultades estén escuchando
    time.sleep(2)

    print(f"\n--- Escenario: {TOTAL_PROGRAMAS} procesos totales "
          f"({PROGS_POR_FAC} por facultad) ---")

    # 2) Lanzar todos los programas simultáneamente y registrar info inicial
    procesos_info = lanzar_programas(
        PROGS_POR_FAC,
        NUM_FACULTADES,
        BASE_PORT,
        SEMESTRE,
        lista_facultades
    )

    total_lanzados = len(procesos_info)
    codigos = []            # lista de exit codes (0 vs !=0)
    pendientes = procesos_info.copy()

    # 3) Esperar a que todos los procesos terminen (polling)
    while pendientes:
        time.sleep(0.05)  # evitamos busy-waiting excesivo
        para_eliminar = []
        ahora = time.time()
        for entry in pendientes:
            p = entry["proc"]
            if p.poll() is not None:
                # El proceso terminó; registramos su timestamp de finalización
                entry["end"] = ahora
                entry["duracion"] = entry["end"] - entry["start"]
                codigos.append(p.returncode)
                para_eliminar.append(entry)
        for e in para_eliminar:
            pendientes.remove(e)

    # 4) Calcular métricas individuales
    duraciones = [entry["duracion"] for entry in procesos_info]
    if duraciones:
        tiempo_medio = sum(duraciones) / len(duraciones)
        tiempo_max   = max(duraciones)
    else:
        tiempo_medio = 0.0
        tiempo_max   = 0.0

    satisfechas    = sum(1 for c in codigos if c == 0)
    no_satisfechas = sum(1 for c in codigos if c != 0)

    tiempo_primero = min(entry["start"] for entry in procesos_info)
    tiempo_ultimo  = max(entry["end"]   for entry in procesos_info)
    tiempo_total   = tiempo_ultimo - tiempo_primero

    # 5) Imprimir métricas del escenario
    print(f"\n  • Programas Académicos que se usaron : { total_lanzados }")
    print(f"  • Facultades que se usaron          : {', '.join(lista_facultades)}")
    print(f"  • Tiempo medio de respuesta         : {tiempo_medio:.2f} segundos")
    print(f"  • Tiempo máximo de respuesta        : {tiempo_max:.2f} segundos")
    print(f"  • Peticiones satisfechas             : {satisfechas}")
    print(f"  • Peticiones no satisfechas          : {no_satisfechas}")
    print(f"  • Tiempo total (del primero al último) = {tiempo_total:.2f} segundos\n")

    # 6) Después del escenario, terminar procesos de facultad
    print("Terminando procesos de facultad …")
    for p in facultad_procs:
        try:
            # Enviar SIGINT para que cierren adecuadamente (si tienen handler)
            p.send_signal(signal.SIGINT)
            time.sleep(0.2)
            if p.poll() is None:
                p.terminate()
        except Exception:
            pass

    print("\n¡Simulación del escenario de 50 procesos COMPLETADA!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Ejecución interrumpida por el usuario.")
        sys.exit(1)
