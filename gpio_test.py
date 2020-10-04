import RPi.GPIO as GPIO
from sys import exit
from signal import SIGINT, signal, pause
from time import sleep

open_door_pin = 13  # Physical 13 -> BCM 27
doorbell_pin = 11   # Physical 11  -> BCM 17

signal_duration = 0.3
repetitions = 1

GPIO.setmode(GPIO.BOARD)
GPIO.setup(open_door_pin, GPIO.OUT)
GPIO.setup(doorbell_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


def open_door():
    try:
        for x in range(repetitions):
            GPIO.output(open_door_pin, True)
            sleep(signal_duration)
            GPIO.output(open_door_pin, False)
            sleep(signal_duration)
        print("Door is hopefully open!")
        return True
    except Exception as ex:
        print(f"Ouff something bad happened: {ex}")


def doorbell_pressed_callback(channel):
    print("Ding Dong!")
    open_door()
    print("")


def signal_handler(sig, frame):
    GPIO.cleanup()
    exit(0)


GPIO.add_event_detect(
    doorbell_pin,
    GPIO.RISING,
    callback=doorbell_pressed_callback,
    bouncetime=2000
    )

signal(SIGINT, signal_handler)
pause()
