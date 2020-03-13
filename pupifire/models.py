from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from django.utils.translation import gettext_lazy as _

# Create your models here.


class User(AbstractUser):

    username_validator = UnicodeUsernameValidator()

    uid = models.CharField(primary_key=True, max_length=64)

    # Sobreescribimos el campo para permitir "username" repetido ya que identificamos a los usuarios por su "uid"
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=False,  # unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )

    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = []

    # photo_url = models.URLField(blank=True, null=True)
    # phone = models.CharField(max_length=32, blank=True, null=True)
    # comment = models.CharField(max_length=512, blank=True, null=True)
    # anonymous = models.BooleanField(default=True)

    id_token = models.CharField(max_length=2048, blank=True, null=True)
    refresh_token = models.CharField(max_length=2048, blank=True, null=True)
    custom_token = models.CharField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return "{lastname}, {names}".format(lastname=self.last_name, names=self.names)
