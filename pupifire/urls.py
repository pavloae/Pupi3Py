from django.urls import path

from pupifire import views

app = 'pupifire'
urlpatterns = [
    path('', views.index, name='root'),
    path('index/', views.index, name='index'),
    path('tos/', views.tos, name='tos'),
    path('privacy-policy/', views.privacy_policy, name='privacy-policy'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('verify/', views.verify, name='verify'),
    path('completeSignIn/', views.verify, name='verify'),
    path('profile/', views.profile, name='profile')
]
