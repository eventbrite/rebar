"""
Tests for FormGroups
"""

from django import forms
from unittest import TestCase

from rebar.group import formgroup_factory, FormGroup


class FormGroupTests(TestCase):

    def test_factory(self):

        FormGroupClass = formgroup_factory([])
        self.assert_(issubclass(FormGroupClass, FormGroup))

    def test_creation(self):
        """A FormGroup can hold Forms or FormSets."""

    def test_form_access(self):
        """You can access individual Forms as properties."""

        FormGroupClass = formgroup_factory([
            (TestForm,  'test1'),
            (TestForm2, 'test2'),
            ])

        fg = FormGroupClass(instance=CallSentinel())

        self.assert_(len(fg), 2)
        self.assert_(isinstance(fg.test1, TestForm))
        self.assert_(isinstance(fg.test2, TestForm2))

        self.assert_(fg.test1 == fg.forms[0])
        self.assert_(fg.test2 == fg.forms[1])

    def test_form_prefixes(self):

        FormGroupClass = formgroup_factory([
            (TestForm,  'test1'),
            (TestForm2, 'test2'),
            ])

        instance = CallSentinel()
        fg = FormGroupClass(instance=instance)

        # members have different prefixes
        self.assert_(fg.forms[0].prefix != fg.forms[1].prefix)

        # the prefixes all start with the same string
        self.assert_(fg.forms[0].prefix.find(fg.prefix) == 0)
        self.assert_(fg.forms[1].prefix.find(fg.prefix) == 0)

    def test_save(self):
        """Calling .save() calls save on all elements."""

        FormGroupClass = formgroup_factory([
            (TestForm,  'test1'),
            (TestForm2, 'test2'),
            ])

        instance = CallSentinel()
        fg = FormGroupClass(instance=instance)

        # assert our save sentinel values is False to start with
        self.assertFalse(instance.called.get('save', False))
        self.assertFalse(fg.forms[0].called.get('save', False))
        self.assertFalse(fg.forms[1].called.get('save', False))

        # calling .save() will call .save() on both Forms, flipping the flag
        fg.save()
        self.assert_(fg.forms[0].called.get('save', False))
        self.assert_(fg.forms[1].called.get('save', False))

        # this also calls save() on the instance
        self.assert_(instance.called.get('save', False))

    def test_validation(self):

        FormGroupClass = formgroup_factory([
            (TestForm,  'test1'),
            (TestForm2, 'test2'),
            ])

        # create some form data -- missing a required field
        data = {
            'group-test1-name' : '',
            'group-test2-name' : 'Anita Man',
            }

        fg = FormGroupClass(data, instance=CallSentinel())
        self.assertFalse(fg.is_valid())
        self.assert_(fg.forms[0].called.get('is_valid', False))
        self.assert_(fg.forms[1].called.get('is_valid', False))

        # formgroup.errors is a dict of error dicts
        # -- TestForm2 is valid
        self.assertFalse(fg.errors[1])
        # -- TestForm is not valid
        self.assert_(fg.errors[0])

        # create some form data that passes validation
        data = {
            'group-test1-name' : 'Anita Man',
            'group-test2-name' : 'Mike Rotch',
            }

        fg = FormGroupClass(data, instance=CallSentinel())
        self.assert_(fg.is_valid())
        self.assert_(fg.forms[0].called.get('is_valid', False))
        self.assert_(fg.forms[1].called.get('is_valid', False))


# Support objects for testing FormGroups --

class CallSentinel(object):

    def __init__(self, *args, **kwargs):
        super(CallSentinel, self).__init__(*args, **kwargs)

        self.called = {}

    def save(self, *args, **kwargs):
        self.called['save'] = True

    def is_valid(self):
        self.called['is_valid'] = True

        return super(CallSentinel, self).is_valid()

class TestForm(CallSentinel, forms.Form):

    name = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):

        self.instance = kwargs.pop('instance')

        super(TestForm, self).__init__(*args, **kwargs)

class TestForm2(TestForm):
    pass
