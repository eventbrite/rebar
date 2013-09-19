=============
 Form Groups
=============

Rebar Form Groups provide a way to manipulate a heterogenous set of
Forms or FormSets as a single entity.

.. warning:: Restrictions

   To treat a set of heterogenous Forms or FormSets as a single
   entity, some restrictions are necessary. Specifically, every member
   of a Form Group will receive the same arguments at instantiation.

   This means if you're using ModelForms and ModelFormSets, *every*
   member has the same ``instance``. If your data model does not meet
   this requirement, you'll need to work around it to use Form Groups.


Declaration
===========

Form Groups classes are created using a factory function, much like
Form Sets. The only required argument is the sequence of members for
the Form Group. A Form Group may contain any number of Forms_ or
FormSets_.

Let's take an example where we might split form validation for a
Contact into basic information and address information.

.. testcode::

   from django import forms

   class ContactForm(forms.Form):

       first_name = forms.CharField(
           label="First Name")
       last_name = forms.CharField(
           label="Last Name")
       email = forms.EmailField(
           label="Email Address")

   class AddressForm(forms.Form):

       street = forms.CharField()
       city = forms.CharField()
       state = forms.CharField()

A Form Group allows you to combine the two and treat them as one.

.. testcode::

   from rebar.groups2 import formgroup_factory

   ContactFormGroup = formgroup_factory(
       (
           (ContactForm, 'contact'),
           (AddressForm, 'address'),
       ),
   )

The ``ContactFormGroup`` class can now be instantiated like any other
form.

.. doctest::

   >>> ContactFormGroup()  # doctest: +ELLIPSIS
   <rebar.groups2.FormGroup object at ...>


Using Form Groups
=================

Form Groups attempt to "look" as much like a single form as possible.
Note that I say *as possible*, since they are a different creature,
you can't use them completely without knowledge. The goal is to make
them similar enough to work with Django's `class based views`_

Accessing Member Forms
----------------------

Once you've instantiated a Form Group, its members are accesible
either by index or name.

.. doctest::

   >>> form_group = ContactFormGroup()
   >>> form_group.contact
   <ContactForm object at ...>
   >>> form_group.address
   <AddressForm object at ...>
   >>> form_group[0] == form_group.contact
   True

The members are provided in the order of declaration.

Form Prefixes
-------------

Form Groups have a prefix_, much like FormSets, and sets the prefix on
each member.

.. doctest::

   >>> form_group = ContactFormGroup()
   >>> form_group.prefix
   'group'
   >>> form_group.contact.prefix
   'group-contact'

You can also override the default prefix.

.. doctest::

   >>> form_group = ContactFormGroup(prefix='contact')
   >>> form_group.prefix
   'contact'
   >>> form_group.contact.prefix
   'contact-contact'

Validation
----------

Passing Extra Arguments
-----------------------

Most arguments that you pass to a Form Group will be passed in to its
members, as well. Sometimes, however, you want to pass arguments to
specific members of the Form Group. The ``member_kwargs`` parameter
allows you to do this.

``member_kwargs`` is a dict, where each key is the name of a Form
Group member, and the value is a dict of keyword arguments to pass to
that member.

For example:

.. doctest::

  >>> form_group = ContactFormGroup(
  ...     member_kwargs={
  ...         'address': {
  ...             'prefix': 'just_address',
  ...         },
  ...     },
  ... )
  >>> form_group.contact.prefix
  'group-contact'
  >>> form_group.address.prefix
  'just_address'

In this example we override the prefix argument. A more realistic
application is when you have a heavily customized form subclass that
requires some additional piece of information.

Form Groups in Views
====================

Using in Class Based Views
--------------------------

Rendering Form Groups
---------------------


.. _Forms:
.. _FormSets:
.. _`class based views`:
.. _prefix:
