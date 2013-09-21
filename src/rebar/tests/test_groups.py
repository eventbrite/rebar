"""
Tests for FormGroups
"""

from django.utils.unittest import TestCase

from django.core.exceptions import ValidationError
from django.forms.util import ErrorList

from mock import patch

from rebar.tests.helpers import (
    EmailForm,
    FakeModel,
    NameForm,
)


from rebar.groups2 import formgroup_factory, FormGroup


class FormGroupFactoryTests(TestCase):

    def test_form_group_factory_returns_formgroup_subclass(self):

        fg_class = formgroup_factory([])
        self.assertTrue(
            issubclass(fg_class, FormGroup)
        )

    def test_form_group_factory_takes_member_sequence(self):

        fg_class = formgroup_factory(
            (NameForm,
             EmailForm,
            ),
        )

        self.assertTrue(
            issubclass(fg_class, FormGroup)
        )

    def test_formgroup_factory_can_take_baseclass(self):

        class MyFormGroup(FormGroup):
            pass

        fg_class = formgroup_factory(
            (NameForm,
             EmailForm,
            ),
            formgroup=MyFormGroup,
        )

        self.assertTrue(
            issubclass(fg_class, MyFormGroup)
        )

    def test_formgroup_factory_baseclass_must_subclass_formgroup(self):

        with self.assertRaises(TypeError):
            fg_class = formgroup_factory(
                (NameForm,
                 EmailForm,
                ),
                formgroup=object,
            )


class FormGroupAccessorTests(TestCase):


    def test_formgroup_length_is_number_of_members(self):

        formgroup = formgroup_factory(
            (NameForm,
             EmailForm,
            ),
        )()
        self.assertEqual(len(formgroup), 2)

        formgroup = formgroup_factory(
            (NameForm,
            ),
        )()
        self.assertEqual(len(formgroup), 1)

    def test_formgroup_members_accessible_as_forms_prop(self):

        formgroup = ContactFormGroup()
        self.assertEqual(len(formgroup.forms), 2)

    def test_formgroup_members_accessible_by_index(self):

        formgroup = ContactFormGroup()

        self.assertIsInstance(formgroup[0], NameForm)
        self.assertIsInstance(formgroup[1], EmailForm)

        self.assertTrue('first_name' in formgroup[0].fields)

    def test_formgroup_member_accessible_by_name(self):

        formgroup = ContactFormGroup()

        self.assertEqual(
            formgroup.name, formgroup[0]
        )
        self.assertEqual(
            formgroup.email, formgroup[1]
        )

    def test_formgroup_member_name_configurable(self):

        formgroup = formgroup_factory(
            (
                (NameForm, 'named_form',),
            ),
        )()

        self.assertIsInstance(formgroup.named_form, NameForm)


class FormGroupPrefixTests(TestCase):

    def test_formgroup_has_prefix(self):

        formgroup = ContactFormGroup()
        self.assertEqual(formgroup.prefix, formgroup.get_default_prefix())

    def test_formgroup_prefix_overridable(self):

        formgroup = ContactFormGroup(prefix='testing')
        self.assertEqual(formgroup.prefix, 'testing')
        self.assertEqual(formgroup.name.prefix, 'testing-name')

    def test_formgroup_prefix_is_inherited_by_members(self):

        formgroup = ContactFormGroup()
        self.assertEqual(formgroup.name.prefix, 'group-name')

    def test_html_id_adds_prefix(self):

        formgroup = ContactFormGroup()

        self.assertEqual(
            formgroup.html_id('testing'),
            'id_group-testing',
        )

    def test_html_id_uses_auto_id(self):

        formgroup = ContactFormGroup(auto_id='foo_%s')

        self.assertEqual(
            formgroup.html_id('testing'),
            'foo_group-testing',
        )

    def test_html_id_delegation(self):

        formgroup = ContactFormGroup()

        self.assertEqual(
            formgroup.html_id('testing', form=formgroup.name),
            'id_group-name-testing',
        )


class FormGroupInitialTests(TestCase):

    def test_pass_initial_data_to_members(self):

        form_group = ContactFormGroup(
            initial={
                'first_name': 'Joe',
            },
        )

        self.assertEqual(
            form_group.name.initial.get('first_name'),
            'Joe',
        )
        self.assertEqual(
            form_group.name['first_name'].value(),
            'Joe',
        )



