# MyPiEye

Compares image files, uses opencv to determine if any motion happened, and if so, saves those files.

## NOTE: There's still some polishing to do.


What works:
 - Image capturing
 - Image comparison
 - Image save to local drive
 - Image save to Google Drive
 
 
If you don't mind a little bit of tweaking and prodding here and there, it works. The core functionality is
running just fine.

Work in progress.

## Setup and configuration

Requires python 3.5 or greater.

Installation on a PC is pretty simple. Run `setup.py install`, wait while it downloads everything, and
you should be good to go by running `mypieye`. A virtual environment is recommended, of course.

Installation on an RPi is a bit more involved.

Configuration is mostly handled within an .ini file. 
By default it will look for `mypieye.ini` in the current directory. It can also be specified at the command line with
the `--iniconfig` switch.

Detailed info can be found in doc/html.

