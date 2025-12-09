import random

from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process, Queue
from fastapi import FastAPI
from datetime import datetime
import uvicorn
import sqlite3

colaApi = Queue()
p_api = None
p_juego = None

eventos = queue.Queue()
r, v, a, n = range(4)
estado = n
puntuacion = 1
semaforo_in = threading.Semaphore(0)


def juego(cola_puntuacion):
    global estado
    button = Button(16, pull_up=False, bounce_time=0.05)
    ledr = LED(17)
    ledv = LED(27)
    otra_vez = True
    try:

        while otra_vez:
            cola_puntuacion.put(1)
            combinaciones = [random.randint(0, 1) for _ in range(10)]

            evento = threading.Event()

            t_seleccion = threading.Thread(target=seleccion, args=(button, evento), daemon=True)
            t_comprobacion = threading.Thread(target=comprobacion, args=(combinaciones, cola_puntuacion),
                                          daemon=True)
            t_logica_led = threading.Thread(target=logica_led, args=(ledr, ledv, evento), daemon=True)

            t_seleccion.start()
            t_logica_led.start()
            t_comprobacion.start()

            t_comprobacion.join()

            try:
                estado = a
                semaforo_in.release()
                ultimo = eventos.get()
                otra_vez = True if ultimo == 0 else False
                estado = n

                if otra_vez:
                    time.sleep(0.7)  # Pausa para ver el LED del principio (fix)
                    
            except queue.Empty:
                otra_vez = False

            evento.set()
            t_logica_led.join()
            semaforo_in.release()
            t_seleccion.join()

    finally:
        ledr.off()
        ledv.off()
        ledr.close()
        ledv.close()
        button.close()


def seleccion(button, evento):
    while not evento.is_set():
        semaforo_in.acquire()
        if evento.is_set():
            break
        button.wait_for_press()
        time1 = time.time()
        button.wait_for_release()
        time2 = time.time()
        # Larga = Verde // Corta = Roja
        eventos.put(0) if (time2 - time1) < 2 else eventos.put(1)


def comprobacion(combinaciones, cola_puntuacion):
    global estado
    puntuacion = 1
    running = True
    while running:
        for i in range(puntuacion):
            if combinaciones[i] == 0:
                estado = r
                time.sleep(0.3)
            else:
                estado = v
                time.sleep(0.3)
            estado = n
            time.sleep(0.3)
        for i in range(puntuacion):
            semaforo_in.release()
            actual = eventos.get()
            if actual == combinaciones[i]:
                print("✔️ Correcto")
            else:
                print("❌ Incorrecto")
                running = False
                break
        if running:
            puntuacion += 1
            cola_puntuacion.put(puntuacion)
            if puntuacion == 5:
                print("Has ganado")
                running = False

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    cola_puntuacion.put(("Terminado", fecha, puntuacion))
    guardar_resultado(fecha, puntuacion)  # <-- Guardar en DB

def logica_led(ledr, ledv, evento):
    global estado
    while not evento.is_set():
        match estado:
            case 0:
                ledr.on()
                ledv.off()
            case 1:
                ledv.on()
                ledr.off()
            case 2:
                ledv.on()
                ledr.on()
            case 3:
                ledr.off()
                ledv.off()
            case _:
                print("Error en led_inicio")


def servidor(puntuaciones, cola_puntuacion):
    app = FastAPI()
    actual = 0

    @app.get("/puntuacion")
    def get_puntuacion():
        return {"actual": actual, "historial": obtener_historial()}

    # esto es un hilo para procesar la cola en segundo plano
    def procesar_cola():
        nonlocal actual
        while True:
            try:
                mensaje = cola_puntuacion.get_nowait()
                if isinstance(mensaje, tuple) and mensaje[0] == "Terminado":
                    _, fecha, puntuacion = mensaje
                    puntuaciones[0].append(fecha)
                    puntuaciones[1].append(puntuacion)
                else:
                    actual = mensaje
            except queue.Empty:
                pass
            time.sleep(0.1)
            
    threading.Thread(target=procesar_cola, daemon=True).start()

    # Ejecutar FastAPI con uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

def crear_db():
    conn = sqlite3.connect("historial_juego.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historial (
        fecha TEXT PRIMARY KEY,
        puntuacion INTEGER)
    """)
    conn.commit()
    conn.close()

def guardar_resultado(fecha, puntuacion):
    conn = sqlite3.connect("historial_juego.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO historial (fecha, puntuacion) VALUES (?, ?)", (fecha, puntuacion))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"Registro con fecha {fecha} ya existe")
    finally:
        conn.close()

def obtener_historial():
    conn = sqlite3.connect("historial_juego.db")
    cursor = conn.cursor()
    cursor.execute("SELECT fecha, puntuacion FROM historial ORDER BY fecha")
    filas = cursor.fetchall()
    conn.close()
    fechas, puntuaciones = zip(*filas) if filas else ([], [])
    return {"fechas": list(fechas), "puntuaciones": list(puntuaciones)}


def main():
    global p_api, p_juego
    crear_db() 
    puntuaciones = [[], []]
    cola_puntuacion = Queue()
    try:
        p_api = Process(target=servidor, args=(puntuaciones, cola_puntuacion))
        p_juego = Process(target=juego, args=(cola_puntuacion,))
        p_api.start()
        p_juego.start()

        p_api.join()
        p_juego.join()

    except KeyboardInterrupt:
        print("\nTerminando ejecución, adios")
        if p_api and p_api.is_alive():
            p_api.terminate()
            p_api.join()
        if p_juego and p_juego.is_alive():
            p_juego.terminate()
            p_juego.join()


if __name__ == '__main__':
    main()
