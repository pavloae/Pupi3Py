import json
import os
from copy import deepcopy

import pyrebase
from pyrebase import pyrebase
from requests import HTTPError

from Pupi3Py import settings
from pupifire.models import User


config_file = os.path.join(
    os.path.dirname(settings.BASE_DIR), 'Pupi3Py.conf/pupitres-firebase-pyrebase.json'
)

with open(config_file) as json_file:
    config = json.load(json_file)

firebase = pyrebase.initialize_app(config)


def with_token_verify(request_method):

    def update_user(user_py: User, user_fb):
        user_py.id_token = user_fb.get('idToken')
        user_py.refresh_token = user_fb.get('refreshToken')
        user_py.save()

    def make_request(database, *args, token=None, last=False, **kwargs):
        try:
            # Si la consulta se realiza con exito devolvemos el valor retornado por la función.
            return request_method(database, *args, token=token, **kwargs)
        except HTTPError as e:
            print(e.__str__())
            # Si se produjo una excepción que no tiene que ver con el token, la propagamos.
            response = e.args[0].response
            if response.status_code != 401:
                raise e
            if last:
                raise FirebaseDatabaseException(160, 'Último intento de autenticación fracasado')
            raise FirebaseDatabaseException(200, 'El token no es válido')

    def wrap_request_method(database, *args, **kwargs):

        if not issubclass(type(database), pyrebase.Database):
            raise FirebaseDatabaseException(
                100,
                'Error en la asignación del decorador en un método de una clase que no hereda de "pyrebase.Database"'
            )

        user_py = database.user
        if not isinstance(user_py, User):
            raise FirebaseDatabaseException(
                110,
                'La instancia no posee un atributo "user" del tipo "pupifire.models.User"'
            )

        id_token = user_py.id_token
        try:
            return make_request(deepcopy(database), *args, token=id_token, last=False, **kwargs)
        except FirebaseDatabaseException as fbe:
            if fbe.code != 200:
                raise fbe

        # Si no tenemos un refreshToken ni un customToken le pedimos al usuario que vuelva a autenticarse.
        if not user_py.refresh_token and not user_py.custom_token:
            raise FirebaseDatabaseException(120, 'No existe refreshToken ni customToken para poder actualizar')

        # Si tenemos un refreshToken tratamos de actualizar el token
        user_fb = None
        if user_py.refresh_token:
            try:
                user_fb = refresh(user_py.refresh_token)
                id_token = user_fb.get('idToken')
            except HTTPError:
                pass

        # Si conseguimos actualizar el token guardamos los datos e intentamos nuevamente la consulta
        if user_fb:
            update_user(user_py, user_fb)
            try:
                return make_request(deepcopy(database), *args, token=id_token, last=False, **kwargs)
            except FirebaseDatabaseException as fbe:
                if fbe.code != 200:
                    raise fbe

        # Si tenemos un customToken intentamos actualizar el token
        user_fb = None
        if user_py.custom_token:
            try:
                user_fb = sign_in_with_custom_token(user_py.custom_token)
                id_token = user_fb.get('idToken')
            except HTTPError as e:
                raise FirebaseDatabaseException(130, 'No se pudo loguear con el customToken')

        if user_fb:
            update_user(user_py, user_fb)
            try:
                return make_request(deepcopy(database), *args, token=id_token, last=True, **kwargs)
            except FirebaseDatabaseException as fbe:
                if fbe.code != 200:
                    raise fbe

        raise FirebaseDatabaseException(140, 'Se agotaron los intentos de autenticación')

    return wrap_request_method


class UserDataBase(pyrebase.Database):

    def __init__(self, credentials, api_key, database_url, requests, user):
        super().__init__(credentials, api_key, database_url, requests)
        self.user = user

    @with_token_verify
    def get(self, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().get(token, json_kwargs)

    @with_token_verify
    def push(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().push(data, token, json_kwargs)

    @with_token_verify
    def set(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().set(data, token, json_kwargs)

    @with_token_verify
    def update(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().update(data, token, json_kwargs)

    @with_token_verify
    def remove(self, token=None):
        return super().remove(token)


def get_database(user: User):
    return UserDataBase(firebase.credentials, firebase.api_key, firebase.database_url, firebase.requests, user)


def sign_in_with_custom_token(custom_token):
    return firebase.auth().sign_in_with_custom_token(custom_token)


def refresh(refresh_token):
    return firebase.auth().refresh(refresh_token)


class FirebaseDatabaseException(Exception):

    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
