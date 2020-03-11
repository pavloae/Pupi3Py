
# Create your tests here.
import json
import os
from collections import OrderedDict
from copy import deepcopy

from django.test import SimpleTestCase, TestCase
from firebase_admin import auth
from pyrebase.pyrebase import PyreResponse
from requests import HTTPError

from Pupi3Py import settings
from pupifire.firebase.admin import default_app
from pupifire.firebase.user import firebase, get_database
from pupifire.models import User

uid = 'oyWO9VIYczOtUaWex34L37cC5583'


class AuthTest(SimpleTestCase):

    def test_create_custom_token(self):
        app = default_app

        custom_token = auth.create_custom_token(uid, app=app)
        self.assertIsInstance(custom_token, bytes)
        self.assertEqual(len(custom_token), 867)
        custom_token = custom_token.decode('utf-8')
        self.assertIsInstance(custom_token, str)
        self.assertEqual(len(custom_token), 867)

    def test_get_prop(self):
        config_file = os.path.join(
            os.path.dirname(settings.BASE_DIR), 'Pupi3Py.conf/pupitres-firebase-pyrebase.json'
        )

        with open(config_file) as json_file:
            config = json.load(json_file)

        self.assertIsNotNone(config)


class DataBase(SimpleTestCase):

    def test_get(self):

        test_result = firebase.database().child('test').get()
        self.assertIsInstance(test_result, PyreResponse)

        user_result = None
        try:
            user_result = firebase.database().child('users').child(uid).get()
        except HTTPError as e:
            response = e.args[0]

        self.assertIsNone(user_result)

    def test_get_user(self):

        # Creamos un token personalizado para el usuario usando la API de Firebase
        custom_token = auth.create_custom_token(uid)
        self.assertIsInstance(custom_token, bytes)

        # Logueamos al usuario y obtenemos un token con la librería Pyrebase
        sign_in = firebase.auth().sign_in_with_custom_token(custom_token.decode('utf-8'))
        self.assertIsInstance(sign_in, dict)

        id_token = sign_in.get('idToken')
        self.assertIsInstance(id_token, str)

        user = User()
        user.id_token = id_token

        # Hacemos una consulta usando el token de Pyrebase
        database = get_database(user).child('users').child(uid)
        user_result = database.get()
        self.assertIsInstance(user_result, PyreResponse)

        user_key = user_result.key()
        user_profile = user_result.val()

        self.assertIsInstance(user_key, str)
        self.assertIsInstance(user_profile, OrderedDict)

        comment = user_profile.get('comment')
        self.assertEqual(comment, 'Motorola Emulator G2')


class DataBaseUser(TestCase):

    def test_get_profile(self):

        user, created = User.objects.get_or_create(uid=uid)

        self.assertIsNotNone(user)

        database = get_database(user).child('users').child(user.uid)
        datasnapshot = database.get()

        self.assertIsNotNone(datasnapshot)
