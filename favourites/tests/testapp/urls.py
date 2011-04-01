from django.conf.urls.defaults import *

urlpatterns = patterns('myapp.views',
    url(r'^book/(?P<book_id>\d+)/$', 'book_details', name='myapp.book_details'),
    url(r'^painting/(?P<painting_id>\d+)/$', 'painting_details', name='myapp.painting_details'),
    url(r'^painting_list/$', 'painting_list', name='myapp.painting_list'),
    url(r'^book_list/$', 'book_list', name='myapp.book_list'),
)
