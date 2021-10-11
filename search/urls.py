from django.urls import path

from . import views

urlpatterns = [
    path('home', views.home, name='home'),
    path('upload_file', views.upload_file, name='upload_file'),
    path('search', views.search, name='search'),
    path('clear', views.clear, name='clear'),
]