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



