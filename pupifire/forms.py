from django import forms

from pupifire.models import User


class UpdateProfile(forms.ModelForm):
    last_name = forms.CharField(required=False)
    first_name = forms.CharField(required=False)
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)

    class Meta:
        model = User
        fields = ('last_name', 'first_name', 'email', 'phone')
