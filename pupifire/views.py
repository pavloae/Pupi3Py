import os

import pyrebase
from django.http import HttpResponse

import firebase_admin
from firebase_admin import credentials

# Create your views here.
from Pupi3Py import settings

service_account_key = os.path.join(
    os.path.dirname(settings.BASE_DIR), 'aula31-e5dd1-firebase-adminsdk-eyng4-42181e09b6.json'
)

config = {
    'apiKey': "AIzaSyDmk-4phXqH4BjGgEkGc2rRiZf2ofguWi8",
    'authDomain': "aula31-e5dd1.firebaseapp.com",
    'databaseURL': "https://aula31-e5dd1.firebaseio.com",
    'projectId': "aula31-e5dd1",
    'storageBucket': "aula31-e5dd1.appspot.com",
    'messagingSenderId': "1069993443421",
    'appId': "1:1069993443421:web:873c974f3016b773",
    "serviceAccount": service_account_key
}

firebase = pyrebase.initialize_app(config)

cred = credentials.Certificate(service_account_key)
firebase_admin.initialize_app(cred)


def index(request):
    return HttpResponse('Index')


def login(request):
    return HttpResponse('Login')


def users(request):
    db = firebase.database()
    firebase_users = db.child("users").get()
    result = firebase_users.val()
    return HttpResponse(str(result))
