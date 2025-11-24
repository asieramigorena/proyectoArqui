from gpiozero import LED, Button
import threading, time, queue
from multiprocessing import Process

button = Button(16, pull_up=False, bounce_time=0.05)
ledr = LED(17)
ledv = LED(27)
eventos = queue.Queue()

def BTN_pulling(button):
    while True:
        button.wait_for_press()
        tiempo1 = time.time()
        button.wait_for_release()
        tiempo2 = time.time()
        eventos.put()


def led_worker():
    while True:
        time.sleep(1)


if __name__ == '__main__':
    #t_btn = threading.Thread(target=BTN_pulling, args=(button,), daemon=True)
    #t_led = threading.Thread(target=led_worker, daemon=True)
    #t_led.start(); t_btn.start()
    p_btn = Process(target=BTN_pulling, args=(button,))
    p_ledv = Process(target=led_worker(), args=())
