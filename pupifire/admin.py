from django.contrib import admin

# Register your models here.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm

from pupifire.models import User


class PupitresChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User


class PupitresUserAdmin(UserAdmin):
    form = PupitresChangeForm


admin.site.register(User, PupitresUserAdmin)

