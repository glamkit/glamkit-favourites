from django.conf.urls.defaults import *

urlpatterns = patterns('favourites.views',
    url(r'^$', 'my_lists', name='favourites.my_lists'),
    url(r'^(?P<username>\w+)/$', 'favourites_lists', name='favourites.lists'),
    url(r'^(?P<username>\w+)/(?P<list_pk>\d+)/$', 'favourites_list', name='favourites.list'), #username is ignored in URL

    url(r'^(?P<username>\w+)/create/$', 'create_favourites_list', name='favourites.create_list'),
    url(r'^(?P<username>\w+)/create_item/$', 'create_favourites_item', name='favourites.create_item'), #other params are passed in POST

    url(r'^(?P<list_pk>\d+)/edit/$', 'edit_favourites_list', name='favourites.edit_list'),
    url(r'^(?P<list_pk>\d+)/delete/$', 'delete_favourites_list', name='favourites.delete_list'),

    url(r'^(?P<list_pk>\d+)/(?P<item_pk>\d+)/delete/$', 'delete_favourites_item', name='favourites.delete_item'),
)