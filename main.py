from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process

button = Button(16, pull_up=False, bounce_time=0.05)
ledr = LED(17)
ledv = LED(27)
eventos = queue.Queue()
R, V, A, N = range(4)
estado = N
"""
def reaccion(button):
    while True:
        button.wait_for_press()
        tiempo1 = time.time()
        button.wait_for_release()
        tiempo2 = time.time()
        eventos.put()
"""

def seleccion(button, name):
    global estado
    while True:
        button.wait_for_press()
        time1 = time.time()
        button.wait_for_release()
        time2 = time.time()
        if time2 - time1 < 2:
            estado  = (estado + 1) % 4
        else:
            eventos.put(estado)

def led_inicio():
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
            t_iniciobtn = threading.Thread(target=seleccion, args=(button, "BTN"))
            t_inicioled = threading.Thread(target=led_inicio, args=())
            t_iniciobtn.start(); t_inicioled.start()
            seleccionado = eventos.get()
            print(seleccionado)
            t_inicioled.join(); t_inicioled.join()

    except KeyboardInterrupt:
        print("\nTerminando ejecución, adios")
