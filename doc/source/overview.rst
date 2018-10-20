Overview
========

MyPiEye is a simple motion-detection system which uploads to Google Drive. I don't like having to pay monthly fees
to yet another company, and I have plenty of "cloud" space, so why not use it?

An RPi, a cheap webcam, add some internet connectivity, and get remote backups of a security cam for about $65, total.

No monthly fees. Music to my cheap ears and skinny wallet.

.. warning::

    This is upload-only. Viewing and managing the images is a manual process done through Google Drive.

There aren't any services exposed by this app, configuration is via .ini file, and there's no live view.

Since this is using Google Drive, if you do too much (how much, I don't know) you might be cut off. Don't
get crazy, is what I'm saying. One or two cameras shouldn't be a problem.

It does run on an RPi, easily. File storage is run in separate processes, with scanning/compare happening in
the main app.

It also runs really well on a standard PC.