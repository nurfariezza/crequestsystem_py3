from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^login/$', views.loginview, name='loginview'),
    #url(r'^auth/callback/$', views.oauthcallback, name='oauthcallback'),
    url(r'^auth/$', views.auth, name='auth'),
    url(r'^logoff/$', views.logoff, name='logoff'),
    url(r'^$', views.home, name='home'),
    #url(r'^list/$', views.list, name='list'),
    url(r'^list/$', views.list, name='list'),
    url(r'^create/$', views.create, name='create'),
    url(r'^submit/$', views.submit, name='submit'),
    url(r'^edit/(?P<pid>[0-9]+)$', views.edit, name='edit'),
    url(r'^update/(?P<pid>[0-9]+)$', views.update, name='update'),
    url(r'^cancel/(?P<pid>[0-9]+)$', views.cancelstatus, name='cancelstatus'),
    url(r'^search/$', views.search, name='search'), #(?P<pid>[0-9]+)$
    url(r'^download/$', views.download, name='download'),
    url(r'^upload/create/$', views.uploadcreate, name='uploadcreate'),
    url(r'^upload/create/list/$', views.uploadcreatelist, name='uploadcreatelist'),
    url(r'^upload/edit/(?P<pid>[0-9]+)$', views.uploadedit, name='uploadedit'),
    url(r'^upload/edit/list/(?P<pid>[0-9]+)$', views.uploadeditlist, name='uploadeditlist'),
    url(r'^upload/file/$', views.getuploadfile, name='getuploadfile'),
    url(r'^upload/delete/$', views.uploaddelete, name='uploaddelete'),
    url(r'^history/(?P<pid>[0-9]+)$', views.history, name='history'),
    url(r'^comment/(?P<pid>[0-9]+)$', views.comment, name='comment'),
    url(r'^createcomment/(?P<pid>[0-9]+)$', views.createcomment, name='createcomment'),
    url(r'^pushnotify/(?P<pid>[0-9]+)$', views.pushnotify, name='pushnotify'),
    url(r'^verified/(?P<pid>[0-9]+)$', views.verified, name='verified'),
    url(r'^tempcreate/$', views.tempcreate, name='tempcreate'),
    url(r'^tempsubmit/$', views.tempsubmit, name='tempsubmit'),
    url(r'^templist/$', views.templist, name='templist'),
    url(r'^viewtemplist/$', views.viewtemplist, name='viewtemplist'),
    url(r'^template/edit/(?P<pid>[0-9]+)$', views.getedittemplatedata, name='getedittemplatedata'),
    url(r'^edittemplate/(?P<pid>[0-9]+)$', views.edittemplate, name='edittemplate'),
    url(r'^edittemplate2/(?P<pid>[0-9]+)$', views.edittemplate2, name='edittemplate2'),
    url(r'^createuser/$', views.createuser, name='createuser'),
    #url(r'^autoreminder/$', views.autoreminder, name='autoreminder'),
    #url(r'^verify_reminder/$', views.verify_reminder, name='verify_reminder'),
    url(r'^auto_verified/$', views.auto_verified, name='auto_verified'),

    url(r'^$', views.home, name='home'),
    url(r'^signout/$', views.sign_out, name='signout'),
    url(r'^signin/$', views.sign_in, name='signin'),
    url(r'^callback/$', views.oauthcallback, name='oauthcallback'),
    #path('', views.home, name='home'),

   







]
