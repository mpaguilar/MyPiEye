"Quick" Start
=============

MyPiEye works fine in a virtual environment. The tricky part is OpenCV, especially on the RPi.
My use case is for an RPi to act as a dedicated device, with MyPiEye running as a service. I haven't put in
the effort to get it to run in a virtual environment, as a service.

PC Installation
---------------

Whether or not you are using a virtual environment, installation is pretty easy.

Clone the repository, and run setup.py

::

    git clone https://github.com/mpaguilar/MyPiEye.git
    cd MyPiEye
    python setup.py install

There should be a lot of installation-related output, and hopefully no errors.

Test it with ``mypieye --help``. If that doesn't work, well...poke at it. I'm still a little new with setuptools.

RPi Installation
----------------

This is a bit more involved. Before running ``setup.py``, OpenCV needs to be built. If there's a quicker/easier way,
I'm open to suggestions.

Taken from ``https://www.pyimagesearch.com/2016/04/18/install-guide-raspberry-pi-3-raspbian-jessie-opencv-3/``

::

    sudo apt-get install build-essential cmake pkg-config
    sudo apt-get install libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev
    sudo apt-get install libavcodec-dev libavformat-dev libswscale-dev libv4l-dev
    sudo apt-get install libxvidcore-dev libx264-dev
    sudo apt-get install libgtk2.0-dev
    sudo apt-get install libatlas-base-dev gfortran
    sudo apt-get install python2.7-dev python3-dev


Get the source code, because there isn't a pip package for OpenCV on RPi. Do this in a separate directory,
because you'll need to ``make install`` for every virtual environment, if you use it that way.

::

    mkdir opencv_work
    mkdir opencv_work
    wget -O opencv.zip https://github.com/Itseez/opencv/archive/3.1.0.zip
    unzip opencv.zip
    wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/3.1.0.zip
    unzip opencv_contrib.zip

Setup the makefile.

::

    cd opencv-3.1.0/
    mkdir build
    cd build
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D INSTALL_PYTHON_EXAMPLES=ON \
        -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib-3.1.0/modules \
        -D BUILD_EXAMPLES=OFF \
        -D ENABLE_PRECOMPILED_HEADERS=OFF \
        -D WITH_FFMPEG=ON \
        ..

That will run for awhile. A very long while on an RPi. Do it before you go to sleep, or something.

If that finishes without error, lucky you! Er, I mean, you should be able to use ``setup.py``.

::

    git clone https://github.com/mpaguilar/MyPiEye.git
    cd MyPiEye
    python setup.py install

Configuration
-------------

It needs to be configured before use. The app needs your permission to use Google drive, and the folder on the drive
needs to be created using those credentials. There are some local folders to be created, as well.

Start with one of the sample .ini files, and modify to your taste.

The first time this is run, you will be prompted with a google.com URL and a short code ("XXXX-XXXX"). This is what
permits the application to use your GDrive. It asks for minimal permissions, and can only access folders and files
it creates.

Once validated, it will create the folder at google, and any local folders.

Disabling GDrive
^^^^^^^^^^^^^^^^

Omit the ``[gdrive]`` section.

::

    mypieye configure --iniconfig <some ini file>

Running
-------

``mypieye run`` will look for a file named ``mypieye.ini`` in the current directory.

``mypieye --help`` offers more.

Running on RPi
^^^^^^^^^^^^^^

You may need to upgrade setuptools for it to work

::

    sudo pip3 install -U setuptools










