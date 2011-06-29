from django import template
from ..models import FavouritesList
from django.contrib.contenttypes.models import ContentType

register = template.Library()

class FavouritesListsNode(template.Node):
    def __init__(self, owner, context_name, qs_func):
        self.owner = template.Variable(owner)
        self.context_name = context_name
        self.qs_func = qs_func

    def render(self, context):
        try:
            owner = self.owner.resolve(context)
            current_user = context['request'].user
            context[self.context_name] = self.qs_func(owner=owner, current_user=current_user)
        except template.VariableDoesNotExist:
            pass
        return ''
 
def do_lists_owned_by_visible_to(parser, token):
    try:
        tag_name, owner, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use {%% %s owner as context_name %%}" % token.contents.split()[0])
    return FavouritesListsNode(owner=owner, context_name=context_name, qs_func=FavouritesList.objects.owned_by_visible_to)
register.tag('lists_owned_by', do_lists_owned_by_visible_to)

def do_lists_edited_by(parser, token):
    try:
        tag_name, owner, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use '%s owner as context_name'" % token.contents.split()[0])
    return FavouritesListsNode(owner=owner, context_name=context_name, qs_func=FavouritesList.objects.edited_by_visible_to)
register.tag('lists_edited_by', do_lists_edited_by)

def do_lists_editable_by(parser, token):
    """
    editable = owned | edited
    """
    try:
        tag_name, owner, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use '%s owner as context_name'" % token.contents.split()[0])
    return FavouritesListsNode(owner=owner, context_name=context_name, qs_func=FavouritesList.objects.editable_by_visible_to)
register.tag('lists_editable_by', do_lists_editable_by)

###

class PublicFavouritesListsNode(template.Node):
    def __init__(self, obj, context_name, qs_func):
        self.obj = template.Variable(obj)
        self.context_name = context_name
        self.qs_func = qs_func

    def render(self, context):
        try:
            obj = self.obj.resolve(context)
            current_user = context['request'].user
            context[self.context_name] = self.qs_func(item=obj, user=current_user)
        except template.VariableDoesNotExist:
            pass
        return ''
 
def do_public_lists(parser, token):
    try:
        tag_name, _containing, obj, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use {%% %s containing object as context_name %%}" % token.contents.split()[0])
    return PublicFavouritesListsNode(obj=obj, context_name=context_name, qs_func=FavouritesList.objects.containing_item_and_visible_to)
register.tag('public_lists', do_public_lists)


########

class ListsPermissionsNode(template.Node):
    def __init__(self, owner, context_name):
        self.owner = template.Variable(owner)
        self.context_name = context_name

    def render(self, context):
        try:
            owner = self.owner.resolve(context)
            current_user = context['request'].user
            context[self.context_name] = FavouritesList.get_permissions_on_lists_owned_by(owner=owner, user=current_user)
        except template.VariableDoesNotExist:
            pass
        return ''
 
def do_permissions_on_lists_owned_by(parser, token):
    try:
       tag_name, owner, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use '%s owner as context_name'" % token.contents.split()[0])
    return ListsPermissionsNode(owner=owner, context_name=context_name)
register.tag('permissions_on_lists_owned_by', do_permissions_on_lists_owned_by)

#########
########

# What is going on here, with repeated class name?
class ListPermissionsNode(template.Node):
    def __init__(self, lst, context_name):
        self.lst = template.Variable(lst)
        self.context_name = context_name

    def render(self, context):
        try:
            lst = self.lst.resolve(context)
            current_user = context['request'].user
            context[self.context_name] = lst.get_permissions_for_user(user=current_user)
        except template.VariableDoesNotExist:
            pass
        return ''
 
def do_permissions_on_list(parser, token):
    try:
       tag_name, lst, _as, context_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(u"use '%s list as context_name'" % token.contents.split()[0])
    return ListPermissionsNode(lst=lst, context_name=context_name)
register.tag('permissions_on_list', do_permissions_on_list)

#########
       
@register.simple_tag
def get_content_type_id(obj):
    return unicode(ContentType.objects.get_for_model(type(obj)).id)
