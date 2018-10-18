# MyPiEye

Compares image files, uses opencv to determine if any motion happened, and if so, saves those files.

## NOTE: There's still some polishing to do.


What works:
 - Image capturing
 - Image comparison
 - Image save to local drive
 - Image save to Google Drive
 - Basic configuration
 
What doesn't work:
 - setup.py is broken
 - Configuration needs improvement
 - The documentation
 - Misc cleanup problems
 - Untested on an RPi. Works great on PC.

Plus, a little module renaming and project structure updates.
 
If you don't mind a little bit of tweaking and prodding here and there, it works. The core functionality is
running just fine.

Work in progress.

## Setup and configuration

Requires python 3.5 or greater.

Installation on a PC is pretty simple. Run `setup.py install`, wait while it downloads everything, and
you should be good to go by running `mypieye`. A virtual environment is recommended, of course.

Installation on an RPi is a bit more involved. At the time of this writing, there isn't a wheel for OpenCV on ARM,
so you have to build it. Detailed instructions can be found below.

Configuration is mostly handled within an .ini file. 
By default it will look for `mypieye.ini` in the current directory. It can also be specified at the command line with
the `--iniconfig` switch.


### Configuration file settings

There are three sections, `[global]`, `[minsizes]`, `[ignore]`.

* `global` handles things like which camera to use, working and save directories.
* `minsizes` sets the smallest "box" that will be captured. This helps prevent false positives 
when a leaf scurries across your lawn.
* `ignore` specfies boxes to ignore. The pattern is top-start, left-start, width, length. 
Multiple keys can be used, but they must be unique. This can be tricky, because the values depend on the
capture resolution.

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

Get the source code, because there isn't a pip package for OpenCV on RPi:

```
mkdir opencv_work
mkdir opencv_work
wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.1.0.zip
unzip opencv.zip
wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.1.0.zip
unzip opencv_contrib.zip
```

Install python dependencies (still needed? I dunno. Will check.):
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

Then run ```make```. This will take awhile. A long while - take a nap, walk your dogs, or something.
When that's done, install it.
```
sudo make install
sudo ldconfig
```