class FormGroupValidationTests(TestCase):

    def test_form_group_not_bound_by_default(self):

        self.assertFalse(ContactFormGroup().is_bound)

    def test_form_group_bound_when_data_provided(self):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': None,
        }
        self.assertTrue(ContactFormGroup(data=form_data).is_bound)

    def test_members_are_bound_when_group_is(self):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': None,
        }
        form_group = ContactFormGroup(data=form_data)

        self.assertTrue(form_group.name.is_bound)

    def test_members_unbound_when_group_is(self):
        form_group = ContactFormGroup()

        self.assertFalse(form_group.is_bound)
        self.assertFalse(form_group.name.is_bound)

    def test_unbound_group_is_invalid(self):

        form_group = ContactFormGroup()
        self.assertFalse(form_group.is_bound)
        self.assertFalse(form_group.is_valid())

    def test_unbound_group_errors_list_is_empty(self):

        form_group = ContactFormGroup()
        self.assertFalse(form_group.is_bound)
        self.assertEqual(form_group.errors, [])

    def test_group_is_valid_if_members_are(self):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }
        form_group = ContactFormGroup(data=form_data)

        self.assertTrue(form_group.name.is_valid())
        self.assertTrue(form_group.email.is_valid())

        self.assertTrue(form_group.is_valid())

    def test_errors_contains_all_member_errors(self):

        form_data = {
            'group-name-last_name': 'Doe',
        }
        form_group = ContactFormGroup(data=form_data)

        errors = form_group.errors
        self.assertEqual(len(errors), 2)

        self.assertTrue('first_name' in errors[0])
        self.assertTrue('email' in errors[1])

    def test_errors_contains_all_member_errors_when_valid(self):
        """When bound and valid, errors contains empty error dicts."""

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }
        form_group = ContactFormGroup(data=form_data)

        self.assertTrue(form_group.is_valid())
        self.assertEqual(form_group.errors, [{}, {}])

    @patch.object(FormGroup, 'clean')
    def test_accessing_errors_calls_formgroup_clean(self, clean_mock):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }

        form_group = ContactFormGroup(data=form_data)
        self.assertEqual(form_group.errors, [{}, {}])

        clean_mock.assert_called_once_with()

    @patch.object(FormGroup, 'clean')
    def test_is_valid_calls_formgroup_clean(self, clean_mock):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }

        form_group = ContactFormGroup(data=form_data)
        self.assertTrue(form_group.is_valid())

        clean_mock.assert_called_once_with()

    @patch.object(FormGroup, 'clean')
    def test_exceptions_from_clean_in_group_errors(self, clean_mock):

        clean_mock.side_effect = ValidationError('Test Exception')

        form_group = ContactFormGroup(data={})
        self.assertFalse(form_group.is_valid())

        self.assertEqual(
            form_group.group_errors(),
            ['Test Exception'],
        )

    def test_group_errors_is_empty_error_list_when_valid(self):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }

        form_group = ContactFormGroup(data=form_data)
        self.assertTrue(form_group.is_valid())

        self.assertEqual(form_group.group_errors(), ErrorList())

    def test_group_errors_class_customizable(self):

        class MyErrorList(ErrorList):
            pass

        form_group = ContactFormGroup(
            data={},
            error_class=MyErrorList,
        )

        self.assertFalse(form_group.is_valid())
        self.assertIsInstance(form_group.group_errors(), MyErrorList)

    def test_is_valid_only_cleans_once(self):
        """Repeated calls to is_valid will only call clean on members once.

        """

        form_group = ContactFormGroup(data={})
        self.assertEqual(form_group.name.clean_count, 0)

        form_group.is_valid()
        self.assertEqual(form_group.name.clean_count, 1)

        form_group.is_valid()
        self.assertEqual(form_group.name.clean_count, 1)


class MemberArgsTests(TestCase):

    def test_pass_extra_kwargs(self):
        """You can pass extra kwargs to form group members"""

        form_group = ContactFormGroup(
            member_kwargs=dict(
                name=dict(
                    test_kwarg=True,
                ),
            ),
        )

        self.assertEqual(form_group.name.kwargs.get('test_kwarg'), True)


class FormGroupSaveTests(TestCase):

    def test_instance_passed_to_members(self):

        form_group = ContactFormGroup(instance=FakeModel())
        self.assertEqual(form_group.instance, form_group.name.instance)
        self.assertEqual(form_group.instance, form_group.email.instance)

    ## def test_has_save_if_instance_passed(self):

    ##     form_group = ContactFormGroup(instance=FakeModel())

    ##     self.assertTrue(hasattr(form_group, 'save'))
    ##     self.assertTrue(callable(form_group.save))

    ## def test_save_omitted_if_instance_omitted(self):

    ##     form_group = ContactFormGroup(instance=FakeModel())

    ##     self.assertFalse(hasattr(form_group, 'save'))

    def test_save_calls_member_saves(self):

        form_data = {
            'group-name-first_name': 'John',
            'group-name-last_name': 'Doe',
            'group-email-email': 'john.doe@example.com',
        }
        form_group = ContactFormGroup(
            data=form_data,
            instance=FakeModel(),
        )

        form_group.save()

        self.assertTrue(form_group.name.called['save'])
        self.assertTrue(form_group.email.called['save'])

    def test_save_calls_instance_save_once(self):

        with patch.object(FakeModel, 'save') as save_mock:

            form_data = {
                'group-name-first_name': 'John',
                'group-name-last_name': 'Doe',
                'group-email-email': 'john.doe@example.com',
            }
            form_group = ContactFormGroup(
                data=form_data,
                instance=FakeModel(),
            )

            form_group.save()

            save_mock.assert_called_once_with(commit=True)

    def test_inline_formsets_saved_after_parent_saved(self):
        pass

    def test_save_calls_save_m2m_after_parent_saved(self):
        pass

    def test_save_calls_save_related_after_parent_saved(self):
        pass


ContactFormGroup = formgroup_factory(
    (NameForm,
     EmailForm,
     ),
)
