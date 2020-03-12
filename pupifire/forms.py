from django import forms


class UserProfileForm(forms.Form):

    photo_profile = forms.ImageField(label='Archivo de contactos', allow_empty_file=True, required=False)

    last_name = forms.CharField(label='Apellido', required=False)
    first_name = forms.CharField(label='Nombres', required=False)
    comment = forms.CharField(label='Comentario', required=False)

    phone = forms.CharField(label="Teléfono", disabled=True, required=False)
    share = forms.CheckboxInput()
