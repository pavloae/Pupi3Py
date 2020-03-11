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

    def update_user(user, retrieved_tokens):
        user.id_token = retrieved_tokens.get('idToken')
        user.refresh_token = retrieved_tokens.get('refreshToken')
        user.save()

    def get_args(*args, **kwargs):

        id_token = kwargs.pop('id_token', None)

        firebase_ref = args[0]

        if issubclass(type(firebase_ref), pyrebase.Database):
            data = kwargs.get('data', None)
            if request_method.__name__ in ['push', 'set', 'update'] and len(args) > 1:
                data = args[1]

        token = kwargs.get('token', None)
        if id_token:
            token = id_token
        elif request_method.__name__ in ['get', 'remove'] and len(args) > 1:
            token = args[1]
        elif request_method.__name__ in ['push', 'set', 'update'] and len(args) > 2:
            token = args[1]

        json_kwargs = kwargs.get('json_kwargs', {})
        if request_method.__name__ in ['get'] and len(args) > 2:
            json_kwargs = args[2]
        elif request_method.__name__ in ['push', 'set', 'update'] and len(args) > 3:
            json_kwargs = args[3]

        if request_method.__name__ in ['push', 'set', 'update']:
            return data, token, json_kwargs
        elif request_method.__name__ == 'get':
            return token, json_kwargs
        else:
            return token

    def wrap_request_method(*args, **kwargs):

        if request_method.__name__ not in ['get', 'push', 'set', 'update', 'remove', 'put', 'download', 'get_url']:
            raise FirebaseException(110, 'No se aplicó el decorador sobre un método permitido')

        firebase_ref = args[0]
        if not issubclass(type(firebase_ref), pyrebase.Database) or not issubclass(type(firebase_ref), pyrebase.Storage):
            raise FirebaseException(
                100, 'El decorador está aplicado a un método que no es de la clase "pyrebase.Database"'
            )

        # Intentamos hacer la consulta con una copia de la referencia.
        # Si se especificó un token y no es válido tratamos de conseguir un nuevo token.
        # Si surge otro problema propagamos la excepción.
        try:
            return request_method(deepcopy(firebase_ref), *get_args(*args, **kwargs))
        except HTTPError as e:
            if e.args[0].response.status_code != 401:
                raise e

        # Si no hay un usuario especificado lanzamos una excepción
        if not isinstance(firebase_ref.user, User):
            raise FirebaseException(
                120,
                'La instancia no posee un atributo "user" del tipo "pupifire.models.User"'
            )

        # Si no tenemos un refreshToken ni un customToken le pedimos al usuario que vuelva a autenticarse.
        if not firebase_ref.user.refresh_token and not firebase_ref.user.custom_token:
            raise FirebaseTokenException(100, "No hay tokens para revalidar.")

        # Si tenemos un refreshToken tratamos de actualizar el token para volver a realizar la consulta
        if firebase_ref.user.refresh_token:
            try:
                update_user(firebase_ref.user, refresh(firebase_ref.user.refresh_token))
                kwargs.update({'id_token': firebase_ref.user.id_token})
                response = request_method(deepcopy(firebase_ref), *get_args(*args, **kwargs))
                firebase_ref.user.save()
                return response
            except HTTPError as e:
                if e.args[0].response.status_code != 401:
                    raise e

        # Si tenemos un customToken intentamos actualizar el token para hacer el último intento
        if firebase_ref.user.custom_token:
            try:
                update_user(firebase_ref.user, sign_in_with_custom_token(firebase_ref.user.custom_token))
                kwargs.update({'id_token': firebase_ref.user.id_token})
                response = request_method(deepcopy(firebase_ref), *get_args(*args, **kwargs))
                firebase_ref.user.save()
                return response
            except HTTPError as e:
                if e.args[0].response.status_code != 401:
                    raise e

        raise FirebaseTokenException(140, 'Se agotaron los intentos de autenticación')

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


class UserStorage(pyrebase.Storage):

    def __init__(self, credentials, storage_bucket, requests, user):
        super().__init__(credentials, storage_bucket, requests)
        self.user = user

    def put(self, file, token=None):
        return super().put(file, token)

    def download(self, filename, token=None):
        super().download(filename, token)

    def get_url(self, token):
        return super().get_url(token)


def get_database(user: User):
    return UserDataBase(firebase.credentials, firebase.api_key, firebase.database_url, firebase.requests, user)


def get_storage(user: User):
    return UserStorage(firebase.credentials, firebase.storage_bucket, firebase.requests, user)


def sign_in_with_custom_token(custom_token):
    return firebase.auth().sign_in_with_custom_token(custom_token)


def refresh(refresh_token):
    return firebase.auth().refresh(refresh_token)


class FirebaseException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message


class FirebaseTokenException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
