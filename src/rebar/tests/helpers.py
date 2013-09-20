from django import forms


class FakeModel(object):

    def save(self, commit=False):
        pass


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

    def __init__(self, *args, **kwargs):

        self.kwargs = kwargs.copy()
        self.clean_count = 0

        if 'test_kwarg' in kwargs:
            kwargs.pop('test_kwarg')
        if 'instance' in kwargs:
            self.instance = kwargs.pop('instance')

        super(TestForm, self).__init__(*args, **kwargs)

    def clean(self):

        self.clean_count += 1
        return self.cleaned_data

    def save(self, commit=True):
        super(TestForm, self).save()

        if commit:
            self.instance.save()


class NameForm(TestForm):

    first_name = forms.CharField(
        required=True,
        show_hidden_initial=True,
        initial='Larry',
    )
    last_name = forms.CharField()


class EmailForm(TestForm):

    email = forms.EmailField(required=True)
