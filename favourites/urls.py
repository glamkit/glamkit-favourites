from django.conf.urls.defaults import *

urlpatterns = patterns('favourites.views',
    url(r'^$', 'my_lists', name='favourites.my_lists'),
    
    #view all lists for user, create list for user
    url(r'^user/(?P<username>\w+)/$', 'favourites_lists', name='favourites.lists'),
    url(r'^user/(?P<username>\w+)/create/$', 'create_favourites_list', name='favourites.create_list'),
    
    #view list, edit list, delete list, create list item
    url(r'^(?P<list_pk>\d+)/$', 'favourites_list', name='favourites.list'), #username is ignored in URL
    url(r'^(?P<list_pk>\d+)/edit/$', 'edit_favourites_list', name='favourites.edit_list'),
    url(r'^(?P<list_pk>\d+)/delete/$', 'delete_favourites_list', name='favourites.delete_list'),
    
    #create list item (params are passed in in POST)
    url(r'^item/create/$', 'create_favourites_item', name='favourites.create_item'),

    #delete list item
    url(r'^(?P<list_pk>\d+)/(?P<item_pk>\d+)/delete/$', 'delete_favourites_item', name='favourites.delete_item'),
)