from django import template
from ..models import FavouritesList
from django.contrib.contenttypes.models import ContentType

register = template.Library()

def do_get_favourites_lists(parser, token):
    try:
        tag_name, user, _as, varname = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("use '%r user [obj] as context_name" % token.contents.split()[0])
    return FavouritesListsNode(user, varname)
register.tag('get_favourites_lists', do_get_favourites_lists)

class FavouritesListsNode(template.Node):
    def __init__(self, user, varname):
        self.user = template.Variable(user)
        self.varname = varname

    def render(self, context):
        try:
            actual_user = self.user.resolve(context)
            
            if not context.has_key(self.varname): #should save on db calls, but means that only can be used with one user + varname per template...
                if context['request'].user == actual_user: #it's me!
                    lists = FavouritesList.objects.filter(owner=actual_user)
                else:
                    lists = FavouritesList.objects.filter(owner=actual_user, public=True)
            
                context[self.varname] = lists

        except template.VariableDoesNotExist:
            pass
        return ''
        
@register.simple_tag
def get_content_type_id(obj):
    return unicode(ContentType.objects.get_for_model(type(obj)).id)
