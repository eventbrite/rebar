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

   from rebar.group import formgroup_factory

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
   <rebar.group.FormGroup ...>


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
   <ContactForm ...>
   >>> form_group.address
   <AddressForm ...>
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

FormGroups use a similar approach to validation as FormSets. Calling
``is_valid()`` on a FormGroup instance will return ``True`` if all
members are valid.

The ``errors`` property is a list of ErrorLists, in group member
order.

Just as FormSets support a `clean method`_ for performing any
validation at the set level, FormGroups provide a ``clean`` hook for
performing any validation across the entire group. In order to take
advantage of this hook, you'll need to subclass ``FormGroup``.

.. testcode::

   from django.core.exceptions import ValidationError
   from rebar.group import FormGroup

   class BaseInvalidFormGroup(FormGroup):

       def clean(self):
           raise ValidationError("Group validation error.")

This class is passed to ``formgroup_factory`` and used as the base
class for the new Form Group.

.. testcode::

   InvalidFormGroup = formgroup_factory(
       (
           (ContactForm, 'contact'),
           (AddressForm, 'address'),
       ),
       formgroup=BaseInvalidFormGroup,
   )

When you instantiate the form group with data, any errors raised by
the ``clean`` method are available as "group errors":

.. doctest::

   >>> bound_formgroup = InvalidFormGroup(data={})
   >>> bound_formgroup.is_valid()
   False
   >>> bound_formgroup.group_errors()
   [u'Group validation error.']

There are two things to note about group level validation:

* Unlike ``Form.clean()``, the return value of ``FormGroup.clean()``
  is unimportant
* Unlike accessing the ``errors`` property of Forms, FormSets, or
  FormGroups, ``FormGroup.group_errors()`` *does not* trigger
  validation.

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

Form Groups are designed to be usable with Django's `class based
views`_. The group class can be specified as the `form_class`_ for an
edit view. If you need to pass additional arguments, you can override
the `get_form_kwargs`_ method to add the ``member_kwargs``.

Rendering Form Groups
---------------------

Form Groups do not provide shortcuts for rendering in templates. The
shortest way to emit the members is to simply iterate over the
members::

  {% for form in formgroup.forms %}

      {{ form.as_p }}

  {% endfor %}

Form Groups do provide media_ definitions that roll-up any media found
in members.

.. _Forms: https://docs.djangoproject.com/en/1.5/ref/forms/api/
.. _FormSets: https://docs.djangoproject.com/en/1.5/topics/forms/formsets/
.. _`class based views`: https://docs.djangoproject.com/en/1.5/topics/class-based-views/
.. _prefix: https://docs.djangoproject.com/en/1.5/ref/forms/api/#prefixes-for-forms
.. _`clean method`: https://docs.djangoproject.com/en/1.5/topics/forms/formsets/#custom-formset-validation
.. _media: https://docs.djangoproject.com/en/1.5/topics/forms/media/
.. _`form_class`: https://docs.djangoproject.com/en/1.5/ref/class-based-views/mixins-editing/#django.views.generic.edit.FormMixin.form_class
.. _`get_form_kwargs`: https://docs.djangoproject.com/en/1.5/ref/class-based-views/mixins-editing/#django.views.generic.edit.FormMixin.get_form_kwargs
