from django.urls import path

import pupifire.view_admin_fire
from pupifire import views

app = 'pupifire'
urlpatterns = [
    path('', views.index, name='root'),
    path('index/', views.index, name='index'),
    path('tos/', views.tos, name='tos'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
    path('login/', views.user_login, name='login'),
    path('verify/', pupifire.view_admin_fire.verify_token, name='verify'),
    path('users/', views.users, name='users')
]
