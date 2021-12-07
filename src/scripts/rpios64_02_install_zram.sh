#/bin/bash

ZRAM_PATH=/usr/bin/zram.sh

# Install ZRAM instead of swapping, if not alredy present
if [[ -e ${ZRAM_PATH} ]]; then
    # remove the old dphys version
    sudo /etc/init.d/dphys-swapfile stop
    sudo apt-get remove --purge dphys-swapfile
    # install zram
    sudo wget -O ${ZRAM_PATH} https://raw.githubusercontent.com/novaspirit/rpi_zram/master/zram.sh
fi

# set autoload
if [[ -z `grep ${ZRAM_PATH} /etc/rc.local` ]] ; then
    sudo sed -i -e "s|^exit 0|# Enable ZRAM\n${ZRAM_PATH} \&\n\nexit 0|g" /etc/rc.local
fi

