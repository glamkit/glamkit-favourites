from django import template

register = template.Library()

@register.inclusion_tag('myapp/includes/nav.html', takes_context=True)
def myapp_nav(context):
    user = context['user']
    return locals()
    