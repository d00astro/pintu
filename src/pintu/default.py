# -*- coding: utf-8 -*-
"""
Default values.
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
import os
import pathlib
import re

# General
INSTALL_DIR = pathlib.Path(os.getenv("PINTU_INSTALL_DIR", ""))
"""Pintu installation directory"""
CONF_DIR = INSTALL_DIR / "config"
"""Pintu configuration files directory"""
CONFIG_FILES = [
    "pintu.conf",
    str(pathlib.Path().home() / "pintu.conf"),
    str(CONF_DIR / "pintu.conf"),
]
"""Configuration files to read."""
LOG_CONFIG_FILE = CONF_DIR / "logging.conf"
"""Logging configuration file."""
EVENTS_FILE = CONF_DIR / "events.json"  # Not used (yet)s
"""Events handling configuration file"""
COMPACT_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%S%f"
"""Compact filename-friendly datetime format (ISO 8601 based)."""
COMPACT_TIMESTAMP_REGEXP = re.compile(r"\d{8}T\d{12}")
"""Regular expression for compact filename-friendly datetime format."""
RECORDINGS_DIR = INSTALL_DIR / "recordings"  # Not used (yet)
"""Recordings directory"""
RECORDINGS_FILENAME_FORMAT = COMPACT_TIMESTAMP_FORMAT + ".mp4"
"""Path of recorded clips within the recordings directory."""
STREAM_ID_TIMESTAMP_FORMAT = "%Y%m%d%H%M%S-%f"
"""Format of stream id timestamps"""

# Redis
REDIS_HOST = "localhost"
"""Hostname / IP of Redis"""
REDIS_PORT = 6379
"""Redis port"""


# API
API_LISTEN_PORT = 8080
"""API listen port"""
API_SCHEME = "http"
"""API protocol scheme ('http' or 'https')"""
API_NET_LOCATION = "127.0.0.1"
"""Net location of the API"""
API_ROUTE_PREFIX = ""
"""Route prefix, pruned by reverse proxies, if any"""


# GPIO
USE_BCM_PIN_NUMBERING = False
"""Use BCM pin numbering instead of board pin numbering."""

DOORBELL_PIN = 11
"""Pin on which the doorbell is signalling."""
DOORBELL_PRESSED_PINSTATE = 1
"""Sate of the pin when doorbell is pressed."""
DOORBELL_DEBOUNCE_MS = 2000
"""Number of milliseconds to 'debounce' the doorbell signal for."""

DOOR_SENSOR_PIN = 12
"""Pin on which the door sensor is signalling."""
DOOR_SENSOR_OPENED_PINSTATE = 1
"""State of the pin when door is open."""
DOOR_SENSOR_DEBOUNCE_MS = 500
"""Number of milliseconds to 'debounce' the door sensor signal for."""

DOOR_UNLOCK_PIN = 13
"""Pin on which the door unlock actuation/output should be singalled on."""
DOOR_UNLOCK_SIGNAL_PINSTATE = 1
"""State of the pin to signal to open the lock."""
DOOR_UNLOCK_SIGNAL_DURATION = datetime.timedelta(seconds=3)
"""Number of milliseconds to hold the signal."""

LOCK_SENSOR_PIN = 15
"""Pin on which the lock sensor is signalling."""
LOCK_SENSOR_UNLOCKED_PINSTATE = 1
"""State of the pin when the lock is unlocked."""
LOCK_SENSOR_DEBOUNCE_MS = 500
"""Number of milliseconds to 'debounce' the lock sensor singal for."""


# Image Processing
RETENTION = datetime.timedelta(minutes=1)
"""Duration of holding video and recordings in memory"""
CAMERA_NAME = "doorcam"
"""Name of the camera"""
VIDEO = "/dev/video0"
"""Video source"""
SAMPLE_RATE = 5.0
"""Image sampling rate, in frames per second."""
IMAGE_FORMAT = "jpg"
"""Image format to save images as."""
BUFFER_SIZE = 0
"""Number of slots in the background extraction buffer.
0 means no background extraction."""
BUFFER_INTERVAL = datetime.timedelta(minutes=1)
"""Interval between samples in the frame buffer."""
DIFF_THRESHOLD = 42
"""Minimum distance between pixels in background and input image,
for it to be classified as foreground.e
"""
DETECTION_MODEL_DIR = INSTALL_DIR / "models"
"""Directory where detection models are stored."""
DETECTION_MODEL_NAME = "ndm_i8_coco"
"""Base name of the model to use."""
DETECTION_NAMES_FILE = DETECTION_MODEL_DIR / "names_coco"
"""Name of the file that contain the object classes"""
CLIPPING_MARGIN = 0.005  # Not used (yet)
"""Maximum relative distance to the image edge for a detection to be considered
clipped by the image."""
INFERENCE_IMAGE = "input"
"""Sample image kind used for inference."""
CONFIDENCE_TRESHOLD = 0.33
"""Detections over this confidence are considereded true."""
NMS_IOU_THRESHOLD = 0.75
"""Non-minimum suppression threshold"""
