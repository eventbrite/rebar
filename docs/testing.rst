====================
 Testing with Rebar
====================

.. testsetup::

   import rebar.tests
   rebar.tests.setup()

Rebar includes some helpers for writing unit tests for Django Forms.

Generating Form Data
====================

A common pattern for testing Forms and Formsets is to create a dict of
form data to use when instantiating the form. When dealing with a
large form, or a form with lots of initial values, keeping the test in
sync can be cumbersome.

:func:`rebar.testing.flatten_to_dict` takes a Form, Formset, or
FormGroup, and returns its fields as a dict. This allows you to create
an unbound form, flatten it, and use the resulting dict as data to
test with.

If passed a FormSet, the return of ``flatten_to_dict`` will include
the ManagementForm_.

For example, if you have a form with a required field:

.. testcode::

   from django import forms

   class NameForm(forms.Form):

       first_name = forms.CharField(required=True)

You can create an unbound version of the form to generate the form
data dict from.

.. doctest::

  >>> from rebar.testing import flatten_to_dict
  >>> unbound_form = NameForm()
  >>> form_data = flatten_to_dict(unbound_form)
  >>> form_data['first_name'] = 'Larry'
  >>> NameForm(data=form_data).is_valid() is True
  True

This is an obviously oversimplified example, but ``flatten_to_dict``
allows you to focus your test on the fields that actually matter in
that context.

If a ModelForm is passed to ``flatten_to_dict`` with a foreign key,
the related object's primary key, if any, will be used as the value
for that field. This correlates with how Django treats those fields in
form proessing.


Empty Form Data for Formsets
============================

FormSets allow you to create a view that contains multiple instances
of the same form. FormSets have a convenience property, `empty_form`_,
which returns an empty copy of the form, with its index set to the
placeholder ``__prefix__``.

Rebar provides a convience function,
:func:`rebar.testing.empty_form_data`, which takes the empty form and
returns the form data dict with the prefix correctly filled in. For
example, if the FormSet contains a single item, the prefix will be set
to 2.

For example, assume we make a FormSet from our example ``NameForm``
above.

.. testcode::

   from django.forms import formsets
   NameFormSet = formsets.formset_factory(form=NameForm)

When we instantiate that FormSet, it will have a single form in it,
which is empty (ie, we didn't start with any forms). That forms prefix
contains "1", indicating its place in the sequence.

.. doctest::

   >>> formset = NameFormSet()
   >>> len(formset)
   1
   >>> formset[0].prefix
   u'form-0'

The empty_form property contains a copy of the NameForm, with its
prefix set to the ``__prefix__`` sentinel.

.. doctest::

   >>> formset.empty_form  # doctest: +ELLIPSIS
   <NameForm ...>
   >>> formset.empty_form.prefix
   u'form-__prefix__'

If we pass the FormSet to ``empty_form_data``, we'll get a dict of
data for the next form in the sequence.

.. doctest::

   >>> from rebar.testing import empty_form_data
   >>> empty_form_data (formset)
   {u'form-1-first_name': None}

You can also specify a specific index for the generated form data.

   >>> empty_form_data (formset, index=42)
   {u'form-42-first_name': None}

.. _ManagementForm: https://docs.djangoproject.com/en/1.5/topics/forms/formsets/#understanding-the-managementform
.. _`empty_form`: https://docs.djangoproject.com/en/1.5/topics/forms/formsets/#empty-form
