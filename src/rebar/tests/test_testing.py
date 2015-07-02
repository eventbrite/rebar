from django import VERSION
from unittest import TestCase

from django.forms.formsets import formset_factory

from rebar.tests.helpers import (
    EmailForm,
    NameForm,
)
from rebar.testing import (
    empty_form_data,
    flatten_to_dict,
)


class EmptyFormDataTests(TestCase):

    def test_returns_dict(self):

        formset = ContactFormSet()

        self.assertIsInstance(empty_form_data(formset), dict)

    def test_returns_all_fields(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset)

        for field in formset.empty_form.fields:
            self.assertTrue(
                [k for k in empty_data if k.endswith(field)]
            )

    def test_keys_include_formset_prefix(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset)

        for field_name in empty_data:
            self.assertTrue(formset.prefix in field_name)

    def test_returns_empty_form_fields_without_prefix_stub(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset)

        for field_name in empty_data:
            self.assertFalse('__prefix__' in field_name)

    def test_contains_next_form_index(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset)

        for field_name in empty_data:
            self.assertTrue(
                str(len(formset.initial_forms) + 1) in
                field_name.split('-'),

                "Field name (%s) does not include next empty form index." %
                field_name
            )

    def test_index_can_be_specified(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset, index=42)

        for field_name in empty_data:
            self.assertTrue(
                '42' in field_name.split('-'),

                "Field name (%s) does not use specified index." %
                field_name
            )

    def test_hidden_initial_fields_included(self):

        formset = ContactFormSet()
        empty_data = empty_form_data(formset)

        # we know that the first_name field in our test form wants to
        # include the initial value in a hidden field
        self.assertEqual(
            empty_data['initial-form-1-first_name'],
            'Larry',
        )


class FlattenToDictTests(TestCase):

    def test_returns_dict(self):

        self.assertIsInstance(flatten_to_dict(NameForm()), dict)

    def test_form_to_dict(self):

        self.assertEqual(
            flatten_to_dict(EmailForm()),
            {'email': ''},
        )

    def test_flatten_respects_prefix(self):

        self.assertEqual(
            flatten_to_dict(EmailForm(prefix='foo')),
            {'foo-email': ''},
        )

    def test_initial_hidden_included(self):

        self.assertEqual(
            flatten_to_dict(NameForm()),
            {
                'initial-first_name': 'Larry',
                'first_name': 'Larry',
                'last_name': '',
            },
        )

    def test_flatten_formset(self):

        expected_result = {
                'initial-form-0-first_name': 'Larry',
                'form-0-first_name': 'Larry',
                'form-0-last_name': '',
                'form-INITIAL_FORMS': 0,
                'form-MAX_NUM_FORMS': 1000,
                'form-TOTAL_FORMS': 1,
            }

        if VERSION >= (1, 7):
            # 1.7 added min-version
            expected_result['form-MIN_NUM_FORMS'] = 0

        self.assertEqual(
            flatten_to_dict(ContactFormSet()),
            expected_result,
        )



ContactFormSet = formset_factory(NameForm)
