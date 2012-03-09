from django.core.exceptions import ValidationError
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.forms.models import BaseInlineFormSet

from django.forms.util import ErrorList

from rebar.validators import StateValidatorFormMixin


class FormGroup(object):
    """Form-like wrapper for a heterogenous collection of Forms.

    A FormGroup collects an ordered set of Forms and/or FormSets,
    and provides convenience methods for validating the group as a
    whole.
    """

    # form_classes is a list of two-tuples, where each tuple consists of
    #
    # (Class, Name)
    #
    # Class is a subclass of BaseForm or BaseFormSet, and Name is a
    # valid Python identifier that can be used for property access

    form_classes = []

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, label_suffix=":", instance=None,
                 error_class=ErrorList, member_kwargs=None):

        self.member_kwargs = member_kwargs or {}
        self.is_bound = data is not None or files is not None
        self.data = data or {}
        self.files = files or {}
        self.prefix = prefix or self.get_default_prefix()
        self.initial = initial or {}
        self.auto_id = auto_id
        self.label_suffix = label_suffix
        self.error_class = error_class

        # An instance is required
        if instance is None:
            raise ValueError("You must supply an instance to operate on.")
        self.instance = instance

        # construct the forms and create a dict for easy name-access
        self.named_forms = []
        for kls, name in self.form_classes:

            extra_kwargs = self.member_kwargs.get(name) or {}

            if issubclass(kls, BaseForm):
                self.named_forms.append(
                    (name,
                      kls(
                          data=data,
                          files=files,
                          auto_id=self.auto_id,
                          prefix='%s-%s' % (self.prefix, name),
                          initial=self.initial,
                          label_suffix=self.label_suffix,
                          instance=self.instance,
                          error_class=self.error_class,
                          **extra_kwargs
                          )
                      ))

            elif issubclass(kls, BaseInlineFormSet):
                # BaseInlineFormSet does not take an auto_id or error_class
                self.named_forms.append(
                    (name,
                      kls(
                          data=data,
                          files=files,
                          prefix='%s-%s' % (self.prefix, name),
                          instance=self.instance,
                          **extra_kwargs
                          )
                      ))

            elif issubclass(kls, BaseFormSet):
                self.named_forms.append(
                    (name,
                      kls(
                          data=data,
                          files=files,
                          auto_id=self.auto_id,
                          prefix='%s-%s' % (self.prefix, name),
                          instance=self.instance,
                          error_class=self.error_class,
                          **extra_kwargs
                          )
                      ))

        self.forms = [form for name, form in self.named_forms]
        self.named_forms = dict(self.named_forms)

        self._errors = None
        self._group_errors = None

    def __getattr__(self, name):

        return self.named_forms[name]

    def __len__(self):

        return len(self.forms)

    def _apply(self, method_name, *args, **kwargs):
        """Apply a method to all member forms."""

        return [method(*args, **kwargs)
                for method in self._collect(method_name)]

    def _collect(self, property):
        """Return a list of the property values for each form instance."""

        return [getattr(form, property)
                for form in self.forms]

    @classmethod
    def get_default_prefix(cls):
        return "group"

    def group_errors(self):
        """
        Returns an ErrorList of errors that aren't associated with a
        particular form -- i.e., from formset.clean(). Returns an
        empty ErrorList if there are none.
        """
        if self._group_errors is not None:
            return self._group_errors
        return self.error_class()

    def _get_errors(self):
        """
        Returns a list of form.errors for every form in self.forms.
        """
        if self._errors is None:
            self.full_clean()
        return self._errors
    errors = property(_get_errors)

    def is_valid(self):
        """
        Returns True if form.errors is empty for every form in self.forms.
        """
        if not self.is_bound:
            return False

        # perform cleaning on each member, then Group level
        self.full_clean()

        return (not(self.group_errors()) and
                all(self._apply('is_valid')))

    def full_clean(self):
        """
        Cleans all of self.data and populates self._errors.
        """
        self._errors = []
        if not self.is_bound:  # Stop further processing.
            return
        for form in self.forms:
            self._errors.append(form.errors)

        # Give self.clean() a chance to do full-group validation.
        try:
            self.clean()
        except ValidationError, e:
            self._group_errors = self.error_class(e.messages)

    def clean(self):
        """
        Hook for doing formgroup-wide cleaning/validation after
        .clean() has been called on every member.

        Any ValidationError raised by this method will be accessible
        via formgroup.group_errors().()
        """
        pass

    def save(self):
        """Save the changes to the instance and any related
        objects."""

        # first call save for the Form instances
        for form in self.forms:
            if isinstance(form, BaseForm):
                form.save(commit=False)

        # then commit the instance
        self.instance.save()
        for form in self.forms:
            if isinstance(form, BaseForm):
                if hasattr(form, 'save_m2m'):
                    form.save_m2m()
                if hasattr(form, 'save_related'):
                    form.save_related()

        # then call save for any formsets
        for form in self.forms:
            if isinstance(form, BaseFormSet):
                form.save(commit=True)

        # return the instance
        return self.instance

    @property
    def media(self):
        """Return the media definitions for all Forms and FormSets."""

        return self._collect('media')

    def add_prefix(self, field_name):
        """
        Returns the field name with a prefix appended, if this Form has a
        prefix set.

        Subclasses may wish to override.
        """

        if self.prefix:
            return '%s-%s' % (self.prefix, field_name)

        return field_name

    def html_id(self, field_name, form=None):

        if form is None:
            form = self

        return form.auto_id % form.add_prefix(field_name)


class StateValidatorFormGroup(StateValidatorFormMixin, FormGroup):
    """

    Subclasses are expected to define the state_validators property,
    which is a mapping of states to StateValidator objects."""

    def get_errors(self, *states):

        return [form.get_errors(*states)
                   for form in self.forms
                   if isinstance(form, StateValidatorFormMixin)] + \
               [self.state_validators[state].errors(self)
                   for state in states]

    def is_valid(self, *states):
        """Returns True if no errors are thrown for the specified state."""

        # if no state is specified, fallback to the base FormGroup's is_valid
        if not states:
            return super(StateValidatorFormGroup, self).is_valid()

        # see if the states pass for all forms that define state_validators
        return all(form.is_valid(*states)
                   for form in self.forms
                   if isinstance(form, StateValidatorFormMixin)) and \
               all(self.state_validators[state].is_valid(self)
                   for state in states)


def formgroup_factory(form_classes,
                      state_validators=None,
                      formgroup=None,
                      ):
    """Return a FormGroup Class for the given form[set] classes.

    If the optional state_validators dict is provided, this
    constructed class will subclass StateValidatorFormGroup."""

    # determine the base class to use
    if formgroup is None:
        if state_validators is None:
            formgroup = FormGroup
        else:
            formgroup = StateValidatorFormGroup

    attrs = {
        'form_classes': form_classes,
        'state_validators': state_validators,
        }
    return type('FormGroup', (formgroup,), attrs)
