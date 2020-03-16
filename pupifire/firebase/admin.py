import os

import firebase_admin
from firebase_admin import credentials, auth
from firebase_admin.auth import TokenSignError

from Pupi3Py import settings

service_account_key = os.path.join(
    os.path.dirname(settings.BASE_DIR), 'Pupi3Py.conf/pupitres-firebase-adminsdk-n3yp9-55604aa9ed.json'
)
cred = credentials.Certificate(service_account_key)
default_app = firebase_admin.initialize_app(cred)


def request_custom_token(uid):

    try:
        # Pedimos un token personalizado para el usuario
        custom_token = auth.create_custom_token(uid)
        if not isinstance(custom_token, bytes):
            raise FirebaseAuthException(140, 'El token obtenido no es válido')
        return custom_token.decode('utf-8')
    except ValueError:
        raise FirebaseAuthException(120, 'Los parámetros de entrada no son válidos')
    except TokenSignError:
        raise FirebaseAuthException(130, 'Los parámetros de entrada no son válidos')
    except UnicodeDecodeError:
        raise FirebaseAuthException(140, 'No se pudo transformar el token a una cadena')


def pull(user):
    user_record = auth.get_user(user.uid, default_app)
    """:type : auth.UserRecord"""

    user.email = user_record.email or ''
    user.phone_number = user_record.phone_number
    user.email_verified = user_record.email_verified
    user.display_name = user_record.display_name
    user.photo_url = user_record.photo_url
    user.save()


def push(user):
    auth.update_user(
        user.uid,
        email=user.email or None,
        phone_number=user.phone_number,
        email_verified=user.email_verified,
        display_name=user.display_name,
        photo_url=user.photo_url)


class FirebaseAuthException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
