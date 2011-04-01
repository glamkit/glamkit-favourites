from django.conf.urls.defaults import *

urlpatterns = patterns('favourites.views',
    url(r'^add_to_collection/(?P<collection_id>\d+)/$', 'add_to_collection', name='favourites.add_to_collection'),
    url(r'^add_to_new_collection/$', 'add_to_new_collection', name='favourites.add_to_new_collection'),
)