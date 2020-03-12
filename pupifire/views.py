import json
from json import JSONDecodeError

from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.urls import reverse

from pupifire.firebase.admin import request_custom_token, FirebaseAuthException
from pupifire.firebase.user import get_database, sign_in_with_custom_token, FirebaseException, get_storage, firebase
from pupifire.forms import UserProfileForm
from pupifire.models import User


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
        user_profile_form = UserProfileForm(data=request.POST, files=request.FILES)
        if user_profile_form.is_valid():
            photo_profile = request.FILES.get('photo_profile')
            """:type : InMemoryUploadedFile"""
            if photo_profile:
                name = photo_profile.name.encode('utf-8').decode('utf-8')
                firebase.storage().child(user.uid).child(name).put(photo_profile.file)
                photo_url = firebase.storage().child(user.uid).child(name).get_url(user.id_token)

                data = {
                    'lastname': user_profile_form.cleaned_data['last_name'],
                    'names': user_profile_form.cleaned_data['first_name'],
                    'comment': user_profile_form.cleaned_data['comment'],
                    'url_image': photo_url
                }

                get_database(user).child('users').child(user.uid).update(data, user.id_token)

        return redirect(reverse('index'))

    else:

        try:
            datasnapshot = get_database(user).child('users').child(user.uid).get()
        except FirebaseException:
            return redirect(reverse('login'))

        value = datasnapshot.val()

        user.last_name = value.get('lastname')
        user.first_name = value.get('names')
        user.photo_url = value.get('url_image')
        user.comment = value.get('comment')
        user.save()

        form = UserProfileForm(
            initial={
                'last_name': user.last_name,
                'first_name': user.first_name,
                'comment': user.comment,
                'phone': user.phone,
                'share': True
            }
        )

    return render(request, 'profile.html', {'user': user, 'form': form})
