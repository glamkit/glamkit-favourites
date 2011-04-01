from django import template
from django.template.loader import render_to_string

from django.conf import settings

from ..favourites.models import Collection
from ..favourites.utils import get_shortcut

register = template.Library()

def _render_item(item, custom_template):
    template = [custom_template % {"app_label": item._meta.app_label, "module_name": item._meta.module_name}, 'favourites/includes/default_item.html']
    url = None if not hasattr(item, "get_absolute_url") else item.get_absolute_url()
    context = {"item": item, "url": url}
    return render_to_string(template, context)    

@register.simple_tag
def favourites_render_item(item):
    """
    @returns: item in the favourites collection rendered to html
    """
    return _render_item(item, settings.FAVOURITE_ITEM_TEMPLATE)

@register.simple_tag
def favourites_preview_collection_item(item):
    """
    Same as favourites_render_item, 
    yet creates smaller preview version <=> uses different template
    """
    return _render_item(item, settings.FAVOURITE_ITEM_TEMPLATE_PREVIEW)
                
@register.inclusion_tag('favourites/includes/favourites_links.html', takes_context=True)
def favourites_links(context, item):
    """
    If the user is not authenticated:
        show nothing
        # EVENTUALLY:  store the information in session
    
    Otherwise, 
        For the collections the item is in - show "remove" link
        For the collections the item is not in - show "add" link
        show "add to new collection" link
    """
    u = context["user"]
    visible = context.get("visible", False) # whether the menu should be initially visible
    
    if u.is_authenticated():
        # inefficient. yes. 
        # tons of sql queries. yes.
        # can do better? not with generic relations
        if not "favourites_media_showed" in context:
            include_media = True
            context["favourites_media_showed"] = True
        else:
            include_media = False
        model_name = get_shortcut(item)
        collections_in = []
        collections_out = []
        collections = []
        for collection in u.collection_set.all():
            if item in collection:
                collections_in.append({"collection": collection, "relation": collection.get_meta_information(item)})
            else:
                if item.__class__ in [t.model_class() for t in collection.allowed_models.all()]:
                    collections_out.append({"collection": collection})
            collections.append({"collection": collection})
        return locals()
    else:
        return {"anonymous": True}

@register.inclusion_tag('favourites/includes/collection_preview.html', takes_context=True)
def favourites_collection(context):
    """
    Display preview of the default collection
    """
    u = context["user"]
    if u.is_anonymous():
        return {"anonymous": True}
    collection = u.collection_set.get(default=True)
    items = collection[:settings.PREVIEW_ITEMS_NO]
    return locals()
   
@register.inclusion_tag('favourites/includes/collections_list.html', takes_context=True)
def favourites_collections_list(context):
    """
    Display the list of collections, with the appropriate links
    
    Do not link to the collection currently selected 
    """
    if context["user"].is_anonymous():
        return {"collections": []}
        
    collections = Collection.objects.filter(owner=context["user"])
    if "collection" in context:
        current_collection = context["collection"]
    return locals()
    
    

class CollectionItemInList(template.Node):
    def __init__(self, item, collection, var):
        self.item = template.Variable(item)
        self.collection = template.Variable(collection)
        self.var = var
        
    def render(self, context):
        item = self.item.resolve(context)
        collection = self.collection.resolve(context)
        
        context[self.var] = item in collection
        
        return ''

@register.tag(name="favourites_is_item_in_collection")
def favourites_is_item_in_collection(parser, token):
    """
    {% favourites_is_item_in_collection [item] [collection] as [var] %}
    """
    try:
        contents = token.contents.split()
        if len(contents) != 5:
            raise template.TemplateSyntaxError, "%r tag requires exactly four arguments: [item] [collection] as [var]" % token.contents.split()[0]
    except (ValueError, IndexError):
        raise template.TemplateSyntaxError, "%r tag requires four arguments: [item] [collection] as [var]" % token.contents.split()[0]
    return CollectionItemInList(contents[1], contents[2], contents[4])
