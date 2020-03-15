import json
from json import JSONDecodeError

from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.urls import reverse

from pupifire.firebase.admin import request_custom_token, FirebaseAuthException
from pupifire.firebase.user import get_database, FirebaseException, get_storage, firebase, get_auth
from pupifire.forms import UserProfileForm
from pupifire.models import User

image_profile_default = "/static/img/image_profile_default.png"


@login_required
def index(request):
    return render(request, 'index.html')


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
            sign_in = firebase.auth().sign_in_with_custom_token(custom_token)

            # Actualizamos la información del usuario
            user_py, created = User.objects.get_or_create(pk=user.get('uid'))
            user_py.custom_token = custom_token
            user_py.refresh_token = sign_in.get('refreshToken')
            user_py.id_token = sign_in.get('id_token')
            user_py.email = user.get('email') or ''
            user_py.phone = user.get('phoneNumber', None)
            user_py.save()

            # Logueamos al usuario de Django y lo reenviamos al index.
            login(request, user_py)

        except (TypeError or JSONDecodeError):
            redirect(reverse('logout'))
        except FirebaseAuthException:
            redirect(reverse('logout'))

    return redirect(reverse('index'))


def tos(request):
    return HttpResponse("Términos del servicio...")


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


@login_required
def profile(request):

    user = request.user
    """:type : pupifire.models.User"""

    if request.method == 'POST':
        form = UserProfileForm(data=request.POST, files=request.FILES)

        if form.has_changed() and form.is_valid():
            photo_profile = request.FILES.get('photo_profile')
            """:type : InMemoryUploadedFile"""
            if photo_profile:
                name = photo_profile.name.encode('utf-8').decode('utf-8')
                file = photo_profile.file
                get_storage(user).child(user.uid).child(name).put(file, user.id_token)
                photo_url = firebase.storage().child(user.uid).child(name).get_url(user.id_token)

                data = {
                    'lastname': form.cleaned_data['last_name'],
                    'names': form.cleaned_data['first_name'],
                    'comment': form.cleaned_data['comment'],
                    'url_image': photo_url
                }

                get_database(user).child('users').child(user.uid).update(data, user.id_token)

            return redirect(reverse('index'))

    else:

        # Traemos la información del usuario desde Firebase Database
        try:
            if not user.id_token:
                get_auth(user).refresh_token()
            profile = get_database(user).child('users').child(user.uid).get(user.id_token)
            account_info = get_auth(user).get_account_info(user.id_token)
            user_info = account_info.get('users')[0]
            provider = user_info.get('providerUserInfo')[0]
            account_info = get_auth(user).get_account_info(user.id_token).get('users')[0].get('providerUserInfo')[0]
            # phone = get_database(user).child('phones').child(user.phone).get(user.id_token)
            # email = get_database(user).child('emails').child(user.email).get(user.id_token)
        except FirebaseException:
            return redirect(reverse('login'))

        # Armamos el formulario
        form = UserProfileForm(
            initial={
                'photo_url': profile.val().get('url_image', image_profile_default),
                'last_name': profile.val().get('lastname'),
                'first_name': profile.val().get('names'),
                'comment': profile.val().get('comment'),
                # 'phone': phone.val(),
                'share_phone': True,
                'email': user.email_user,
                'share_email': True
            }
        )

    return render(request, 'profile.html', {'form': form})
