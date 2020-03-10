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


class FirebaseAuthException(Exception):
    def __init__(self, code, message) -> None:
        self.code = code
        self.message = message
