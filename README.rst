=======
 rebar
=======

.. image:: https://travis-ci.org/eventbrite/rebar.png?branch=master
   :target: https://travis-ci.org/eventbrite/rebar

.. image:: https://coveralls.io/repos/eventbrite/rebar/badge.png?branch=master
   :target: https://coveralls.io/r/eventbrite/rebar?branch=master


**Rebar** makes your Django Forms stronger.

Rebar is a collection of tools that make it easier to work with Django
forms and develop more complex abstractions. Rebar includes:

* Form Groups

  Treat a heterogeneous set of Forms or FormSets as a single logical
  Form.

* State Validators

  Validate that a Form is in a particular state. For some applications
  you want to allow users to save their work, even if they haven't
  completed the task. *State Validators* allow you to abstract the
  validation for specific states.

* Testing Tools

  Easily generate dictionaries of form data from a Form, FormSet, and
  FormGroup instances for use in unit tests.

Rebar supports Django 1.5 and later on Python 2.6, 2.7, and 3.3.


Running Tests
=============

You can run the tests with ``setup.py``::

  $ python setup.py test

Tox allows you to run the tests against the supported dependency matrix.

::

   $ pip install tox
   $ tox

Rebar prefers Tox 2.0 or later.
