# Pintu
Pintu: Bahasa (Indonesian, Malay) for 'Door'

Pintu is a Raspberry Pi based "smart doorbell" with video capabilities, object detection and an API for remote control.
# Prerequisites

A Raspberry Pi 4, Model B or Compute Module.

You also need at least two of the following for this project to make sense:
- A physical door, gate, barrier or similar
- A camera to view whats going on. This could either be a Pi-camera, a USB web camera or an IP camera that supports HTTP or RTSP video streaming.
- A doorbell or button, for guests to request access, properly hooked up one of the Raspberry Pi input pins. Wiring examples to come.
- An electrically triggered opening or unlocking mechanism, properly hooked up one of the Raspberry Pi input pins. Wiring examples to come.

# OS and Firmware setup
## 1. 64 bit  Raspberry Pi OS 
Pintu requires the 64 bit version of Raspberry Pi OS, and won't work properly on the official Raspberry Pi OS images, which are only 32 bit. 
The Raspberry Pi OS 64-bit builds are still only in a beta stage and unfortunately has a [number of other limitations and issues](https://github.com/raspberrypi/Raspberry-Pi-OS-64bit/issues), so you will not find these in the usual place on the official website.

Instead, these builds are made available through the raspberry pi foundations downloads mirrors. 

- [Desktop](https://downloads.raspberrypi.org/raspios_arm64/images/)

    With the desktop environment. 
    Recommended only if you intend to interact with Pintu's UI directly using a directly attached (touch) screen.

- [Lite](https://downloads.raspberrypi.org/raspios_lite_arm64/images/)
    
    Without desktop environment. Most lightweight and performant.
    Select this version if you are only going to interact with Pintu's web UI and/or API, using remote devices.



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

## 2. Disable Swapping & Enable ZRAM
(Modified from tutorial from [Q-engineering](https://qengineering.eu/install-raspberry-64-os.html).)

The risk of flash disk failure increase with the volume of writes. For this reasin it is recmmended to turn of memory swapping to file, in favor of instead using zram, which compresses the swapped data but retains it in memory.

```console
sudo /etc/init.d/dphys-swapfile stop
sudo apt-get remove --purge dphys-swapfile
```
Answer 'yes', wen asked if you want to remove `dphys-swapfile`.

With root privileges create a new file `/usr/bin/zram.sh`, eg:
```console
sudo nano /usr/bin/zram.sh
```

Paste in the following content. It is a script that set up the in-RAM swap-space using ZRAM.
```bash
#!/bin/bash

export LANG=C

cores=$(nproc --all)

# disable zram
core=0
while [ $core -lt $cores ]; do
    if [[ -b /dev/zram$core ]]; then
        swapoff /dev/zram$core
    fi
    let core=core+1
done
if [[ -n $(lsmod | grep zram) ]]; then
    rmmod zram
fi
if [[ $1 == stop ]]; then
    exit 0
fi

# disable all
swapoff -a

# enable zram
modprobe zram num_devices=$cores

echo lz4 > /sys/block/zram0/comp_algorithm

totalmem=$(free | grep -e "^Mem:" | awk '{print $2}')
mem=$(( ($totalmem / $cores) * 1024 * 2 ))

core=0
while [ $core -lt $cores ]; do
    echo $mem > /sys/block/zram$core/disksize
    mkswap /dev/zram$core
    swapon -p 5 /dev/zram$core
    let core=core+1
done
```

Save the file (make sure it is at `/usr/bin/zram.sh`), exit the text editor and give the file execution permissions:
```
sudo chmod +x /usr/bin/zram.sh
```


To make sure that the script runs on startup, using any text editor modify `/etc/rc.local` with root permissions, eg:
```console
sudo nano /etc/rc.local
```

Include a call to the newly created script by adding the line `/usr/bin/zram.sh &` before `exit 0` at the end of the file, so the file looks like this:
```sh
!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.
#
# In order to enable or disable this script just change the execution
# bits.
#
# By default this script does nothing.

# Print the IP address
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

/usr/bin/zram.sh &

exit 0
```
Save the modified file exit the text editor, and reboot your Raspberry Pi.

After reboot, you can test that it worked by issuing:
```console
free -m
```
The output may look somehting like this
```
               total        used        free      shared  buff/cache   available
Mem:            3743         277        3228          32         237        3367
Swap:           7486           0       14972
```
The important thing is that the sum of `Mem` and `Swap` in the `total`-column is greater than 6000.

## 3. Updating EEPROM
This is not strictly neccesary but using the latest EEPROMs may increase CPU performance and/or lower its heat profile.

You can check if you have the latest EEPROM version by issuing:

```console
sudo CM4_ENABLE_RPI_EEPROM_UPDATE=1 rpi-eeprom-update
```
(The `CM4_ENABLE_RPI_EEPROM_UPDATE=1` part is only required for Compute Modules, but works on Model B as well)

If you have the latest (official and stable) EEPROM bootloader, it should say `BOOTLOADER: up to date` along with information of the current and latest versions, e.g:

```console
BOOTLOADER: up to date
   CURRENT: Thu 29 Apr 2021 04:11:25 PM UTC (1619712685)
    LATEST: Thu 29 Apr 2021 04:11:25 PM UTC (1619712685)
   RELEASE: default (/lib/firmware/raspberrypi/bootloader/default)
            Use raspi-config to change the release.

  VL805_FW: Dedicated VL805 EEPROM
     VL805: up to date
   CURRENT: 000138a1
    LATEST: 000138a1
```

If, on the other hand, you have an outdated EEPROM bootloader, it will say `BOOTLOADER: update available` along with information of the current and latest versions.

To update the bootloader EEPROM, follow the instructions for the corresponding section below, depending on whether you are using a "Model B" board or a "Compute Module".

- **Model B** (i.e. Booting from SD-card)

    If you are using a Raspberry Pi 4 Model B, i.e. a "normal" standalone board, simply run the following commands to update the EEPROM.
    ```console
    sudo rpi-eeprom-update -a
    sudo reboot
    ```

- **Compute Module** (i.e. Booting from on-board eMMC)

    If you are using a Raspberry Pi 4 Compute model, i.e. a "CM4", the update process is a little bit more involved.
    Note that it is here assumed that you are using Linux and used [usbboot](https://github.com/raspberrypi/usbboot) when flashing the OS to the CM4.

    The process **should** be the same for Windows but the commands may be different 🤷. 

    1. Identify the latest EEPROM `bin` file [here](https://github.com/raspberrypi/rpi-eeprom/tree/master/firmware/stable)

        At the moment of writing, `pieeprom-2021-12-02.bin` was the latest.

    2. Download the `bin` file into the `usboot/recovery` directory **of to the computer used to flash the CM4** (not the CM4 itself), e.g:
        ```console
        cd ~/usboot/recovery
        rm -f pieeprom.original.bin
        curl -L -o pieeprom.original.bin https://github.com/raspberrypi/rpi-eeprom/raw/master/firmware/stable/pieeprom-pieeprom-2021-12-02.bin
        ```
        Naturally, modify the `usbboot` directory and the EEPROM `bin` file name to correspond to your situation.

    3. Make sure the “disable MMC boot” jumper on your CM4 carrier board (`J2`, on the official IO-board) is bridged to ground, to disable eMMC boot.

    4. Connect the CM4 to your host computer's USB, as when flashing the OS to eMMC.

    5. Flash the EEPROM to the CM4, by issuing:

        ```console
        cd ~/usbboot
        sudo ./rpiboot -d recovery
        ```
    6. Disconnect the CM4, power it off and un-bridge the eMMC boot jumper and boot it up again in normal operation.

# Installation

## 4. OpenCV:
(Modified from tutorial from [Q-engineering](https://qengineering.eu/install-opencv-4.4-on-raspberry-64-os.html).)

```console
sudo apt-get update
sudo apt-get upgrade
```
Answer `yes` when asked wether to continue.

## 5. Ncnn 
Install as per:
https://qengineering.eu/install-ncnn-on-raspberry-pi-4.html

## 6. Python 3.7+
This should be default in more recent versions of for example Raspberry Pi OS.

## 7. Redis server
```console
sudo apt-get install -y redis-server
```

## 8. Pintu

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

    If installed normally, Redis should start automatically on boot.

    If it is not running, it can be started with:
    ```console
    redis-server
    ```

2. Capture - captures the camera stream and publish it to Redis

    ```console
    pintu-capture [args]
    ```
    or
    ```console
    python3 src/pintu/capture.py [args]
    ```

3. Detector - Detects people and objects 

    ```console
    pintu-detect [args]
    ```
    or
    ```console
    python3 src/pintu/detect.py [args]
    ```

4. Recorder - Records video snippets on events 

    ```console
    pintu-record [args]
    ```
    or
    ```console
    python3 src/pintu/record.py
    ```

5. API - allows for interaction and a super simple UI 

    ```console
    pintu-api [args]
    ```
    or
    ```console
    python3 src/pintu/api.py
    ```




## Potential future stuff
- Google Home / Nest devices to broadcast to
- A sensor to check if the door is open or closed
- A sensor to check if the door is unlocked or locked
- A Presence / IR sensor
- A light control
