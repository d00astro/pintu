# Pintu
Pintu: Bahasa (Indonesian, Malay) for 'Door'

Pintu is a "smart doorbell" with video capabilities, remote control and Chromecast integration, for Raspberry Pi compatible ARM microcontrollers.

## Prerequisites 
before installation
#### RPi.GPIO
##### for Raspberry Pi
... TBC 
##### for Pine64 
Somewhere, e.g. in `~/Downloads/`:
```
git clone https://github.com/swkim01/RPi.GPIO-PineA64.git
cd RPi.GPIO-PineA64
sudo python setup.py install
sudo chmod -R $USER:$USER ./
sed 's/_//' RPi/GPIO/__init__.py
```
The last line is a hack to make it work (needed?)

Then add to `~/.bashrc`:
```
export PYTHONPATH=$HOME/Downloads/RPi.GPIO-PineA64/:$PYTHONPATH
```
Adjust for installation dir, if not `Downloads`.

#### Pip
```
sudo apt install python-pip
```

## Install
```
git clone https://github.com/d00astro/pintu.git
cd pintu
pip install -r requirements

```