#/bin/bash


OPENCV_VERSION=4.4.0

# Check if OpenCV is already installed
if `python3 -c "import cv2" 2> /dev/null` ; then 
    echo "OpenCV already installed!"
    exit 0
fi

# Check for ARM 64 architecture
if [[ -z `uname -a | grep aarch64` ]] ; then
    echo "This installation script is only for 64 bit ARM system, which this is not." 
    exit 1
fi

# Check if sufficient memory
if [[ `free -m | awk -F " " 'NR>1{total += $2} END {print total}'` -lt 5500 ]] ; then
    echo "Not enough memory. At least 5.5 GB of physical + virtual memory is needed. "
    echo "If you haven't installed 'Zram' yet, run the 'rpios64_install_zram.sh' script, reboot and try again."
    echo "Alternatively, you can try to increase swap memory by increasing the value for 'CONF_MAXSWAP' in '/etc/dphys-swapfile', reboot and try again. Note that this is not recommeded if your storage is an SD card, as it will quickly wear out. Also, dont forget to reinstate the swap size once installation is complete."
    exit 1
fi

# Update registry
sudo apt-get update &&
sudo apt-get upgrade &&

# Download dependencies 
sudo apt-get install -y build-essential cmake git unzip pkg-config &&
sudo apt-get install -y libjpeg-dev libpng-dev &&
sudo apt-get install -y libavcodec-dev libavformat-dev libswscale-dev &&
sudo apt-get install -y libgtk2.0-dev libcanberra-gtk* libgtk-3-dev &&
sudo apt-get install -y libxvidcore-dev libx264-dev &&
sudo apt-get install -y python3-dev python3-numpy python3-pip &&
sudo apt-get install -y libtbb2 libtbb-dev libdc1394-22-dev &&
sudo apt-get install -y libv4l-dev v4l-utils &&
sudo apt-get install -y libopenblas-dev libatlas-base-dev libblas-dev &&
sudo apt-get install -y liblapack-dev gfortran libhdf5-dev &&
sudo apt-get install -y libprotobuf-dev libgoogle-glog-dev libgflags-dev &&
sudo apt-get install -y protobuf-compiler &&

# Download OpenCV
cd ~
if [[ -e opencv-${OPENCV_VERSION} ]] ; then
    wget -O opencv.zip https://github.com/opencv/opencv/archive/${OPENCV_VERSION}.zip &&
    unzip opencv.zip &&
fi
if [[ -e opencv_contrib-${OPENCV_VERSION} ]]; then
    wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/${OPENCV_VERSION}.zip &&
    unzip opencv_contrib.zip &&
fi 

# Build OpenCV
cd ~/opencv-${OPENCV_VERSION}/ &&
mkdir -p build &&
cd build &&
cmake \
    -D CMAKE_BUILD_TYPE=RELEASE \
    -D CMAKE_INSTALL_PREFIX=/usr/local \
    -D OPENCV_EXTRA_MODULES_PATH=~/opencv_contrib-${OPENCV_VERSION}/modules \
    -D ENABLE_NEON=ON \
    -D WITH_FFMPEG=ON \
    -D WITH_TBB=ON \
    -D BUILD_TBB=ON \
    -D BUILD_TESTS=OFF \
    -D WITH_EIGEN=OFF \
    -D WITH_GSTREAMER=OFF \
    -D WITH_V4L=ON \
    -D WITH_LIBV4L=ON \
    -D WITH_VTK=OFF \
    -D WITH_QT=OFF \
    -D OPENCV_ENABLE_NONFREE=ON \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=OFF \
    -D BUILD_NEW_PYTHON_SUPPORT=ON \
    -D BUILD_opencv_python3=TRUE \
    -D OPENCV_GENERATE_PKGCONFIG=ON \
    -D BUILD_EXAMPLES=OFF \
    .. &&
make -j$(nproc) &&
sudo make install &&
sudo ldconfig &&
make clean &&
sudo apt-get update &&
# Test it 
python -c "import cv2" &&

## Remove
cd ~ &&
sudo rm -rf ~/opencv-${OPENCV_VERSION}
sudo rm -rf ~/opencv_contrib-${OPENCV_VERSION}
