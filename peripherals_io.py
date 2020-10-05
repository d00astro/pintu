import RPi.GPIO as GPIO
from signal import SIGINT, signal, pause
from time import sleep
from config import get_settings
import requests


config = get_settings()


def initialize():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(config.open_door_pin, GPIO.OUT)
    GPIO.setup(config.doorbell_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(
        config.doorbell_pin,
        GPIO.RISING,
        callback=doorbell_pressed_callback,
        bouncetime=2000
        )
    # If process is terminated, shut down gracefully
    signal(SIGINT, on_sigint)


def graceful_shutdown():
    try:
        GPIO.remove_event_detect(config.doorbell_pin)
        GPIO.cleanup()
        return True
    except Exception as ex:
        config.log.warn(f"Issuse while shutting peripherals down gracefully: {ex}")
    return False


def on_sigint(sig, frame):
    graceful_shutdown()


def open_door():
    try:
        for x in range(config.open_door_signal_repititions):
            GPIO.output(config.open_door_pin, True)
            sleep(config.open_door_signal_duration)
            GPIO.output(config.open_door_pin, False)
            sleep(config.open_door_signal_duration)
        config.log.info("Door is hopefully open!")
        return True
    except Exception as ex:
        config.log.error(f"Something bad happened when trying to open the door: {ex}")
        return False


def doorbell_pressed_callback(channel):
    try:
        config.log.info("Ding Dong! Someone pressed the door-bell")
        #TODO: webhooks go here
        requests.get(config.doorbell_url)
        config.log.info("Doorbell handler completed")
    except Exception as ex:
        config.log.error(f"Something bad happened when handling doorbell: {ex}")

# pause()
