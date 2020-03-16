import json
import os
from copy import deepcopy
from inspect import signature

from pyrebase.pyrebase import Auth, Database, Storage, initialize_app
from requests import HTTPError

from Pupi3Py import settings
from pupifire.models import User

config_file = os.path.join(
    os.path.dirname(settings.BASE_DIR), 'Pupi3Py.conf/pupitres-firebase-pyrebase.json'
)

with open(config_file) as json_file:
    config = json.load(json_file)

firebase = initialize_app(config)


def with_token_update(request_method):

    token_args_position = list(signature(request_method).parameters.keys()).index('token')

    def wrap_request_method(*args, **kwargs):

        token = kwargs.pop('token', None)
        if not token and len(args) > token_args_position:
            token = args[token_args_position]

        reference = args[0]
        ref_type = type(reference)
        if not (issubclass(ref_type, Database) or issubclass(ref_type, Storage) or issubclass(ref_type, Auth)):
            raise FirebaseException(
                100,
                'El decorador está aplicado a un método que no es de la clase "pyrebase.Database" ni ""pyrebase.Storage'
            )

        # Intentamos hacer la consulta con una copia de la referencia (Luego de hacer la consulta la clase borra el url)
        # Si se especificó un token y no es válido tratamos de conseguir un nuevo token.
        # Si surge otro problema propagamos la excepción.
        try:
            args_list = list(args)
            args_list[0] = deepcopy(reference)
            return request_method(*args_list, **kwargs)
        except HTTPError as e:
            if e.args[0].response.status_code != 401 and token is None:
                raise e

        # Tratamos de actualizar el token para volver a realizar la consulta
        get_auth(reference.user).refresh_token()
        try:
            args_list = list(args)
            args_list[token_args_position] = reference.user.id_token
            return request_method(*args_list, **kwargs)
        except HTTPError as e:
            if e.args[0].response.status_code != 401:
                raise e

        raise FirebaseTokenException(140, 'Se agotaron los intentos de autenticación')

    return wrap_request_method


class UserAuth(Auth):

    def __init__(self, api_key, requests, credentials, user):
        super().__init__(api_key, requests, credentials)
        self.user = user

    def refresh_token(self):

        if not isinstance(self.user, User):
            raise FirebaseException(120, 'La instancia no posee un atributo "user" del tipo "pupifire.models.User"')

        if not self.user.refresh_token:
            return self.__sign_in_with_custom_token()

        try:
            dict_token = super().refresh(self.user.refresh_token)
            self.__update_user(dict_token)
            return dict_token
        except HTTPError as e:
            if e.args[0].response.status_code != 401:
                raise e

        return self.__sign_in_with_custom_token()

    def __sign_in_with_custom_token(self):

        if not isinstance(self.user, User):
            raise FirebaseException(120, 'La instancia no posee un atributo "user" del tipo "pupifire.models.User"')

        if not self.user.custom_token:
            raise FirebaseTokenException(100, "No hay tokens para revalidar.")

        try:
            dict_token = self.sign_in_with_custom_token(self.user.custom_token)
            self.__update_user(dict_token)
            return dict_token
        except HTTPError as e:
            if e.args[0].response.status_code != 401:
                raise e

        raise FirebaseTokenException(140, 'Se agotaron los intentos de autenticación')

    def __update_user(self, dict_token):
        self.user.id_token = dict_token.get('idToken')
        self.user.refresh_token = dict_token.get('refreshToken')
        self.user.save()

    @with_token_update
    def get_account_info(self, token):
        if not token:
            self.refresh_token()
            token = self.user.id_token
        return super().get_account_info(token)


class UserDataBase(Database):

    def __init__(self, credentials, api_key, database_url, requests, user):
        super().__init__(credentials, api_key, database_url, requests)
        self.user = user

    @with_token_update
    def get(self, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().get(token, json_kwargs)

    @with_token_update
    def push(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().push(data, token, json_kwargs)

    @with_token_update
    def set(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().set(data, token, json_kwargs)

    @with_token_update
    def update(self, data, token=None, json_kwargs=None):
        if json_kwargs is None:
            json_kwargs = {}
        return super().update(data, token, json_kwargs)

    @with_token_update
    def remove(self, token=None):
        return super().remove(token)


class UserStorage(Storage):

    def __init__(self, credentials, storage_bucket, requests, user):
        super().__init__(credentials, storage_bucket, requests)
        self.user = user

    @with_token_update
    def put(self, file, token=None):
        return super().put(file, token)

    @with_token_update
    def download(self, filename, token=None):
        super().download(filename, token)

    @with_token_update
    def get_url(self, token):
        return super().get_url(token)


def get_auth(user: User):
    return UserAuth(firebase.api_key, firebase.requests, firebase.credentials, user)


def get_database(user: User):
    return UserDataBase(firebase.credentials, firebase.api_key, firebase.database_url, firebase.requests, user)


def get_storage(user: User):
    return UserStorage(firebase.credentials, firebase.storage_bucket, firebase.requests, user)


class FirebaseException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message


class FirebaseTokenException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
