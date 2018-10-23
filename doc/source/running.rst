Running
=======

I generally setup a folder structure like so:

::

    <root>-cam1
            |
            - tmp
            - save
            mypieye.ini

``mypieye.ini`` can use relative settings, and is pretty easy to copy and paste around.

Set ``cam1`` as the current directory.

``mypieye configure`` will set up directories and authentication. It should be run at least once.

``mypieye run`` will look for a file named ``mypieye.ini`` in the current directory.

``mypieye --help`` offers more.