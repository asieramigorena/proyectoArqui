import random

from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()


button = Button(16, pull_up=False, bounce_time=0.05)
ledr = LED(17)
ledv = LED(27)
eventos = queue.Queue()
R, V, A, N = range(4)
estado = N
puntuacion = 1
puntuaciones = []
combinaciones = []
respuesta = []

def inicio():
    for i in range(10):
        combinaciones[i] = random.randint(0, 1)

def seleccion(button):
    while True:
        button.wait_for_press()
        time1 = time.time()
        button.wait_for_release()
        time2 = time.time()
        #Larga = Verde // Corta = Roja
        eventos.put(0) if (time2 - time1) < 2 else eventos.put(1)

def comprobacion():
    global respuesta
    global puntuacion
    running = True
    while running:
        for i in range(puntuacion):
            actual = eventos.get()
            if actual != combinaciones[i]:
                running = False
                break
            else:
                respuesta.append(actual)
        puntuacion += 1

def juego():
    t_seleccion = threading.Thread(target=seleccion, args=(button,))
    t_logicaled = threading.Thread(target=logica_led, args=())
    t_seleccion.start(); t_logicaled.start()
    t_logicaled.join(); t_seleccion.join()

def logica_led():
    global estado
    while True:
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

if __name__ == '__main__':
    try:
        while True:
            inicio()


    except KeyboardInterrupt:
        print("\nTerminando ejecución, adios")
