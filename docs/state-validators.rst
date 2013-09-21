.. :py:module:: rebar.validators

==================
 State Validators
==================

There are times when it's useful to have validation logic above and
beyond what a form applies. For example, a CMS might have very lax
validation for saving a document in progress, but enforce additional
validation for publication.

State Validators provide a method for encapsulating validation logic
for states above and beyond basic form or model validation.

State Validators are made up of individual validation functions, and
provides error information about failures, if any. They are similar to
the validators in Forms_ or Models_, in that you describe validators
on a field basis. State Validators can be used to validate forms,
models, and dicts of values.


Creating Validators
===================

A State Validator consists of a collection of validation functions. A
validation function takes an input value and raises a ValidationError_
if the value is invalid.

For example, validation functions that enforce a field as "required"
and one that require an integer value might be written as follows.

.. testcode::

   from django.core.exceptions import ValidationError


   def required(value):
       if not bool(value):
           raise ValidationError("This field is required.")

   def is_int(value):
       try:
           int(value)
       except (ValueError, TypeError):
           raise ValidationError("An integer is required.")

These are wrapped into a State Validator using the
:py:func:`.statevalidator_factory`.

.. testcode::

   from rebar.validators import statevalidator_factory

   AgeValidator = statevalidator_factory(
       {
           'age': (required, is_int,),
       },
   )

``statevalidator_factory`` takes a dict which maps field names to one
or more validator functions, and returns a :py:class:`.StateValidator`
class.

Note that when validating, *all* validators will be called for each
field, regardless of whether a preceeding validator raises an
exception. The goal is to collect all errors that need to be corrected.

Validating Data
===============

Once a StateValidator class has been created, it can be used to
validate data. State Validators can validate a simple dict of fields,
a form, or a model. When validating a form, its ``cleaned_data`` will
be validated if it is bound, otherwise the initial data values will be
used.

.. doctest::

   >>> validator = AgeValidator()
   >>> validator.is_valid({'age': 10})
   True
   >>> validator.is_valid({'age': 'ten'})
   False
   >>> validator.is_valid({})
   False

Accessing Errors
----------------

In addition to determining if the data is valid or not, the errors
raised by the validation functions can be retrieved through the
``errors`` method. :py:meth:`.StateValidator.errors`
returns a dict, where the keys correspond to field names, and the
values are a sequence of errors. ``errors`` returns an empty dict if
there are no errors.

.. doctest::

   >>> validator = AgeValidator()
   >>> validator.errors({'age': 10})
   {}
   >>> validator.errors({'age': 'ten'})
   {'age': [u'An integer is required.']}
   >>> validator.errors({})
   {'age': [u'This field is required.', u'An integer is required.']}


Enabling & Disabling Validators
-------------------------------

State Validators may be disabled or re-enabled. A disabled validator
is always valid, and returns no errors.

.. doctest::

   >>> validator.enabled
   True
   >>> validator.disable()
   >>> validator.is_valid({})
   True
   >>> validator.errors({})
   {}

.. doctest::

   >>> validator.enabled
   False
   >>> validator.enable()
   >>> validator.is_valid({})
   False


.. _Forms:
.. _Models:
.. _ValidationError:
