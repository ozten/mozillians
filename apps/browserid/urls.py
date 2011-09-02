from django.conf.urls.defaults import patterns, url

from browserid import views

urlpatterns = patterns('',
    url('^foobar$', views.browserid_login, name='foobar'),

    url('^browserid_login', views.browserid_login, name='browserid_login'),
    url('^browserid_register', views.browserid_login, name='browserid_register'),
)
