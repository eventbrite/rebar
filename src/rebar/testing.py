"""Tools for testing Forms, FormSets, and FormGroups."""

from django.core.exceptions import ObjectDoesNotExist
from django.forms.forms import BaseForm
from django.forms.formsets import BaseFormSet
from django.forms.models import InlineForeignKeyField


def flatten_to_dict(item):
    """Recursively flatten a Form-like object to a data dict.

    Given a Form-like object such as a Form, ModelForm, FormSet, or
    FormGroup, flatten the members into a single dict, similar to what
    is provided by request.POST.

    If ``item`` is a FormSet, all member Forms will be included in the
    resulting data dictionary"""

    data = {}

    forms = []
    if isinstance(item, BaseForm):
        forms.append(item)
    if hasattr(item, 'forms'):
        forms += item.forms
    if hasattr(item, 'management_form'):
        forms += [item.management_form]

    for form in forms:

        # recurse into FormSets
        if isinstance(form, BaseFormSet):
            data.update(flatten_to_dict(form))
            continue

        for field in form.fields:

            try:
                # determine the initial value of this field
                if isinstance(form.fields[field],
                              (InlineForeignKeyField,)):
                    if getattr(form.instance, field):
                        value = getattr(form.instance, field).pk
                    else:
                        # the instance doesn't have a pk yet
                        value = None
                else:
                    value = form[field].value()
                    #getattr(form.instance, field,
                    #                form.fields[field].initial)
            except ObjectDoesNotExist:
                value = None

            if value is None:
                value = ''

            data[form.add_prefix(field)] = value

            # see if we also need to add the initial value
            if form.fields[field].show_hidden_initial:
                data[form.add_initial_prefix(field)] = value

    return data


def empty_form_data(formset, index=None):
    """Return a form data dictionary for a "new" form in a formset.

    Given a formset and an index, return a copy of the empty form
    data. If index is not provided, the index of the *first* empty
    form will be used as the new index.

    """

    index = str(index or len(formset))
    result = {}

    for field in formset.empty_form.fields:

        result[
            formset.empty_form
            .add_prefix(field)
            .replace('__prefix__', index)
        ] = formset.empty_form[field].value()

        # add initial data, if needed
        if formset.empty_form.fields[field].show_hidden_initial:
            result[
                formset.empty_form
                .add_initial_prefix(field)
                .replace('__prefix__', index)
            ] = formset.empty_form[field].value()

    return result
