from django.urls import path

from pupifire import views

app_name = 'pupifire'
urlpatterns = [
    path('', views.index, name='root'),
    path('index/', views.index, name='index'),

    # Login
    path('tos/', views.tos, name='tos'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
    path('accounts/login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/', views.verify, name='verify'),
    path('completeSignIn/', views.verify, name='complete'),

    # Profile
    path('perfil/', views.user_profile, name='profile'),

    # Schedule
    path('agenda/', views.schedule, name='schedule'),

    # Courses
    path('cursos/', views.own_memberships, name='courses'),
    path('cursos/<str:cid>/profile/', views.course_profile, name='course_profile'),
    path('cursos/<str:cid>/classes/', views.course_classes, name='course_classes'),

    # Escuelas
    path('escuelas/', views.schools_by_city, name='schools'),
    path('escuelas/<int:cp>/', views.schools_by_cp, name='schools_cp'),
    path('escuelas/<int:cp>/crear/', views.school_create, name='schools_create'),
    path('escuelas/cursos/<str:institution_id>/', views.courses_by_school, name='courses_school'),
    path('escuelas/materias/<str:institution_id>/', views.subjects_by_school, name='subjects_school'),
    path('escuelas/<str:state>/', views.schools_by_city, name='schools_state'),
    path('escuelas/<str:state>/<str:city>/', views.schools_by_city, name='schools_city'),


]
