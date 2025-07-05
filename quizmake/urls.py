from django.urls import path
from . import views

urlpatterns = [
    path('', views.quizmakerhome, name='quizmakerhome'),
] 