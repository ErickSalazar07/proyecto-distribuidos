#!/usr/bin/env python3
import subprocess
import time
import random
import signal
import sys

def arrancar_facultades(num_facultades, base_port, broker_ip, semestre):
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
            "-ip-p-b", broker_ip,
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
                "proc": p,
                "start": start_time,
                "facultad": nombre_fac
            })
        print(f"   • Facultad '{nombre_fac}' (puerto {puerto_fac}) recibió "
              f"{num_programas_por_facultad} solicitudes.")
    return procesos_info

def main():
    # Parámetros generales
    NUM_FACULTADES = 10
    BASE_PORT       = 6000
    BROKER_IP       = "10.43.96.80:5553"
    SEMESTRE        = "05-2025"
    # Escenarios: total de procesos de 'programa_academico.py'
    ESCENARIOS = [50, 100, 200, 500]

    print("\n=== Orquestador de simulación de solicitudes (versión con métricas) ===\n")

    # 1) Arrancar todas las facultades (puertos 6000..6009)
    facultad_procs, lista_facultades = arrancar_facultades(
        NUM_FACULTADES, BASE_PORT, BROKER_IP, SEMESTRE
    )

    # Pequeño delay para asegurarnos de que los servidores de facultades estén escuchando
    time.sleep(2)

    resultados = {}  # para guardar tiempos totales por escenario

    for total_programas in ESCENARIOS:
        # Calcular cuántos programas por facultad (entero)
        progs_por_fac = total_programas // NUM_FACULTADES

        print(f"\n--- Escenario: {total_programas} programas totales "
              f"({progs_por_fac} por facultad) ---")

        # 2) Lanzar todos los programas simultáneamente y registrar info inicial
        procesos_info = lanzar_programas(
            progs_por_fac,
            NUM_FACULTADES,
            BASE_PORT,
            SEMESTRE,
            lista_facultades
        )

        total_lanzados = len(procesos_info)
        # Variables para ir registrando métricas:
        tiempos = []           # lista de tiempos individuales (float en segundos)
        codigos = []           # lista de exit codes (0 vs !=0)
        pendientes = procesos_info.copy()

        # 3) Esperar a que todos los procesos terminen (polling)
        while pendientes:
            time.sleep(0.05)  # evitamos busy-waiting excesivo
            para_eliminar = []
            ahora = time.time()
            for entry in pendientes:
                p = entry["proc"]
                if p.poll() is not None:
                    # Ya terminó; medir su tiempo de respuesta:
                    t_proc = ahora - entry["start"]
                    tiempos.append(t_proc)
                    codigos.append(p.returncode)
                    para_eliminar.append(entry)
            # Sacamos los que ya terminamos de la lista "pendientes"
            for e in para_eliminar:
                pendientes.remove(e)

        # 4) Calcular métricas
        if tiempos:
            tiempo_medio = sum(tiempos) / len(tiempos)
            tiempo_max   = max(tiempos)
        else:
            tiempo_medio = 0.0
            tiempo_max   = 0.0

        satisfechas    = sum(1 for c in codigos if c == 0)
        no_satisfechas = sum(1 for c in codigos if c != 0)

        # El tiempo total real del escenario (desde el primero que arrancó hasta el último que terminó)
        tiempo_primero = min(entry["start"] for entry in procesos_info)
        tiempo_ultimo  = max(entry["start"] + t for entry, t in zip(procesos_info, tiempos))
        tiempo_total   = tiempo_ultimo - tiempo_primero
        resultados[total_programas] = tiempo_total

        # 5) Imprimir todas las métricas del escenario
        print(f"\n  • Programas Académicos que se usaron: { total_lanzados }")
        print(f"  • Facultades que se usaron      : {', '.join(lista_facultades)}")
        print(f"  • Tiempo medio de respuesta     : {tiempo_medio:.2f} segundos")
        print(f"  • Tiempo máximo de respuesta    : {tiempo_max:.2f} segundos")
        print(f"  • Peticiones satisfechas         : {satisfechas}")
        print(f"  • Peticiones no satisfechas      : {no_satisfechas}")
        print(f"  • Tiempo total (del primero al último) = {tiempo_total:.2f} segundos\n")

    # 6) Después de todos los escenarios, terminar procesos de facultad
    print("Terminando procesos de facultad …")
    for p in facultad_procs:
        try:
            # Enviar SIGINT primero para que cierren adecuadamente (si tienen handler)
            p.send_signal(signal.SIGINT)
            time.sleep(0.2)
            if p.poll() is None:
                p.terminate()
        except Exception:
            pass

    # 7) Resumen final de tiempos totales por escenario
    print("\n=== Resumen final de tiempos totales ===")
    for total, t in resultados.items():
        print(f"  • {total:>3d} programas → {t:.2f} segundos")

    print("\n¡Simulación COMPLETADA con métricas!\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Ejecución interrumpida por el usuario.")
        sys.exit(1)

