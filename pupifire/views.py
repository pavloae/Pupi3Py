import json
from json import JSONDecodeError

from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# Create your views here.
from django.shortcuts import render, redirect
from django.urls import reverse

from pupifire.firebase.admin import request_custom_token, FirebaseAuthException
from pupifire.firebase.user import get_database, firebase, sign_in_with_custom_token, FirebaseDatabaseException
from pupifire.models import User


@login_required
def index(request):

    user_py = request.user
    """:type : pupifire.models.User"""

    return redirect(reverse('profile'))


def user_login(request):
    return render(request, 'login.html')


def user_logout(request):
    auth.logout(request)
    return redirect(reverse('login'))


def verify(request):

    if request.method == 'POST':
        try:
            user = json.loads(request.POST.get('user'))
            uid = user.get('uid')

            # Obtenemos un token personalizado para el usuario
            custom_token = request_custom_token(uid)

            # Logueamos al usuario en firebase
            sign_in = sign_in_with_custom_token(custom_token)

            # Actualizamos la información del usuario
            user_py, created = User.objects.get_or_create(pk=user.get('uid'))
            user_py.custom_token = custom_token
            user_py.refresh_token = sign_in.get('refreshToken')
            user_py.id_token = sign_in.get('id_token')
            user_py.photo_url = user.get('photoURL', None)
            user_py.email = user.get('email', None)
            user_py.phone = user.get('phoneNumber', None)
            user_py.anonymous = user.get('isAnonymous', True)
            user_py.save()

            # Logueamos al usuario de Django y lo reenviamos al index.
            login(request, user_py)

        except (TypeError or JSONDecodeError) as e:
            redirect(reverse('logout'))
        except FirebaseAuthException as fbe:
            redirect(reverse('logout'))

    return redirect(reverse('index'))


def tos(request):
    return HttpResponse("Términos del servicio...")


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


def login_user_fb(request):
    user_py = request.user
    """:type : pupifire.models.User"""

    # Si tenemos un refreshToken intentamos obtener un nuevo token.
    if user_py.refresh_token:
        user_fb = firebase.auth().refresh(user_py.refresh_token)


def login_with_refresh(user):

    if not user.refresh_token:
        return None

    try:
        user_fb = firebase.auth().refresh(user.refresh_token)
        user.id_token = user_fb.get('idToken', None)
        user.refresh_token = user_fb.get('refreshToken', None)
        return user
    except Exception as e:
        return None


@login_required
def profile(request):
    user = request.user
    """:type : pupifire.models.User"""

    try:
        database = get_database(user).child('users').child(user.uid)
        datasnapshot = database.get()
    except FirebaseDatabaseException as e:
        print(e.message)
        return redirect(reverse('login'))

    value = datasnapshot.val()

    user.last_name = value.get('lastname')
    user.first_name = value.get('names')
    user.photo_url = value.get('url_image')
    user.comment = value.get('comment')
    user.save()

    return render(request, 'profile.html', {'user': user})


