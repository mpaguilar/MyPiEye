Configuration
=============

It needs to be configured before use. The app needs your permission to use Google drive, and the folder on the drive
needs to be created using those credentials. There are some local folders to be created, as well.

Start with one of the sample .ini files, and modify to your taste.

.ini Configuration
------------------

Configuration is key-value pairs, in an .ini style. To disable a feature, like ``s3`` or ``gdrive``, remark out its
section.

* ``[global]`` handles things like which camera to use, working and save directories.

* ``[minsizes]`` sets the smallest "box" that will be captured. This helps prevent false positives
    when a leaf scurries across your lawn.

* ``[ignore]`` specfies boxes to ignore. The pattern is top-start, left-start, width, length.
    Multiple keys can be used, but they must be unique. This can be tricky, because the values depend on the
    capture resolution.

* ``[gdrive]`` Settings for saving to GDrive. Note that you must set up the application, then authorize this instance.

* ``[s3]`` AWS settings, for the bucket and optional database.

Google Configuration
--------------------
This assumes you know something about Google APIs setup and configuration.


Setting up the application
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use https://console.developers.google.com/ to set up the application, and give it access to the
``https://www.googleapis.com/auth/drive.file`` scope.


Getting an access token
^^^^^^^^^^^^^^^^^^^^^^^

The first time ``mypieye configure`` is run, you will be prompted with a google.com URL and a short code ("XXXX-XXXX"). This is what
permits the application to use your GDrive. It asks for minimal permissions, and can only access folders and files
it creates.

Once validated, it will create the folder at google, and any local folders.

There's two parts to uploading to Google.
 - Create an application to get the CLIENT_ID and CLIENT_SECRET, and update the ini file.
 - Creating an access token for a specific device

AWS Configuration
-----------------

Create a key with permissions to S3 and DynamoDB.

Create the bucket and DynamoDB tables.


