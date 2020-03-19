import json
import os
from collections import OrderedDict

from json import JSONDecodeError
from operator import itemgetter

import unidecode as unidecode
from django.contrib import auth
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import HttpResponse

from django.shortcuts import render, redirect
from django.urls import reverse
from tablib import Dataset

from Pupi3Py import settings
from pupifire.firebase.admin import request_custom_token, FirebaseAuthException, pull, push
from pupifire.firebase.user import get_database, FirebaseException, get_storage, firebase, get_auth
from pupifire.forms import UserProfileForm, CourseProfile, InstitutionForm
from pupifire.models import User

image_profile_default = "/static/img/image_profile_default.png"

DATA_DIR = os.path.join(settings.BASE_DIR, 'Pupi3Py/data')

with open(os.path.join(DATA_DIR, 'provincias.csv'), 'r') as f:
    state_dataset = Dataset().load(f.read()).subset(cols=['code', 'name'])

with open(os.path.join(DATA_DIR, 'geonames.csv'), 'r') as f:
    city_dataset = Dataset().load(f.read()).subset(cols=['cp', 'code', 'name'])


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
def user_profile(request):

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
                result = get_storage(instance).child('user/'+instance.uid+'/'+name).put(file, instance.token)
                photo_url = get_storage(instance).child('user/'+instance.uid+'/'+name).get_url(result.get('downloadTokens'))
                instance.photo_url = photo_url


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


@login_required
def schedule(request):
    events = [
        {
            'title': 'Estática y Resistencia de Materiales',
            'start': '2020-03-18T09:30:00-03:00',
            'end': '2020-03-18T11:50:00-03:00',
            'url': '/index/'
        }]
    return render(request, 'schedule.html', {'events': events})


@login_required
def own_memberships(request):
    """
        Esta vista muestra todos los cursos a los que pertenece el usuario, ya sea como profesor o como alumno
    :param request:
    :return:
    """
    user = request.user
    """:type : User"""
    context = {}
    ref = get_database(user).child("memberships")
    datasnapshot = ref.order_by_child("user_id").equal_to(user.uid).limit_to_first(100).get(user.token)
    values = datasnapshot.val()

    if values:
        memberships = []
        for key, value in datasnapshot.val().items():
            memberships.append({'pk': key, 'value': value})
        context.update({'memberships': memberships})
    return render(request, 'memberships.html', context)


@login_required
def course_profile(request, cid=None):
    user = request.user
    """:type : User"""

    if request.method == 'POST':

        return redirect(reverse('pupifire:courses'))

    datasnapshot = get_database(user).child("courses").child(cid).get(user.token)
    members = datasnapshot.val().get('members')
    profile = datasnapshot.val().get('profile')

    data = {'year': profile.get('year'), 'classroom': profile.get('classroom'), 'owner': profile.get('owner')}
    institution = profile.get('institution')
    if isinstance(institution, dict):
        data.update({
            'institution_id': institution.get('institution_id'),
            'institution_name': institution.get('name')
        })

    subject = profile.get('subject')
    if isinstance(subject, dict):
        data.update({
            'subject_id': subject.get('subject_id'),
            'subject_name': subject.get('name'),
            'grade': subject.get('grade')
        })

    form = CourseProfile(data=data)
    return render(request, 'course_profile.html', {'form': form})


def course_classes(request, cid=None):
    pass


def schools_by_city(request, state=None, city=None):

    context = {}
    # state = state or request.session.get('state')
    # city = city or request.session.get('city')

    if isinstance(state, str):
        state_clean = unidecode.unidecode(state.lower())
        for row in state_dataset:
            if state_clean == unidecode.unidecode(row[1].lower()):
                context.update({'state': {'code': row[0], 'name': row[1]}})
                request.session.update({'state': row[1]})
                break

    if 'state' not in context:
        request.session.pop('state', None)
        state_list = []
        for row in state_dataset:
            state_list.append({'code': row[0], 'name': row[1]})
        state_list.sort(key=itemgetter('name'))
        context.update({'states': state_list})
        return render(request, 'cities.html', context)

    if isinstance(city, str):
        city_clean = unidecode.unidecode(city.lower())
        cp = None
        near_cities = []
        for row in city_dataset:
            if row[1] != context['state'].get('code'):
                continue
            if city_clean == unidecode.unidecode(row[2].lower()):
                cp = int(row[0])
                request.session.update({'city': row[2]})
            else:
                near_cities.append(row[2])
        return redirect(reverse('pupifire:schools_cp', args=(cp,)))
    else:
        city_list = []
        for row in city_dataset:
            if row[1] == context['state'].get('code'):
                city_list.append({'cp': row[0], 'code': row[1], 'name': row[2]})
        city_list.sort(key=itemgetter('name'))
        context.update({'cities': city_list})

    return render(request, 'cities.html', context)


def courses_by_school(request, institution_id):

    user = request.user
    context = {}
    ref = get_database(user).child('courses')
    datasnapshot = ref.order_by_child("institution_id").equal_to(institution_id).limit_to_first(100).get()
    values = datasnapshot.val()

    if values:
        course_list = []
        for key, value in values.items():
            course_list.append({'pk': key, 'value': value})
        context.update({'courses': course_list})

    return render(request, 'courses.html', context)


def subjects_by_school(request, institution_id):
    return render(request, 'inicio.html')


def schools_by_cp(request, cp):

    user = request.user
    """:type : User"""

    request.session.update({'cp': cp})
    state = request.session.get('state')
    city = request.session.get('city')

    context = {'cp': cp, 'state': state, 'city': city}

    if isinstance(city, str):
        near_cities = []
        for row in city_dataset:
            if row[0] != str(cp):
                continue
            if city != row[2]:
                near_cities.append(row[2])
        if len(near_cities) > 0:
            context.update({'near_cities': ','.join(near_cities)})

    datasnapshot = get_database(user).child('institutions').order_by_child('cp').equal_to(cp).limit_to_first(100).get()
    values = datasnapshot.val()

    if values:
        schools = []
        for key, value in values.items():
            schools.append({'pk': key, 'value': value})
        context.update({'schools': schools})

    return render(request, 'schools.html', context)


@login_required
def school_create(request, cp):

    user = request.user
    """:type : User"""

    state = request.session.get('state')
    city = request.session.get('city')

    if request.method == 'POST':

        form = InstitutionForm(data=request.POST)

        if form.is_valid():

            data = {
                'name': form.cleaned_data['name'],
                'address': form.cleaned_data['address'],
                'city': city,
                'state': state,
                'cp': cp,
                'phone': form.cleaned_data['phone'],
                'level': form.cleaned_data['level'],
                'email': form.cleaned_data['email'],
                'public': True,
                user.uid: {'admin': True}}
            get_database(user).child('institutions').push(data, user.token)

            return redirect(reverse('pupifire:schools'))

    else:

        form = InstitutionForm()

    return render(request, 'institution.html', {'form': form})
