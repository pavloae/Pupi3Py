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
        fields = ['photo_url', 'last_name', 'first_name', 'email', 'email_verified', 'phone_number']
        widgets = {
            'photo_url': forms.HiddenInput(),
        }


class CourseProfile(forms.Form):

    GRADE_CHOICES = ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7), (8, 8), (9, 9))
    CLASSROOM_CHOICES = ((0, 'A'), (1, 'B'), (2, 'C'), (3, 'D'), (4, 'E'), (5, 'F'))
    SHIFT_CHOICES = ((0, 'MAÑANA'), (1, 'TARDE'), (2, 'NOCHE'))

    institution_id = forms.CharField(max_length=128, widget=forms.HiddenInput(), required=False)
    institution_name = forms.CharField(max_length=128, label='Institución')

    subject_id = forms.CharField(max_length=128, widget=forms.HiddenInput(), required=False)
    subject_name = forms.CharField(max_length=128, label='Materia')
    grade = forms.ChoiceField(choices=GRADE_CHOICES, label='Sala/Grado/Año', required=False)

    classroom = forms.ChoiceField(choices=CLASSROOM_CHOICES, label='División', required=False)
    shift = forms.ChoiceField(choices=SHIFT_CHOICES, label='Turno', required=False)

    owner = forms.CharField(max_length=128, widget=forms.HiddenInput(), required=False)


class InstitutionForm(forms.Form):

    name = forms.CharField(max_length=79)
    address = forms.CharField(max_length=79, required=False)
    city = forms.CharField(max_length=79, required=False)
    state = forms.CharField(max_length=79, required=False)
    cp = forms.IntegerField(required=False)
    phone = forms.CharField(max_length=19, required=False)
    level = forms.CharField(max_length=79, required=False)
    email = forms.EmailField(required=False)
    public = forms.BooleanField(required=False)
