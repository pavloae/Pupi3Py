from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.


class User(AbstractUser):

    uid = models.CharField(primary_key=True, max_length=64)

    photo_url = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=32, blank=True, null=True)
    comment = models.CharField(max_length=512, blank=True, null=True)
    anonymous = models.BooleanField(default=True)

    id_token = models.CharField(max_length=2048, blank=True, null=True)
    refresh_token = models.CharField(max_length=2048, blank=True, null=True)
    custom_token = models.CharField(max_length=2048, blank=True, null=True)

    def __str__(self):
        return "{lastname}, {names}".format(lastname=self.last_name, names=self.names)
