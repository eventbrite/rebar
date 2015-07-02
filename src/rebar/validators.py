from copy import deepcopy

from django.core.exceptions import ValidationError
from django.db import models
from django.forms import forms, formsets
from rebar.dix import ErrorList


class StateValidatorFormMixin(object):
    """Mixin for adding state validators to forms.

    Subclasses are expected to define the state_validators property,
    which is a mapping of states to StateValidator objects."""

    state_validators = {}

    def __init__(self, *args, **kwargs):

        # Make a copy of the state validators so mutating them for one
        # for instance does not impact other instances.
        self.state_validators = deepcopy(self.__class__.state_validators)

        self.state_validators = dict([
            (state, self._make_validator(state, validator))
             for state, validator in self.__class__.state_validators.items()
            ])
        return super(StateValidatorFormMixin, self).__init__(*args, **kwargs)

    def _make_validator(self, state, validator):

        if isinstance(validator, type):
            # need to instantiate the state validator
            return validator()
        elif isinstance(validator, dict):
            return type('%sValidator' % state,
                        (StateValidator,),
                        {'validators': validator})()

        # must already be an instantiated instance, just make a copy
        return deepcopy(validator)

    def is_valid(self, *states):
        """Returns True if no errors are thrown for the specified state."""

        # if no state is specified, fallback to the base Form's is_valid
        if not states:
            return super(StateValidatorFormMixin, self).is_valid()

        return all(self.state_validators[state].is_valid(self)
                   for state in states)

    def get_errors(self, state):
        """Return any validation errors raised for the specified state."""

        return self.state_validators[state].errors(self)


class StateValidator(object):
    """Field Validators which must pass for an object to be in a state."""

    validators = {}

    def __init__(self):
        self._enabled = True

    @property
    def enabled(self):
        return self._enabled

    def disable(self):
        """Disable the validator; when disabled, no errors will be returned."""

        self._enabled = False

    def enable(self):
        """Enable the validators."""

        self._enabled = True

    def is_valid(self, instance):
        """Return True if no errors are raised when validating instance.

        instance can be a dict (ie, form.cleaned_data), a form, or a
        model instance. If instance is a form, full_clean() will be
        called.
        """

        errors = self.errors(instance)

        if isinstance(errors, list):
            return not any(errors)

        return not bool(errors)

    def _validate(self, data):
        """Helper to run validators on the field data."""

        errors = {}

        # if the validator is not enabled, return the empty error dict
        if not self._enabled:
            return errors

        for field in self.validators:

            field_errors = []

            for validator in self.validators[field]:
                try:
                    validator(data.get(field, None))
                except ValidationError as e:
                    field_errors += e.messages

            # if there were errors, cast to ErrorList for output convenience
            if field_errors:
                errors[field] = ErrorList(field_errors)

        return errors

    def errors(self, instance):
        """Run all field validators and return a dict of errors.

        The keys of the resulting dict coorespond to field
        names. instance can be a dict (ie, form.cleaned_data), a form,
        a formset, or a model instance.

        If instance is a form, full_clean() will be called if the form
        is bound.

        If instance is a formset, full_clean() will be called on each
        member form, if bound.
        """

        if isinstance(instance, dict):
            return self._validate(instance)

        elif isinstance(instance, forms.BaseForm):
            if instance.is_bound and instance.is_valid():
                return self._validate(instance.cleaned_data)

            return self._validate(dict(
                [
                    (f, instance.initial.get(f, instance[f].value()))
                    for f in self.validators
                    ]
                ))

        elif isinstance(instance, formsets.BaseFormSet):
            if instance.can_delete:
                validate_forms = [
                    form for form in instance.initial_forms
                    if not instance._should_delete_form(form)
                    ] + [
                    form for form in instance.extra_forms
                    if (form.has_changed() and
                        not instance._should_delete_form(form))
                    ]

                return [
                    self.errors(f)
                    for f in validate_forms
                    ]
            else:
                validate_forms = instance.initial_forms + [
                    form for form in instance.extra_forms
                    if form.has_changed()
                    ]
                return [self.errors(f) for f in validate_forms]

        elif isinstance(instance, models.Model):
            return self._validate(dict(
                [(f, getattr(instance, f)) for f in self.validators]
                ))


def statevalidator_factory(field_validators, validator=StateValidator):
    """Return a StateValidator Class with the given validators."""

    attrs = {
        'validators': field_validators,
        }

    return type('StateValidator', (validator,), attrs)
