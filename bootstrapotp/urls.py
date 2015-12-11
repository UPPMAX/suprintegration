
from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^back$', views.back, name='back'),
    url(r'^finish$', views.finish, name='finish'),
    url(r'^image$', views.image, name='image'),
]
