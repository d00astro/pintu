#!/bin/bash
LOGDIR=/var/log/pintu
LOG=${LOGDIR}/install.log
ERR=${LOGDIR}/install_error
OK=${LOGDIR}/install_ok
PINTU_VAR_FILE=/etc/pintu/default


mkdir -p ${LOGDIR}



if [[ -r ${PINTU_VAR_FILE} ]] ; then
    source ${PINTU_VAR_FILE}
fi

# Remember install dir
if [[ -z ${PINTU_INSTALL_DIR} ]] ; then

    # TODO: Figure out and ask for install dir
    PINTU_INSTALL_DIR=/home/pi/pintu
    # TODO: validate install dir is correct

    echo "PINTU_INSTALL_DIR=${PINTU_INSTALL_DIR}" | sudo tee ${PINTU_VAR_FILE}
fi

# Update registry
sudo apt-get update &&
sudo apt-get upgrade &&

# 1. (Reserved for future use)

# 2. Install ZRAM, if not already installed
if [ -z `cat /proc/swaps | grep zram` ] ; then 
    echo "Installing ZRAM" >> ${LOG}
    $PINTU_INSTALL_DIR/scripts/rpios64_02_install_zram.sh >> ${LOG} 2>&1 && 
    reboot || echo "ZRAM install failed!" > ${ERR}
fi

# 3. Install OpenCV, if not already installed
if [ -z `python3 -c "import cv2 ; print(cv2.__version__)"` ] ; then 
    echo "Installing OpenCV" >> ${LOG}
    $PINTU_INSTALL_DIR/scripts/rpios64_03_build_opencv.sh >> ${LOG} 2>&1 && 
    reboot || echo "OpenCV install failed!" > ${ERR}
; fi

# 4. Install NCNN, if not already installed
if [ -z `python3 -c "import ncnn ; print(ncnn.__version__)"` ] ; then
    echo "Installing NCNN" >> ${LOG}
    $PINTU_INSTALL_DIR/scripts/rpios64_04_build_ncnn.sh  >> ${LOG} 2>&1 && 
    reboot || echo "NCNN install failed!" >  ${ERR}
fi

# 5. Install Pintu, if not already installed
if [ -z `python3 -c "import pintu ; print(pintu.__version__)"` ] ; then 
    echo "Installing Pintu" >> $LOG
    if [ -z `python3 -m pip --version` ] ; then 
        echo "Installing pip" >> $LOG
        sudo apt-get install python3-pip >> $LOG 2>&1 || echo "Pip install failed!" > ${ERR} 2>&1
    fi
    python3 -m pip install $PINTU_INSTALL_DIR >> $LOG 2>&1 || echo "Pintu install failed!" >  ${ERR} 2>&1

    echo "Pintu install successful!" > $OK
fi

# 6. Install Redis Server, if not alreday installed
if [ -z `redis-server --version` ] ; then
    sudo apt-get insall redis-server || echo "Redis install failed!" >  ${ERR} 2>&1
fi

