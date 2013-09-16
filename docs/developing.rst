==================
 Developing Rebar
==================

To run the Rebar unittests, ensure Django and django-discover-runner
have been installed::

  $ pip install Django django-discover-runner

Then run the tests using ``django-admin``::

  $ django-admin.py test --settings=rebar.test_settings rebar
