import json
from json import JSONDecodeError

from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.urls import reverse

from pupifire.firebase.admin import request_custom_token, FirebaseAuthException, pull, push
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
    return redirect(reverse('pupifire:login'))


def verify(request):

    if request.method == 'POST':
        try:
            user = json.loads(request.POST.get('user'))

            # Actualizamos la información del usuario
            user_py, created = User.objects.get_or_create(pk=user.get('uid'))
            user_py.display_name = user.get('displayName')
            user_py.photo_url = user.get('photoUrl')
            user_py.email = user.get('email') or ''
            user_py.email_verified = user.get('emailVerified')
            user_py.phone_number = user.get('phoneNumber')
            user_py.is_fb_anonymous = user.get('isAnonymous')
            if not user_py.is_fb_anonymous:
                user_py.provider_id = user.get('providerData')[0].get('providerId')

            # Obtenemos un token personalizado para el usuario
            user_py.custom_token = request_custom_token(user_py.uid)

            # Logueamos al usuario en firebase
            sign_in = firebase.auth().sign_in_with_custom_token(user_py.custom_token)
            user_py.refresh_token = sign_in.get('refreshToken')
            user_py.id_token = sign_in.get('id_token')

            user_py.save()

            # Logueamos al usuario de Django y lo reenviamos al index.
            login(request, user_py)

        except (TypeError or JSONDecodeError):
            redirect(reverse('pupifire:logout'))
        except FirebaseAuthException:
            redirect(reverse('pupifire:logout'))

    return redirect(reverse('pupifire:index'))


def tos(request):
    return HttpResponse("Términos del servicio...")


def privacy_policy(request):
    return render(request, 'privacy_policy.html')


@login_required
def profile(request):

    user = request.user
    """:type : pupifire.models.User"""

    if request.method == 'POST':

        form = UserProfileForm(data=request.POST, files=request.FILES, instance=user)

        if form.is_valid():

            instance = form.save(commit=False)

            photo_profile = request.FILES.get('photo_profile')
            if isinstance(photo_profile, InMemoryUploadedFile):
                name = photo_profile.name.encode('utf-8').decode('utf-8')
                file = photo_profile.file
                get_storage(instance).child(instance.uid).child(name).put(file, instance.id_token)
                instance.photo_url = firebase.storage().child(instance.uid).child(name).get_url(instance.id_token)

            instance.save()
            push(instance)

            data = {
                'last_name': form.cleaned_data['last_name'],
                'first_name': form.cleaned_data['first_name'],
                'comment': form.cleaned_data['comment'],
                'shared_email': form.cleaned_data['shared_email'],
                'shared_phone': form.cleaned_data['shared_phone']
            }
            get_database(user).child('users').child(user.uid).update(data, user.id_token)

            return redirect(reverse('pupifire:index'))

    else:

        try:
            # Actualizamos la información del usuario desde Firebase Auth
            pull(user)
            # Recuperamos la información de perfil desde Firebase Database
            user_profile = get_database(user).child('users').child(user.uid).get(user.token)
        except FirebaseException:
            return redirect(reverse('pupifire:login'))

        form = UserProfileForm(instance=user, initial={
            'last_name': user_profile.val().get('last_name'),
            'first_name': user_profile.val().get('first_name'),
            'comment': user_profile.val().get('comment'),
            'shared_phone': user_profile.val().get('shared_phone', False),
            'shared_email': user_profile.val().get('shared_email', False)
        })

    return render(request, 'profile.html', {'form': form})
