
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.landing, name='landing'),
    url(r'^sendtosupr$', views.sendtosupr, name='sendtosupr'),
    url(r'^back$', views.back, name='back'),
    url(r'^finish$', views.finish, name='finish'),
    url(r'^image$', views.image, name='image'),
]
