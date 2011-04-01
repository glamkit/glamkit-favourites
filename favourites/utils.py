from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.db.models.loading import get_model

import models

############## INTERNAL API ################

# TODO: throw appropriate exceptions
def shortcut2model():
    """
    Lazy evaluate a dictionary of model->shortcut from
    dictionary of shortcut->model
    """
    if hasattr(shortcut2model, 'a'):
        return shortcut2model.a
    shortcut2model.a = dict([(value, key) for key, value in settings.FAVOURITABLE_MODELS.items()])
    return shortcut2model.a

def get_shortcut(item):
    """
    Get a shortcut string corresponding to the instance <item>
    """
    return shortcut2model()["%s.%s" % (item._meta.app_label, item.__class__.__name__)]

def resolve_object_or_404(model_label, item_pk):
    model = get_model(*settings.FAVOURITABLE_MODELS.get(model_label, None).split(".", 1))
    if model is None:
        raise Http404
    try:
        return model.objects.get(pk=item_pk)
    except model.DoesNotExist:
        raise Http404

"""
x this decorator checks whether the user has the permission to modify the collection
 AND add the collection object to the argument
 
 - if the collection can not be resolved, 404 is raised
 - if user does not have the required permission, he is redirected to favourites.permission_denied
"""

def can_modify_collection(func):
    def wrapper(request, *args, **kw):
        assert 'collection_id' in kw, "Function has to accept 'collection_id' as a keyword argument"
        try:
            collection = models.Collection.objects.get(pk=int(kw.pop('collection_id')))
        except (models.Collection.DoesNotExist, ValueError):
            raise Http404()
        if not request.user == collection.owner:
            return HttpResponseRedirect(reverse('favourites.permission_denied'))
        return func(request, collection, *args, **kw)
    return wrapper

def can_be_ajax(func):
    def wrapper(request, *args, **kw):
        return func(request, *args, is_ajax="is_ajax" in request.REQUEST, **kw)
    return wrapper

############## EXTERNAL API ################

def times_favourited(item):
    """
    @returns: int - how many times item was favourited <=> to how many collections the item was added
    """
    return models.Collection.objects.containing(item).count()
    
    
def users_favourited(item):
    """
    @returns: QS of users who have favourited this item
    """
    return User.objects.filter(collection__relation__content_type=get_content_type(item), collection__relation__object_id=item.pk).distinct()
