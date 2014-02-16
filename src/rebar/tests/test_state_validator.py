"""StateValidator Test Suite"""

from unittest import TestCase
from django.core.exceptions import ValidationError

from rebar.tests.helpers import (
    NameForm,
)

from rebar.validators import (
    StateValidator,
    statevalidator_factory,
)


def required(value):
    if not bool(value):
        raise ValidationError("This field is required")


class StateValidatorTests(TestCase):

    def test_factory(self):
        """We can construct StateValidator instances using a factory."""

        TestValidator = statevalidator_factory({
            'name': (required,),
        })

        self.assert_(isinstance(TestValidator, type))
        self.assert_(issubclass(TestValidator, StateValidator))

        # instantiate our new class
        validator = TestValidator()

        self.assert_(validator.is_valid({'name': 'Foo'}))
        self.assertFalse(validator.is_valid({}))

    def test_is_valid_runs_validators(self):

        # set up a dummy validator function that just counts the
        # number of calls
        def call(val):
            call.num_calls += 1
            return True
        call.num_calls = 0

        TestValidator = statevalidator_factory({
            'name': (call, call,),
            'address': (call,),
        })

        # instantiate our new class
        validator = TestValidator()
        validator.is_valid({'name': 'foo', 'address': 'bar'})
        self.assertEqual(call.num_calls, 3)

        # the validators will be called even if no value is provided
        call.num_calls = 0
        validator.is_valid({})
        self.assertEqual(call.num_calls, 3)

    def test_disabled_validators(self):

        TestValidator = statevalidator_factory({
            'name': (required,),
        })

        # instantiate our new class and test that an empty dict is not
        # valid.
        validator = TestValidator()
        self.assertFalse(validator.is_valid({}))
        self.assert_(validator.errors({}))

        # disable the validator; calls to is_valid will now return True
        validator.disable()
        self.assertFalse(validator.enabled)
        self.assert_(validator.is_valid({}))
        self.assertFalse(validator.errors({}))

        # re-enable the validator
        validator.enable()
        self.assertTrue(validator.enabled)
        self.assertFalse(validator.is_valid({}))
        self.assertTrue(validator.errors({}))

    def test_errors_returns_error_dict(self):
        TestValidator = statevalidator_factory({
            'name': (required,),
        })

        # instantiate our new class and pass it invalid data
        validator = TestValidator()
        errors = validator.errors({})
        self.assertEqual(list(errors.keys()), ['name'])
        self.assert_(isinstance(errors['name'], list))

    def test_validator_validates_form_cleaned_data(self):

        TestValidator = statevalidator_factory({
            'last_name': (required,),
        })
        validator = TestValidator()

        form = NameForm(
            data={
                'first_name': 'Joe',
                'last_name': 'Smith',
            },
        )

        # this is a valid form
        self.assertTrue(form.is_valid())
        self.assertTrue(form.is_bound)

        # it also passes the state validator
        self.assertTrue(validator.is_valid(form))

        # if we monkey with the cleaned_data, it will fail
        del form.cleaned_data['last_name']
        self.assertFalse(validator.is_valid(form))


    def test_validator_validates_unbound_form_initial_data(self):

        TestValidator = statevalidator_factory({
            'last_name': (required,),
        })
        validator = TestValidator()

        form = NameForm(
            initial={
                'first_name': 'Joe',
            },
        )

        self.assertFalse(form.is_bound)

        self.assertFalse(validator.is_valid(form))
        self.assertTrue('last_name' in validator.errors(form))

    def test_validator_errors_uses_field_keys(self):

        TestValidator = statevalidator_factory({
            'last_name': (required,),
        })
        validator = TestValidator()

        form = NameForm(
            data={
                'first_name': 'Joe',
            },
        )

        self.assertFalse(validator.is_valid(form))
        self.assertEqual(
            validator.errors(form),
            {'last_name': [
                'This field is required',
                ],
            },
        )
