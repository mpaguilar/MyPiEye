# MyPiEye

Compares image files, uses opencv to determine if any motion happened, and if so, saves those files.

## NOTE: There's still some polishing to do.


What works:
 - Image capturing
 - Image comparison
 - Image save to local drive
 - Image save to AWS, with metadata support
 - Image save to Azure
 - Using Celery with Redis backend for messaging
 
 
If you don't mind a little bit of tweaking and prodding here and there, it works. The core functionality is
running just fine.

Work in progress.

## Setup and configuration

Requires python 3.5 or greater.

Installation on a PC is pretty simple. Run `setup.py install`, wait while it downloads everything, and
you should be good to go by running `mypieye`. A virtual environment is recommended, of course.

Installation on an RPi is a bit more involved.

The running user should be added to the ``video`` group.

Configuration is mostly handled within an .ini file. 
By default it will look for `mypieye.ini` in the current directory. It can also be specified at the command line with
the `--iniconfig` switch.

## Usage suggestions

Create a mypieye.ini in a separate directory (I use `../mpe_workdir`).
Activate the virtual env, and use it from there.

## Usage, extended

The main app spawns several processes, configured via .ini or environment variables. See the example .ini for details.

Backends are enabled and disabled in the ``[multi]`` section. Each one will have its own config section in the .ini.

Adding a new backend is kind of pain.

 - write the backend, using an existing one as an example (``celery_storage`` and ``minio_storage`` are pretty good).
 - update ``supervisor.py`` to launch it
 - update ``configure_app.py`` to handle checks and configs 

### Celery
The `celery` backend requires a running Redis server. 

Launch workers using celery worker arguments, such as ``--pool``
```shell

    python -m MyPiEye --loglevel DEBUG worker --pool=solo

``` 

For debugging, use ``--pool=solo``. 

To run on Windows, use ``--pool=eventlet``

### Notes

In general use, the app launches:
 
 - one process for the camera. Each instance of the app is expected to handle one camera, at most.
 - one process for the shared object manager. Only processes needing immediate access to the camera results
   (storage, mostly) are included.
 - at least one process per-backend. Each backend can have multiple processes.
 
Celery worker processes are just that - Celery worker processes. Most of the configuration is Celery-specific,
including number of processes launched.
 
Post-processing of the images are run in separate processes, typically on other machines. Post-processing
requires using a Redis server, and (at least) the Celery backend for messaging.

It's possible to use a storage-only backend, e.g., minio, and use some other means of identifying when new 
images are added. 



