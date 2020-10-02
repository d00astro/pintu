# Pintu
Pintu: Bahasa (Indonesian, Malay) for 'Door'

Pintu is a "smart doorbell" with video capabilities, remote control and Chromecast integration, for Raspberry Pi compatible ARM microcontrollers.

## Prerequisites
#### Python 3.8
Somewhere, eg in `~/Downloads/` , and as root (or using `sudo`, depending on debian flavor) run the following to install Python 3.8
```
apt install libffi-dev libbz2-dev liblzma-dev libsqlite3-dev libncurses5-dev libgdbm-dev zlib1g-dev libreadline-dev libssl-dev tk-dev build-essential libncursesw5-dev libc6-dev openssl git;
wget https://www.python.org/ftp/python/3.8.0/Python-3.8.0.tar.xz
tar xf Python-3.8.0.tar.xz
cd cpython-3.8*
./configure --prefix=$HOME/.local --enable-optimizations --disable-profiling
make -j -l 4
make altinstall
cd ..
rm -r Python-3.8.0
rm Python-3.8.0.tar.xz
```

Then add to `~/.bashrc`:
```
export PATH=$HOME/.local/bin/:$PATH
```

#### RPi.GPIO
##### for Raspberry Pi
... TBC 
##### for Pine64 
Somewhere, e.g. in `~/Downloads/`:
```
git clone https://github.com/swkim01/RPi.GPIO-PineA64.git
cd RPi.GPIO-PineA64
sudo python3.8 setup.py install
sudo chmod -R $USER:$USER ./
sed 's/_//' RPi/GPIO/__init__.py
```
The last line is a hack to make it work

Then add to `~/.bashrc`:
```
export PYTHONPATH=$HOME/Downloads/RPi.GPIO-PineA64/:$PYTHONPATH
```
Adjust for installation dir, if not `Downloads`.

#### Pip
```

```