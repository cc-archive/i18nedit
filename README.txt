=====
Herder
=====

:Version: $LastChangedRevision: 4737 $
:Author: Nathan R. Yergler <nathan@creativecommons.org>
:Organization: `Creative Commons <http://creativecommons.org>`_
:Copyright: 
   2008, Nathan R. Yergler, Creative Commons; 
   licensed to the public under the `MIT license 
   <http://opensource.org/licenses/mit-license.php>`_.

Herder is a web application for editting and managing translations.

Installation and Setup
======================

Install ``herder`` using easy_install::

    easy_install herder

Make a config file as follows::

    paster make-config herder config.ini

Tweak the config file as appropriate and then setup the application::

    paster setup-app config.ini

Then you are ready to go.

A development config file, cunningly named ``development.ini``, is provided.

Development
===========

``Herder`` uses `zc.buildout <http://python.org/pypi/zc.buildout>`_ to
manage dependencies and the deployment process.  To work on
``Herder``, you'll need to do the following::

  $ python2.5 bootstrap/bootstrap.py
  $ ./bin/buildout

Buildout will retrieve the necessary dependencies and install them in
the ``eggs`` sub-directory.  After buildout completes you can
initialize the database and run the application::

  $ ./bin/paster setup-app development.ini
  $ ./bin/paster serve --reload development.ini

