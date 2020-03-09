import pyrebase
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render, redirect
from django.urls import reverse

config = {
    'apiKey': "AIzaSyDmk-4phXqH4BjGgEkGc2rRiZf2ofguWi8",
    'authDomain': "aula31-e5dd1.firebaseapp.com",
    'databaseURL': "https://aula31-e5dd1.firebaseio.com",
    'storageBucket': "aula31-e5dd1.appspot.com",
}

firebase = pyrebase.initialize_app(config)


def index(request):

    user_py = request.user
    """:type : pupifire.models.User"""

    custom_token = user_py.custom_token

    user_fb = firebase.auth().sign_in_with_custom_token(custom_token)

    return redirect(reverse('users'))


def user_login(request):
    return render(request, 'login.html')


def user_logout(request):
    auth.logout(request)
    return redirect(reverse('login'))


def tos(request):
    return HttpResponse("Términos del servicio...")


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


@login_required
def users(request):
    user = request.user
    """:type : pupifire.models.User"""

    db = firebase.database()
    datasnapshot = db.child('users').child(user.uid).get(user.id_token)

    value = datasnapshot.val()

    user.last_name = value.get('lastname')
    user.first_name = value.get('names')
    user.photo_url = value.get('url_image')
    user.comment = value.get('comment')
    user.save()



    return render(request, 'profile.html', {'user': user})
