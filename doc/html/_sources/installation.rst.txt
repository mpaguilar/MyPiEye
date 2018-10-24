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

Raspberry Pi Installation
-------------------------

You may need to upgrade setuptools for it to work. There's a file called ``fast_opencv.sh`` which will do
a lot of the work. Assuming you have git installed, start with an empty directory ``mypieye``.

::

    mkdir mypieye
    cd mypieye
    git clone https://github.com/mpaguilar/MyPiEye.git .

    sudo apt install -y python3-pip
    sh fast_opencv.sh
    sudo python3 setup.py install

Create directories and copy the .ini file there.















