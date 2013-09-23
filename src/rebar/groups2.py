from django.core.exceptions import ValidationError
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.forms.util import ErrorList

from rebar.validators import StateValidatorFormMixin


class Unspecified(object):
    """Unspecified Value."""
Unspecified = Unspecified()


class FormGroup(object):

    def __init__(self,
                 data=None,
                 files=None,
                 initial=None,
                 instance=Unspecified,
                 prefix=None,
                 auto_id='id_%s',
                 error_class=None,
                 member_kwargs=None):

        self.is_bound = data is not None or files is not None
        self.data = data or {}
        self.files = files or {}
        self.initial = initial or {}
        self.instance = instance
        self.auto_id = auto_id
        self.error_class = error_class or ErrorList
        self._errors = None
        self._group_errors = None

        self.prefix = prefix or self.get_default_prefix()

        self.member_kwargs = member_kwargs or {}

        # instantiate the members
        self._forms = []
        self._forms_by_name = {}

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
                initial=self.initial,
            )
            extra_kwargs = self.member_kwargs.get(name, {})
            if self.instance is not Unspecified:
                extra_kwargs['instance'] = self.instance
            kwargs.update(extra_kwargs)

            new_form = member_class(
                **kwargs
            )
            self._forms_by_name[name] = new_form
            self._forms.append(new_form)

    @property
    def forms(self):
        return self._forms

    def __len__(self):

        return len(self.forms)

    def __getitem__(self, index):

        return self.forms[index]

    def __getattr__(self, name):

        return self._forms_by_name[name]

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

        self._errors = map(
            lambda f: f.errors,
            self.forms,
        )

        try:
            self.clean()
        except ValidationError, e:
            self._group_errors = self.error_class(e.messages)

    def clean(self):
        pass

    def is_valid(self):

        if not self.is_bound:
            return False

        self._full_clean()

        return all(
            map(
                lambda f: f.is_valid(),
                self.forms,
            )
        )

    @property
    def errors(self):

        if self._errors is None:
            self._full_clean()

        return self._errors

    def group_errors(self):

        if self._group_errors is not None:
            return self._group_errors

        return self.error_class()

    def save(self):

        # first call save with commit=False for all Forms
        for form in self._forms:
            if isinstance(form, BaseForm):
                form.save(commit=False)

        # call save on the instance and commit
        self.instance.save(commit=True)

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

    @property
    def media(self):

        return reduce(
            lambda x, y: x+y,
            map(
                lambda f: f.media,
                self.forms,
            )
        )


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


def formgroup_factory(members,
                      formgroup=None,
                      state_validators=None,
                      ):
    """Return a FormGroup class for the given form[set] members.

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
            form_classes=members,
            state_validators=state_validators,
        ),
    )
