from django.urls import path

from pupifire import views

app = 'pupifire'
urlpatterns = [
    path('', views.index, name='root'),
    path('index/', views.index, name='index'),
    path('tos/', views.tos, name='tos'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
    path('login/', views.login, name='login'),
    path('users/', views.users, name='users')
]
