from django.conf.urls import url
from django.contrib.auth.views import logout
from accounts import views


urlpatterns = [
    url(r'^send_login_email$', views.send_login_email, name='send_login_email'),
    url(r'^login$', views.login, name='login'),
    url('^logout$', logout, {'next_page': '/'}, name='logout'),
]