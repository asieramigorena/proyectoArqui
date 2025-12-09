import random

from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process, Queue
from fastapi import FastAPI
from datetime import datetime

colaApi = Queue()
pApi, pJuego = None, None

eventos = queue.Queue()
r, v, a, n = range(4)
estado = n
puntuacion = 1
puntuaciones = [[], []]


def juego():
    button = Button(16, pull_up=False, bounce_time=0.05)
    ledr = LED(17)
    ledv = LED(27)
    otra_vez = True
    while otra_vez:
        combinaciones = []
        for i in range(10):
            combinaciones[i] = random.randint(0, 1)

        evento = threading.Event()

        t_seleccion = threading.Thread(target=seleccion, args=(button, evento), daemon=True)
        t_comprobacion = threading.Thread(target=comprobacion, args=(combinaciones,), daemon=True)
        t_logica_led = threading.Thread(target=logica_led, args=(ledr, ledv, evento), daemon=True)

        t_seleccion.start()
        t_logica_led.start()
        t_comprobacion.start()

        t_comprobacion.join()

        try:
            ultimo = eventos.get()
            otra_vez = True if ultimo == 1 else False
        except queue.Empty:
            otra_vez = False

        evento.set()
        t_logica_led.join()
        t_seleccion.join()

        ledr.off()
        ledv.off()
        ledr.close()
        ledv.close()


def seleccion(button, evento):
    while not evento.is_set():
        button.wait_for_press()
        time1 = time.time()
        button.wait_for_release()
        time2 = time.time()
        # Larga = Verde // Corta = Roja
        eventos.put(0) if (time2 - time1) < 2 else eventos.put(1)


def comprobacion(combinaciones):
    global puntuacion, estado
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
            actual = eventos.get()
            if actual != combinaciones[i]:
                running = False
                break
        if running:
            puntuacion += 1
            if puntuacion == 10:
                print("Has ganado")
                running = False
    puntuaciones[1].append(puntuacion)
    puntuaciones[0].append(datetime.now().strftime("%d/%m/%Y %H:%M:%S"))


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


def servidor():
    global puntuacion
    app = FastAPI()
    while True:
        print("test")
        time.sleep(1)


def main():
    global p_api, p_juego
    try:
        while True:
            p_api = Process(target=servidor)
            p_juego = Process(target=juego)

    except KeyboardInterrupt:
        print("\nTerminando ejecución, adios")
        p_api.join()
        p_juego.join()

if __name__ == '__main__':
    main()
