from django import forms


class UserProfileForm(forms.Form):

    photo_url = forms.URLField(required=False)
    photo_profile = forms.ImageField(label='Archivo de contactos', allow_empty_file=True, required=False)

    last_name = forms.CharField(label='Apellido', required=False, max_length=19)
    first_name = forms.CharField(label='Nombres', required=False, max_length=39)
    comment = forms.CharField(label='Comentario', required=False, max_length=79)

    phone = forms.CharField(label="Teléfono", disabled=True, required=False)
    share = forms.BooleanField(label="Compartir")
