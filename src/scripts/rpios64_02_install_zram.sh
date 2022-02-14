#!/bin/bash

ZRAM_INSTALL_PATH=/usr/bin/zram.sh

if [[ -y ${PINTU_INSTALL_DIR} ]] ; then
    echo "Pintu install directory not set in `PINTU_INSTALL_DIR` environment variable."
fi

# Install ZRAM instead of swapping, if not alredy present
if [[ -e ${ZRAM_INSTALL_PATH} ]]; then
    # remove the old dphys version
    sudo /etc/init.d/dphys-swapfile stop
    sudo apt-get remove -y --purge dphys-swapfile
    # install zram
    sudo cp ${PINTU_INSTALL_DIR}/scripts/zram.sh ${ZRAM_INSTALL_PATH}

    # Alternative source... if you trust it, it may be more maintained
    # sudo wget -O ${ZRAM_INSTALL_PATH} https://raw.githubusercontent.com/novaspirit/rpi_zram/master/zram.sh
fi

# Set autoload
if [[ -z `grep ${ZRAM_INSTALL_PATH} /etc/rc.local` ]] ; then
    sudo sed -i -e "s|^exit 0|# Enable ZRAM\n${ZRAM_INSTALL_PATH} \&\n\nexit 0|g" /etc/rc.local
fi

touch 

