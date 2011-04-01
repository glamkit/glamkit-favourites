from django.conf.urls.defaults import *

urlpatterns = patterns('favourites.views',
    url(r'^$', 'collection_details', name='favourites.collection_details'),
    url(r'^remove/$', 'remove_collection', name='favourites.remove_collection'),
    url(r'^edit/$', 'edit_collection', name='favourites.edit_collection'),
    url(r'^swap_items/$', 'swap_items', name='favourites.swap_items'),
    url(r'^(?P<relation_id>\d+)/edit/$', 'edit_item', name='favourites.edit_item'),
    url(r'^(?P<relation_id>\d+)/remove_from_collection/$', 'remove_from_collection', name='favourites.remove_from_collection'),
)