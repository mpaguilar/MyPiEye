# MyPiEye

Compares image files, uses opencv to determine if any motion happened, and if so, saves those files.

## NOTE: this isn't ready. I'm converting it from a much messier project.

If you want to use it, it works. It will capture images and store them to the local drive. Getting it set up on a PC is still more work than it should be, and I'm hoping there is a wheel for opencv on RPi.

Work in progress.

## RPi building instructions:

Taken from ```https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/```

```
sudo apt-get install build-essential cmake pkg-config
sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
sudo apt-get install libxvidcore-dev libx264-dev
sudo apt-get install libgtk2.0-dev
sudo apt-get install libatlas-base-dev gfortran
sudo apt-get install python2.7-dev python3-dev
```

Get the source code, because there isn't a pip package:

```
mkdir opencv_work
mkdir opencv_work
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.1.0.zip
unzip opencv.zip
wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.1.0.zip
unzip opencv_contrib.zip
```

Install python dependencies:
```
sudo pip3 install numpy
sudo pip3 install matplotlib
sudo pip3 install scipy
sudo pip3 install google-api-python-client
sudo pip3 install click
sudo pip3 install colorama
```

You might also need (depending on your distro):
```
sudo pip3 install oauth2client
```

Setup the makefile:
```
cd ~/opencv-3.1.0/
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_PYTHON_EXAMPLES=ON \
    -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-3.1.0/modules \
    -D BUILD_EXAMPLES=ON ..
```
Check the output for errors.

Then run ```make```. This will take awhile. A long while - take a nap, or something.
When that's done, install it.
```
sudo make install
sudo ldconfig
```

