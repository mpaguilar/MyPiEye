Storage
=======

.. automodule:: MyPiEye.Storage
   :members:

.. autoclass:: MyPiEye.Storage.ImageStorage
   :members:
   :undoc-members:
   :special-members: __init__

Local Filesystem
^^^^^^^^^^^^^^^^

Saves both annotated (with boxes) and non-annotated files.

.. autofunction:: MyPiEye.Storage.local_filesystem.local_save


Google Drive
^^^^^^^^^^^^

Save to Google. Maintaining the folder is completely manual, this only uploads.



.. autoclass:: MyPiEye.Storage.GDriveAuth
   :members:
   :undoc-members:
   :special-members: __init__

.. autoclass:: MyPiEye.Storage.GDriveStorage
   :members:
   :undoc-members:
   :special-members: __init__