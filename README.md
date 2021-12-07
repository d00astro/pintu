# Pintu
Pintu: Bahasa (Indonesian, Malay) for 'Door'

Pintu is a "smart doorbell" with video capabilities, remote control and Chromecast integration, for Raspberry Pi.

## Prerequisites
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

## Install
```
git clone https://github.com/d00astro/pintu.git
cd pintu
pip install -r requirements
```

## Run
TBD