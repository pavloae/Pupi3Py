from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from django.utils.translation import gettext_lazy as _

# Create your models here.


class User(AbstractUser):

    username_validator = UnicodeUsernameValidator()

    uid = models.CharField(primary_key=True, max_length=128)

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

    display_name = models.CharField(max_length=128, null=True, blank=True)
    photo_url = models.URLField(max_length=2000, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_number = models.CharField(max_length=32, blank=True, null=True)
    is_fb_anonymous = models.BooleanField(default=True)
    provider_id = models.CharField(max_length=16, blank=True, null=True)

    id_token = models.CharField(max_length=2048, blank=True, null=True)
    refresh_token = models.CharField(max_length=2048, blank=True, null=True)
    custom_token = models.CharField(max_length=2048, blank=True, null=True)

    @property
    def token(self):
        return self.id_token or ''

    def __str__(self):
        return "{lastname}, {names}".format(lastname=self.last_name, names=self.first_name)
