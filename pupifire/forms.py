from django import forms
from django.forms import models

from pupifire.models import User


class UserProfileForm(models.ModelForm):

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.provider_id == 'phone':
            self.fields['phone_number'].disabled = True
        if self.instance and self.instance.provider_id == 'password':
            self.fields['email'].disabled = True

    photo_profile = forms.ImageField(allow_empty_file=True, required=False)

    last_name = forms.CharField(label='Apellido', required=False, max_length=19)
    first_name = forms.CharField(label='Nombres', required=False, max_length=39)
    comment = forms.CharField(label='Comentario', required=False, max_length=79)

    shared_email = forms.BooleanField(label="Compartir", required=False)
    shared_phone = forms.BooleanField(label="Compartir", required=False)

    class Meta:
        model = User
        fields = ['photo_url', 'email', 'email_verified', 'phone_number']
        widgets = {
            'photo_url': forms.HiddenInput(),
        }

