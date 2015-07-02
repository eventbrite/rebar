from django.core.exceptions import ValidationError
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.forms.models import BaseInlineFormSet
from rebar.dix import ErrorList

from rebar.validators import StateValidatorFormMixin


class Unspecified(object):
    """Unspecified Value."""
Unspecified = Unspecified()


class FormGroup(object):
    """Form-like wrapper for a heterogenous collection of Forms.

    A FormGroup collects an ordered set of Forms and/or FormSets,
    and provides convenience methods for validating the group as a
    whole.

    """

    def __init__(self,
                 data=None,
                 files=None,
                 auto_id='id_%s',
                 prefix=None,
                 initial=None,
                 label_suffix=':',
                 instance=Unspecified,
                 error_class=None,
                 member_kwargs=None):

        self.is_bound = data is not None or files is not None
        self.data = data or {}
        self.files = files or {}
        self.initial = initial or {}
        self.label_suffix = label_suffix
        self.instance = instance
        self.auto_id = auto_id
        self.error_class = error_class or ErrorList
        self._errors = None
        self._group_errors = None

        self.prefix = prefix or self.get_default_prefix()

        self.member_kwargs = member_kwargs or {}

        # instantiate the members
        self._forms = []
        self.named_forms = {}

        for member_class in self.form_classes:
            if isinstance(member_class, tuple):
                member_class, name = member_class
            else:
                name = member_class.__name__.lower()
                if name.endswith('form'):
                    name = name[:-4]

            kwargs = dict(
                prefix=self.add_prefix(name),
                data=data,
                files=files,
            )

            if issubclass(member_class, BaseForm):
                kwargs.update(dict(
                    auto_id=self.auto_id,
                    error_class=self.error_class,
                    label_suffix=self.label_suffix,
                    initial=self.initial.copy(),
                ))

            elif issubclass(member_class, BaseInlineFormSet):
                # inline formsets do not take additional kwargs
                pass

            elif issubclass(member_class, BaseFormSet):
                kwargs.update(dict(
                    auto_id=self.auto_id,
                    error_class=self.error_class,
                ))
            extra_kwargs = self.member_kwargs.get(name, {})
            if self.instance is not Unspecified:
                extra_kwargs['instance'] = self.instance
            kwargs.update(extra_kwargs)

            new_form = member_class(
                **kwargs
            )
            self.named_forms[name] = new_form
            self._forms.append(new_form)

    @property
    def forms(self):
        return self._forms

    def __len__(self):

        return len(self.forms)

    def __getitem__(self, index):

        return self.forms[index]

    def __getattr__(self, name):

        try:
            return self.named_forms[name]
        except KeyError:
            raise AttributeError

    def _apply(self, method_name, *args, **kwargs):
        """Call ``method_name`` with args and kwargs on each member.

        Returns a sequence of return values.

        """

        return [
            getattr(member, method_name)(*args, **kwargs)
            for member in self.forms
        ]

    def get_default_prefix(self):

        return 'group'

    def add_prefix(self, field_name):
        """Return the field name with a prefix prepended."""

        return '%s-%s' % (self.prefix, field_name)

    def html_id(self, field_name, form=None):
        """Return the html ID for the given field_name."""

        if form is None:
            form = self

        return form.auto_id % (form.add_prefix(field_name),)

    def _full_clean(self):

        self._errors = []
        if not self.is_bound:
            return

        self._errors = [
            f.errors
            for f in self.forms
        ]

        try:
            self.clean()
        except ValidationError as e:
            self._group_errors = self.error_class(e.messages)

    def clean(self):
        """
        Hook for doing formgroup-wide cleaning/validation.

        Subclasses can override this to perform validation after
        .clean() has been called on every member.

        Any ValidationError raised by this method will be accessible
        via formgroup.group_errors().()

        """

    def is_valid(self):

        if not self.is_bound:
            return False

        self._full_clean()

        forms_valid = [
            f.is_valid()
            for f in self.forms
        ]

        return all(forms_valid)

    @property
    def errors(self):

        if self._errors is None:
            self._full_clean()

        return self._errors

    def group_errors(self):
        """
        Return the group level validation errors.

        Returns an ErrorList of errors that aren't associated with a
        particular form. Returns an empty ErrorList if there are none.

        """

        if self._group_errors is not None:
            return self._group_errors

        return self.error_class()

    def save(self):
        """Save the changes to the instance and any related objects."""

        # first call save with commit=False for all Forms
        for form in self._forms:
            if isinstance(form, BaseForm):
                form.save(commit=False)

        # call save on the instance
        self.instance.save()

        # call any post-commit hooks that have been stashed on Forms
        for form in self.forms:
            if isinstance(form, BaseForm):
                if hasattr(form, 'save_m2m'):
                    form.save_m2m()
                if hasattr(form, 'save_related'):
                    form.save_related()

        # call save on any formsets
        for form in self._forms:
            if isinstance(form, BaseFormSet):
                form.save(commit=True)

        return self.instance

    @property
    def media(self):

        group_media = self.forms[0].media

        for form in self.forms[1:]:
            group_media += form.media

        return group_media


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
                      formgroup=None,
                      state_validators=None,
                      ):
    """Return a FormGroup class for the given form[set] form_classes.

    """

    base_class = formgroup or FormGroup
    if state_validators is not None:
        base_class = StateValidatorFormGroup

    if not issubclass(base_class, FormGroup):
        raise TypeError("Base formgroup class must subclass FormGroup.")

    return type(
        'FormGroup',
        (base_class,),
        dict(
            form_classes=form_classes,
            state_validators=state_validators,
        ),
    )
