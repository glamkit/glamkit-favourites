from django.conf.urls.defaults import *

# that's how we define an item
# possible model_names are defined in favourites_conf.py
urlpatterns = patterns('',
    (r'^(?P<model_name>\w+)/(?P<item_pk>\d+)/', include('favourites.urls_items')),
    (r'^collection/(?P<collection_id>\d+)/', include('favourites.urls_collections')),
)

urlpatterns += patterns('favourites.views',
    url(r'^$', 'collections_index', name='favourites.collections_index'),
    url(r'^permission_denied/$', 'permission_denied', name='favourites.permission_denied')
)