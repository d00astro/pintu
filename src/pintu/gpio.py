# -*- coding: utf-8 -*-
"""
GPIO and peripherals handling.
"""
__author__ = "Anders Åström"
__contact__ = "anders@astrom.sg"
__copyright__ = "2022, Anders Åström"
__licence__ = """The MIT License
Copyright © 2022 Anders Åström

Permission is hereby granted, free of charge, to any person obtaining a copy of this
 software and associated documentation files (the “Software”), to deal in the Software
 without restriction, including without limitation the rights to use, copy, modify,
 merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
 permit persons to whom the Software is furnished to do so, subject to the following
 conditions:

The above copyright notice and this permission notice shall be included in all copies
 or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
 PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
 CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
 OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import collections
import enum
import functools
import logging
import signal
from typing import Callable

import redis
import RPi.GPIO as GPIO

import pintu
import pintu.record
import pintu.util

log = logging.getLogger(__name__)


@functools.lru_cache
def redis_connection():
    return redis.Redis(
        host=pintu.config.redis_host, port=pintu.config.redis_port
    )


# TODO: Replace with proper Event logic:
def record_it():
    now = pintu.util.now()
    pintu.record.record(
        redis_connection(),
        pintu.config.camera_name,
        start_time=now - pintu.config.pre_event_recording_duration,
        end_time=now + pintu.config.post_event_recording_duration,
    )


class PinState(int, enum.Enum):
    """
    Pin-state representation.
    """

    Low = 0
    High = 1

    @property
    def pull_up_down(self):
        return GPIO.PUD_DOWN if self else GPIO.PUD_UP

    @property
    def transition(self):
        return GPIO.RISING if self else GPIO.FALLING

    @property
    def invert(self):
        return PinState.Low if self else PinState.High

    def __str__(self) -> str:
        return "HIGH" if self else "LOW"


def on_doorbell_event(state: bool):
    """
    Handler for doorbell events

    :param state:
        `True` for events when doorbell is pressed, `False` for when it is released.
    """
    if state:
        log.info("Ding! Someone pressed the door-bell!")
        return
    log.info("Dong! Someone released the door-bell!")

    # TODO: Replace with proper Event logic:
    record_it()


def on_door_opened_event(state: bool):
    """
    Handler for door sensor events.

    :param state:
        `True` for events when door is opened, `False` for when it is closed.
    """
    if state:
        log.info("Hello! Someone opened the door!")
        return
    log.info("Someone closed the door!")

    # TODO: Replace with proper Event logic:
    record_it()


def on_unlocked_event(state: bool):
    """
    Handler for lock sensor events.

    :param state:
        `True` for events when unlocked, `False` for when it is locked.
    """
    if state:
        log.info("Clink! Someone unlocked the door!")
        return
    log.info("Someone locked the door!")

    # TODO: Replace with proper Event logic:
    record_it()


PinEvent = collections.namedtuple(
    "PinEvent", ["pin_number", "trigger_pinstate", "debounce_ms", "handler"]
)

_PIN_EVENTS = {
    "doorbell pressed": PinEvent(
        pintu.config.doorbell_pin,
        PinState(pintu.config.doorbell_pressed_pinstate),
        pintu.config.doorbell_debounce_ms,
        on_doorbell_event,
    )
    if pintu.config.doorbell_pin is not None
    else None,
    "door opened": PinEvent(
        pintu.config.door_sensor_pin,
        PinState(pintu.config.door_sensor_opened_pinstate),
        pintu.config.door_sensor_debounce_ms,
        on_door_opened_event,
    )
    if pintu.config.door_sensor_pin is not None
    else None,
    "door unlocked": PinEvent(
        pintu.config.lock_sensor_pin,
        PinState(pintu.config.lock_sensor_unlocked_pinstate),
        pintu.config.lock_sensor_debounce_ms,
        on_unlocked_event,
    )
    if pintu.config.lock_sensor_pin is not None
    else None,
}
"""Input / sensor pins configuration, grouped by function."""


def handle(
    pin_event: PinEvent,
    handler: Callable[[bool], None],
):
    """
    Pin event handler wrapper. Creates a handler that provides the state of the pin,
    instead of the pin number.

    :param pin_event:
        Configuration for a pin event.

    :param handler:
        Handler to call
    """

    def wrapper(channel: int):
        handler(bool(pin_event.trigger_pinstate) == bool(GPIO.input(channel)))

    return wrapper


def initialize():
    """
    Initialize GPIOs
    """
    # Set pin_mode
    GPIO.setmode(
        GPIO.BCM if pintu.config.use_bcm_pin_numbering else GPIO.BOARD
    )

    # Configure unlock actuation, if specified
    if pintu.config.door_unlock_pin is not None:
        GPIO.setup(
            pintu.config.door_unlock_pin,
            GPIO.OUT,
        )

    for event_name, pin_event in _PIN_EVENTS.items():
        if pin_event is not None:
            log.info(
                f"Configuring event handler for '{event_name}', triggered when "
                f"pin {pin_event.pin_number} goes {pin_event.trigger_pinstate}."
            )
            GPIO.setup(
                pin_event.pin_number,
                GPIO.IN,
                pull_up_down=pin_event.trigger_pinstate.pull_up_down,
            )
            GPIO.add_event_detect(
                pin_event.pin_number,
                # PinState(pintu.config.doorbell_pressed_pinstate).transition,
                GPIO.BOTH,
                callback=handle(pin_event, pin_event.handler),
                bouncetime=pin_event.debounce_ms,
            )
    signal.signal(signal.SIGINT, on_sigint)


def graceful_shutdown():
    """Clean up GPIOs"""
    for event_name, pin_event in _PIN_EVENTS.items():
        if pin_event is not None:
            log.info(
                f"Removing event handler for '{event_name}', triggered when "
                f"pin {pin_event.pin_number} goes {pin_event.trigger_pinstate}."
            )
        try:
            GPIO.remove_event_detect(pin_event.pin_number)
        except (ValueError, TypeError) as ex:
            log.warn(
                f"Error removing '{event_name}' handler on pin {pin_event.pin_number}: "
                f"{ex}"
            )

    GPIO.cleanup()


def on_sigint(sig, frame):
    """Shutdown handling"""
    graceful_shutdown()


def is_door_open() -> bool:
    """
    Check the door sensor.

    :return:
        True if door is open, False otherwise.
    """
    return bool(GPIO.input(pintu.config.door_sensor_pin)) == bool(
        pintu.config.door_sensor_opened_pinstate
    )


def is_door_unlocked() -> bool:
    """
    Check the lock sensor.

    :return:
        True if door is unlocked, False otherwise.
    """
    return bool(GPIO.input(pintu.config.lock_sensor_pin)) == bool(
        pintu.config.lock_sensor_unlocked_pinstate
    )


def unlock_door():
    """
    Unlock the door.
    """
    log.info("Unlocking door.")
    unlock_signal = PinState(pintu.config.door_unlock_signal_pinstate)
    GPIO.output(pintu.config.door_unlock_pin, unlock_signal)


def lock_door():
    """
    Lock the door.
    """
    log.info("Locking door.")
    unlock_signal = PinState(pintu.config.door_unlock_signal_pinstate)
    GPIO.output(pintu.config.door_unlock_pin, unlock_signal.invert)


def open_door():
    """
    Open the door

    Not yet implemented. Maybe you have such a fancy door, but I don't.

    :raises NotImplementedError:
        This feature is not implemented.
    """
    raise NotImplementedError("Open Door function not implemmented")


def close_door():
    """
    Close the door

    Not yet implemented. Maybe you have such a fancy door, but I don't.

    :raises NotImplementedError:
        This feature is not implemented.
    """
    raise NotImplementedError("Close Door function not implemmented")
