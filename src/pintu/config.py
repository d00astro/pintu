# -*- coding: utf-8 -*-
"""
Configuration and paramerers
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
import datetime
import functools
import logging.config
import pathlib

import configargparse
import packaging.version
import pydantic

import pintu.default

argparser = configargparse.ArgParser(
    default_config_files=pintu.default.CONFIG_FILES,
    auto_env_var_prefix="PINTU_",
)
argparser.add_argument(
    "-c",
    "--config",
    env_var="CONFIG",
    is_config_file=True,
    help="Configuration file path.",
)
argparser.add_argument(
    "--log_config_file",
    env_var="LOG_CONFIG_FILE",
    default=pintu.default.LOG_CONFIG_FILE,
    type=pathlib.Path,
    help="Base directory for logs.",
)
argparser.add_argument(
    "--recordings_dir",
    env_var="RECORDINGS_DIR",
    default=pintu.default.RECORDINGS_DIR,
    type=pathlib.Path,
    help="Video recordings directory.",
)
argparser.add_argument(
    "--events_file",
    env_var="EVENTS_FILE",
    default=pintu.default.EVENTS_FILE,
    type=pathlib.Path,
    help="Event handler JSON file.",
)


# # Redis
argparser.add_argument(
    "--redis_host",
    env_var="REDIS_HOST",
    default=pintu.default.REDIS_HOST,
    type=str,
    help="Hostname or IP of the redis server.",
)
argparser.add_argument(
    "--redis_port",
    env_var="REDIS_PORT",
    default=pintu.default.REDIS_PORT,
    type=str,
    help="Port of the redis server.",
)

# # API
argparser.add_argument(
    "-p",
    "--api_port",
    env_var="API_LISTEN_PORT",
    default=pintu.default.API_LISTEN_PORT,
    type=int,
    help="Pintu API listen port",
)
argparser.add_argument(
    "--api_scheme",
    env_var="API_SCHEME",
    default=pintu.default.API_SCHEME,
    type=str,
    help="API protocol scheme ('http' or 'https').",
)
argparser.add_argument(
    "--api_net_location",
    env_var="API_NET_LOCATION",
    default=pintu.default.API_NET_LOCATION,
    type=str,
    help="Public address or ip.",
)
argparser.add_argument(
    "--api_route_prefix",
    env_var="API_ROUTE_PREFIX",
    default=pintu.default.API_ROUTE_PREFIX,
    type=str,
    help="API endpoint prefix.",
)


# # GPIO / PERIPHERALS
argparser.add_argument(
    "--use_bcm_pin_numbering",
    env_var="USE_BCM_PIN_NUMBERING",
    default=pintu.default.USE_BCM_PIN_NUMBERING,
    type=bool,
    help="""If set, pin numbers refer to BCM logical pin numbering
    instead of the physical board numbering.""",
)

# Doorbell sensing / input
argparser.add_argument(
    "--doorbell_pin",
    env_var="DOORBELL_PIN",
    default=pintu.default.DOORBELL_PIN,
    type=int,
    help="GPIO pin number for the doorbell input.",
)
argparser.add_argument(
    "--doorbell_pressed_pinstate",
    env_var="DOORBELL_PRESSED_PINSTATE",
    default=pintu.default.DOORBELL_PRESSED_PINSTATE,
    type=int,
    help="Pinstate (High/1 or Low/0) when doorbell is pressed.",
)
argparser.add_argument(
    "--doorbell_debounce_ms",
    env_var="DOORBELL_DEBOUNCE_MS",
    default=pintu.default.DOORBELL_DEBOUNCE_MS,
    type=int,
    help="Treat signals or jitter that occur within this time-span as a single press.",
)

# Door open/closed sensing / input
argparser.add_argument(
    "--door_sensor_pin",
    env_var="DOOR_SENSOR_PIN",
    default=pintu.default.DOOR_SENSOR_PIN,
    type=int,
    help="GPIO pin number for a sensor detecting if the door is open or closed.",
)
argparser.add_argument(
    "--door_sensor_opened_pinstate",
    env_var="DOOR_SENSOR_OPENED_PINSTATE",
    default=pintu.default.DOOR_SENSOR_OPENED_PINSTATE,
    type=int,
    help="Pinstate (High/1 or Low/0) when door is opened.",
)
argparser.add_argument(
    "--door_sensor_debounce_ms",
    env_var="DOOR_SENSOR_DEBOUNCE_MS",
    default=pintu.default.DOORBELL_DEBOUNCE_MS,
    type=int,
    help="Treat signals or jitter that occur within this time-span as a single press.",
)

# Door lock actuation / output
argparser.add_argument(
    "--door_unlock_pin",
    env_var="DOOR_UNLOCK_PIN",
    default=pintu.default.DOOR_UNLOCK_PIN,
    type=int,
    help="GPIO pin number for the door unlocking output.",
)
argparser.add_argument(
    "--door_unlock_signal_pinstate",
    env_var="DOOR_UNLOCK_SIGNAL_PINSTATE",
    default=pintu.default.DOOR_UNLOCK_SIGNAL_PINSTATE,
    type=int,
    help="Pinstate (High/1 or Low/0) to emit to unlock the door.",
)
argparser.add_argument(
    "--door_unlock_signal_duration",
    env_var="DOOR_UNLOCK_SIGNAL_DURATION",
    default=pintu.default.DOOR_UNLOCK_SIGNAL_DURATION,
    type=datetime.timedelta,
    help="GPIO pin number for the doorbell input.",
)

# Door lock sensing / input
argparser.add(
    "--lock_sensor_pin",
    env_var="LOCK_SENSOR_PIN",
    default=pintu.default.LOCK_SENSOR_PIN,
    type=int,
    help="GPIO pin number for the sensor detecting if the lock is locked or unlocked.",
)
argparser.add_argument(
    "--lock_sensor_unlocked_pinstate",
    env_var="LOCK_SENSOR_UNLOCKED_PINSTATE",
    default=pintu.default.LOCK_SENSOR_UNLOCKED_PINSTATE,
    type=int,
    help="Pinstate (High/1 or Low/0) when door is unlocked.",
)
argparser.add_argument(
    "--lock_sensor_debounce_ms",
    env_var="LOCK_SENSOR_DEBOUNCE_MS",
    default=pintu.default.DOORBELL_DEBOUNCE_MS,
    type=int,
    help="Treat signals or jitter that occur within this time-span as a single press.",
)


# # Image Processing
argparser.add_argument(
    "-v",
    "--video",
    env_var="VERBOSITY",
    default=pintu.default.VIDEO,
    type=str,
    help="Video input.",
)
argparser.add_argument(
    "--retention",
    env_var="RETENTION",
    default=pintu.default.RETENTION,
    type=datetime.timedelta,
    help="Duration of holding video and recordings in memory",
)
argparser.add_argument(
    "--camera_name",
    env_var="CAMERA_NAME",
    default=pintu.default.CAMERA_NAME,
    type=str,
    help="Name of camera",
)
argparser.add_argument(
    "--sample_rate",
    env_var="SAMPLE_RATE",
    default=pintu.default.SAMPLE_RATE,
    type=float,
    help="Image acquisition sample rate.",
)
argparser.add_argument(
    "--image_format",
    env_var="IMAGE_FORMAT",
    default=pintu.default.IMAGE_FORMAT,
    type=str,
    help="Image save format",
)
argparser.add_argument(
    "--buffer_size",
    env_var="BUFFER_SIZE",
    default=pintu.default.BUFFER_SIZE,
    type=int,
    help="Number of slots in background masking frame-buffer",
)
argparser.add_argument(
    "--buffer_interval",
    env_var="BUFFER_INTERVAL",
    default=pintu.default.BUFFER_INTERVAL,
    type=datetime.timedelta,
    help="Interval between samples in the frame buffer.",
)
argparser.add_argument(
    "--diff_treshold",
    env_var="DIFF_THRESHOLD",
    default=pintu.default.DIFF_THRESHOLD,
    type=int,
    help="""Minimum distance ...
    """,
)

argparser.add_argument(
    "--detection_model_dir",
    env_var="DETECTION_MODEL_DIR",
    default=pintu.default.DETECTION_MODEL_DIR,
    type=pathlib.Path,
    help="Directory containing models.",
)
argparser.add_argument(
    "--detection_model_name",
    env_var="DETECTION_MODEL_NAME",
    default=pintu.default.DETECTION_MODEL_NAME,
    type=str,
    help="Name of the model (not including '.bin' or '.param' extensions).",
)
argparser.add_argument(
    "--clipping_margin",
    env_var="CLIPPING_MARGIN",
    default=pintu.default.CLIPPING_MARGIN,
    type=float,
    help="Margin from the edge of image that is considered 'at the edge'.",
)
argparser.add_argument(
    "--inference_image",
    env_var="INFERENCE_IMAGE",
    default=pintu.default.INFERENCE_IMAGE,
    type=str,
    help="Sample image kind used for inference",
)
argparser.add_argument(
    "--confidence_threshold",
    env_var="CONFIDENCE_THRESHOLD",
    default=pintu.default.CONFIDENCE_TRESHOLD,
    type=float,
    help="Only detections with at least this confidence are considered",
)
argparser.add_argument(
    "--nms_iou_threshold",
    env_var="NMS_IOU_THRESHOLD",
    default=pintu.default.NMS_IOU_THRESHOLD,
    type=float,
    help="Non-minimum suppression threshold",
)


class Configuration(pydantic.BaseModel):
    log_config_file: pathlib.Path
    recordings_dir: pathlib.Path
    events_file: pathlib.Path

    redis_host: str
    redis_port: int

    api_port: int
    api_scheme: str
    api_net_location: str
    api_route_prefix: str
    use_bcm_pin_numbering: bool

    doorbell_pin: int
    doorbell_pressed_pinstate: int
    doorbell_debounce_ms: int

    door_sensor_pin: int
    door_sensor_opened_pinstate: int
    door_sensor_debounce_ms: int

    door_unlock_pin: int
    door_unlock_signal_pinstate: int
    door_unlock_signal_duration: datetime.timedelta

    lock_sensor_pin: int
    lock_sensor_unlocked_pinstate: int
    lock_sensor_debounce_ms: int

    video: str
    retention: datetime.timedelta
    camera_name: str
    sample_rate: float
    image_format: str
    buffer_size: int
    buffer_interval: datetime.timedelta
    diff_treshold: int
    detection_model_dir: pathlib.Path
    detection_model_name: str
    clipping_margin: float
    inference_image: str
    confidence_threshold: float
    nms_iou_threshold: float

    @staticmethod
    @functools.lru_cache()
    def load(*args, **kwargs):
        """
        Load configuration.

        Loading order:
        1. Config file
        2. Environment variables
        3. Command line arguments

        :return:
            Configuration object
        """
        args = argparser.parse_args(*args, **kwargs)
        config = Configuration(**vars(args))
        logging.config.fileConfig(str(config.log_config_file))
        return config

    @property
    def version(self):
        """
        Pintu version

        :return:
            Pintu Version
        """
        return packaging.version.Version(str(pintu.__version__))

    @property
    def api_base_endpoint(self):
        """
        External API endpoint.

        :return:
            External API endpoint.
        """
        return (
            f"{self.api_scheme}://"
            f"{self.api_net_location}:{self.api_port}"
            f"{self.api_route_prefix}"
        )

    def api_link(self, path=""):
        """
        Full redirect link to a path.

        :param path: (optional)
            Relative path to redirect to.
            Defaults to "".

        :return:
            Full redirect link to a path.
        """
        return f"{self.api_base_endpoint}{path}"


config = Configuration.load()

log = logging.getLogger(__name__)
log.info("Config loaded")
