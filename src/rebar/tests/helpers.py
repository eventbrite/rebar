from django import forms


class FakeModel(object):

    def __init__(self, **kwargs):

        self.id = None
        self.__dict__.update(kwargs)

    def save(self):
        self.id = 42


class CallSentinel(object):

    def __init__(self, *args, **kwargs):
        super(CallSentinel, self).__init__(*args, **kwargs)

        self.called = {}

    def save(self, *args, **kwargs):
        self.called['save'] = True

    def save_m2m(self, *args, **kwargs):

        if self.instance.id is None:
            raise AssertionError(
                "Expected instance.id to be previously set."
            )

        self.called['save_m2m'] = True

    def save_related(self, *args, **kwargs):

        if self.instance.id is None:
            raise AssertionError(
                "Expected instance.id to be previously set."
            )

        self.called['save_related'] = True

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

    def apply_test(self, *args):

        self.called['apply_test'] = args

        return True


class NameForm(TestForm):

    class Media:
        css = {
            'all': ('name.css',),
        }
        js = (
            'name.js',
        )

    first_name = forms.CharField(
        required=True,
        show_hidden_initial=True,
        initial='Larry',
    )
    last_name = forms.CharField()


class EmailForm(TestForm):

    class Media:
        css = {
            'all': ('email.css',),
        }
        js = (
            'email.js',
        )

    email = forms.EmailField(required=True)
