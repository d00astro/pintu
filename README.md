# Pintu
Pintu: Bahasa (Indonesian, Malay) for 'Door'

Pintu is a "smart doorbell" with video capabilities, remote control and Chromecast integration, for Raspberry Pi.

## Prerequisites

### 64 bit  Raspberry Pi OS 
Pintu requires the 64 bit version of Raspberry Pi OS, and won't work properly on the official Raspberry Pi OS images, which are only 32 bit. 
The Raspberry Pi OS 64-bit builds are still only in a beta stage and has a [number of other limitations and issues](https://github.com/raspberrypi/Raspberry-Pi-OS-64bit/issues), so you will not find these in the usual place on the official website.

Instead, these builds are made available through the raspberry pi foundations downloads mirror. 

#### Lite (headless, without desktop):
https://downloads.raspberrypi.org/raspios_lite_arm64/images/

#### Desktop
https://downloads.raspberrypi.org/raspios_arm64/images/

Download your preferred version, and flash it onto the RPi, and go through the setup as you normally would.

To validate that you are running a 64 bit OS, you can run:
```console
uname -a | grep aarch64
```
And
```console
gcc -v 2>&1 >/dev/null | grep aarch64
```
If both commands printed out information, you are good to go.

### Enable ZRAM
Modified from tutorial from [Q-engineering](https://qengineering.eu/install-raspberry-64-os.html).

...




### OpenCV:
Install as per:
https://qengineering.eu/install-opencv-4.4-on-raspberry-64-os.html

### Ncnn 
Install as per:
https://qengineering.eu/install-ncnn-on-raspberry-pi-4.html


You need at least two of the following for this project to make sense:
- A physical door, gate, barrier or similar
- A doorbell or button, for guests to request access, properly hooked up one of the Raspberry Pi input pins. Wiring examples to come.
- An electrically triggered opening or unlocking mechanism, properly hooked up one of the Raspberry Pi input pins. Wiring examples to come.
- A camera to view whats going on. This could either be a Pi camera, a USB web camera or an IP camera that supports http or rtsp video streaming.
- Google Home / Nest devices to broadcast to
 
Potential future stuff:
- A sensor to check if the door is open or closed
- A sensor to check if the door is unlocked or locked
- A Presence / IR sensor
- A light control

You also need: 
#### Python 3.7+
This should be default in more recent versions of for example Raspberry Pi OS.

### Redis server
... TBD .. 

## Install

```
git clone https://github.com/d00astro/pintu.git
cd pintu
pip install .
```
You may want to export an environment variable `PINTU_INSTALL_DIR` pointing to the repo directory.
E.g. by adding the following line to `/home/pi/.bashrc`:
```console
export PINTU_INSTALL_DIR=/home/pi/pintu
```
(Assuming you cloned pintu into the home directory of the `pi` user.)
## Run
Pintu runs as 5 different processes in parallel:

1. Redis server - Acts as a communication bus between the other services

    ```
    redis-server
    ```

2. Capture - captures the camera stream and publish it to Redis

    ```
    python3 src/pintu/capture.py [args]
    ```

3. Detector - Detects people and objects 

    ```
    python3 src/pintu/detect.py [args]
    ```

4. Recorder - Records video snippets on events 

    ```
    python3 src/pintu/record.py
    ```

5. API - allows for interaction and a super simple UI 

    ```
    python3 src/pintu/api.py
    ```
