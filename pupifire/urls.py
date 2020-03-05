from django.urls import path

from pupifire import views

app = 'pupifire'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('users/', views.users, name='users')
]
