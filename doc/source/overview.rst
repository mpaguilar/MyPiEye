Overview
========

MyPiEye is a simple motion-detection system which uploads to Google Drive. I don't like having to pay monthly fees
to yet another company, and I have plenty of "cloud" space, so why not use it?

An RPi, a cheap webcam, add some internet connectivity, and get a cheap security cam.

No monthly fees. Music to my cheap ears and skinny wallet.

.. note::

    You don't need to use Google drive. It will save files locally, just fine.

.. note::

    You don't have to use all of the AWS features, either. You can use just S3, without the metadata.

.. warning::

    Google drive is upload-only. Viewing and managing the images is a manual process done through Google Drive.
    Setting things up takes a little more work.

    Same thing with AWS, but I'm working on it.

There aren't any services exposed by this app, configuration is via .ini file, and there's no live view.

It does run on an RPi, easily. File storage is run in separate processes, with scanning/compare happening in
the main app.

It also runs really well on a standard PC.