import json
import os
from json import JSONDecodeError

import pyrebase
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse

from Pupi3Py import settings
from pupifire.models import User
from pupifire.views import firebase

service_account_key = os.path.join(
    os.path.dirname(settings.BASE_DIR), 'aula31-e5dd1-firebase-adminsdk-eyng4-42181e09b6.json'
)

config = {
    'apiKey': "AIzaSyDmk-4phXqH4BjGgEkGc2rRiZf2ofguWi8",
    'authDomain': "aula31-e5dd1.firebaseapp.com",
    'databaseURL': "https://aula31-e5dd1.firebaseio.com",
    'storageBucket': "aula31-e5dd1.appspot.com",
    'serviceAccount': service_account_key
}

firebase = pyrebase.initialize_app(config)


def verify_token(request):

    if request.method == 'POST':
        try:
            # Si el cliente envía los datos de un usuario lo buscamos en la base de datos o lo creamos
            user = json.loads(request.POST.get('user'))
            uid = user.get('uid', None)
            if not uid:
                return redirect(reverse('login'))
            user_py, created = User.objects.get_or_create(pk=uid)

            # Pedimos un token personalizado para el usuario
            custom_token = firebase.auth().create_custom_token(user['uid'])
            if not custom_token:
                return redirect(reverse('login'))
            user_fb = firebase.auth().sign_in_with_custom_token(custom_token)

            # Cargamos los datos del usuario y los guardamos
            user_py.custom_token = custom_token
            user_py.id_token = user_fb.get('idToken', None)
            user_py.refresh_token = user_fb.get('refreshToken', None)
            user_py.photo_url = user.get('photoURL', None)
            user_py.email = user.get('email', None)
            user_py.phone = user.get('phoneNumber', None)
            user_py.anonymous = user.get('isAnonymous', True)
            user_py.save()

            # Logueamos al usuario de Django y lo reenviamos al index.
            login(request, user_py)

        except (TypeError or JSONDecodeError) as e:
            redirect(reverse('login'))

    return redirect(reverse('index'))
