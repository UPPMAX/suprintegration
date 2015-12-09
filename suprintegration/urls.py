from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'suprintegration.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^getpasswd/', include('getpasswd.urls')),
    url(r'^bootstrapotp/', include('bootstrapotp.urls')),
)
