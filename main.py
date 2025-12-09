import random

from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process, Queue, Manager
from fastapi import FastAPI
from datetime import datetime

colaApi = Queue()
p_api = None
p_juego = None

eventos = queue.Queue()
r, v, a, n = range(4)
estado = n
puntuacion = 1
semaforo_in = threading.Semaphore(0)


def juego(puntuaciones, cola_puntuacion):
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
            t_comprobacion = threading.Thread(target=comprobacion, args=(combinaciones, puntuaciones, cola_puntuacion),
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
                otra_vez = True if ultimo == 1 else False
                estado = n
            except queue.Empty:
                otra_vez = False

            evento.set()
            t_logica_led.join()
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


def comprobacion(combinaciones, puntuaciones, cola_puntuacion):
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
            if actual != combinaciones[i]:
                running = False
                break
        if running:
            puntuacion += 1
            cola_puntuacion.put(puntuacion)
            if puntuacion == 10:
                print("Has ganado")
                running = False

    fechas = [f for f in puntuaciones[0]]
    puntos = [p for p in puntuaciones[1]]
    fechas.append(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    puntos.append(puntuacion)
    puntuaciones[1] = fechas
    puntuaciones[0] = puntos


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
    while True:
        try:
            actual = cola_puntuacion.get_nowait()
        except:
            pass
        print(f"Actual: {actual}")
        time.sleep(1)


def main():
    global p_api, p_juego
    manager = Manager()
    puntuaciones = manager.list([manager.list(), manager.list()])
    cola_puntuacion = Queue()
    try:
        p_api = Process(target=servidor, args=(puntuaciones, cola_puntuacion))
        p_juego = Process(target=juego, args=(puntuaciones, cola_puntuacion))
        # p_api.start()
        p_juego.start()

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
