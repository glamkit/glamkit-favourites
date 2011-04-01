from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.template import Template, Context
from django.db.models.expressions import F

from ixc_common.decorators import render_to, resolve_or_404
from ixc_common.shortcuts import JSONResponse

from utils import resolve_object_or_404, can_modify_collection, can_be_ajax
from models import Collection, CollectionException, Relation
from forms import CollectionForm, RelationForm

"""
NOTE: decorator @can_modify_collection
    alter the function arguments;

after it is applied,
collection _is_ the actual Collection instance

other NOTE: 

Most of the views can act both as a normal views and as AJAX ones
non-javascript views functionality may not be ready at this stage
(GET requests ignored, templates missing/incorrect, etc.)


"""
@render_to('favourites/permission_denied.html')
def permission_denied(request):
    return {}

@render_to('favourites/public_collection_details.html')
def public_collection_details(request, collection):
    """
    View the public collection
    """
    return locals()
   
@render_to('favourites/collection_details.html')
@login_required
def collections_index(request):
    """
    Show the default collection 
    """
    if request.user.is_anonymous():
        return Http404()
        
    return {"collection": request.user.collection_set.get(default=True), "editable": True}
    
@render_to('favourites/collection_details.html')
@resolve_or_404(Collection, pk_arg="collection_id", instance_arg="collection")
def collection_details(request, collection):
    if collection.owner != request.user:
        if not collection.is_public:
            return HttpResponseRedirect(reverse("favourites.permission_denied"))
        return public_collection_details(request, collection)
    
    editable = True
    
    return locals()
    
@render_to('favourites/remove_collection.html')
@can_be_ajax
@can_modify_collection
def remove_collection(request, collection, is_ajax):
    if request.method == "POST":
        if 'cancel' in request.POST:
            return HttpResponseRedirect(reverse("favourites.collection_details", args=[collection.pk]))
        collection.delete()        
        url = reverse("favourites.collections_index")
        if is_ajax:
            return JSONResponse({"action": "redirect", "url": url})
        return HttpResponseRedirect(url)
    else:
        return locals()     
    
@render_to('favourites/edit_collection.html')
@can_be_ajax
@can_modify_collection
def edit_collection(request, collection, is_ajax):
    form = CollectionForm
    if request.method == "POST":
        form = form(request.POST, instance=collection)
        if is_ajax:
            if not form.is_valid():
                return JSONResponse({"action": "show_errors", "form": form.as_ul()})
            else:
                form.save()
                return JSONResponse({"details": render_to_string("favourites/includes/meta_collection.html", locals())})
        else:
            if not form.is_valid():
                return locals()
            else:
                if not 'cancel' in request.POST:
                    form.save()
                return HttpResponseRedirect(reverse("favourites.collection_details", args=[collection.pk]))
    form = form(instance=collection)
    if is_ajax:
        return JSONResponse({"action": "render_form", "form": form.as_ul()})
    else:
        return locals()
    
@render_to('favourites/edit_item.html')
@can_be_ajax
@can_modify_collection
@resolve_or_404(Relation, pk_arg="relation_id", instance_arg="relation")
def edit_item(request, collection, relation, is_ajax):
    form = RelationForm
    if request.method == "POST":
        form = form(request.POST, instance=relation)
        if is_ajax:
            if not form.is_valid():
                return JSONResponse({"action": "show_errors", "form": form.as_ul()})
            else:
                form.save()
                item = {"favourites_meta_info": relation}
                return JSONResponse({"details": render_to_string("favourites/includes/meta.html", locals())})
        else:
            if not form.is_valid():
                return locals()
            if not 'cancel' in request.POST:
                form.save()
            return HttpResponseRedirect(reverse("favourites.collection_details", args=[collection.pk]))
            
    form = form(instance=relation)
    if is_ajax:
        return JSONResponse({"action": "render_form", "form": form.as_ul()})
    else:
        return locals()
    
@can_modify_collection
@can_be_ajax
def swap_items(request, collection, is_ajax):
    try:
        from_ = int(request.REQUEST.get("from"))
        to = int(request.REQUEST.get("to"))
        relation_id = int(request.REQUEST.get("relation_id"))
        moved_r = Relation.objects.get(pk=relation_id)
        nearby_r = Relation.objects.filter(collection=collection).order_by('importance')[to]
                
        if to > from_:
            Relation.objects.filter(collection=collection).filter(importance__gt=nearby_r.importance).update(importance=F('importance') + 1)
            moved_r.importance = nearby_r.importance + 1
            moved_r.save()
        else:
            Relation.objects.filter(collection=collection).filter(importance__lt=nearby_r.importance).update(importance=F('importance') - 1)
            moved_r.importance = nearby_r.importance - 1
            moved_r.save()
            
        return JSONResponse({"status": "OK"})
    except (KeyError, ValueError, Relation.DoesNotExist):
        raise Http404()
    
   

_links_template = Template("{% load favourites %}{% favourites_links item %}")
def _show_links(item, user):
    c = Context({"item": item, "favourites_media_showed": True, "user": user, "visible": True})
    return _links_template.render(c)

@render_to('favourites/add_to_new_collection.html')
@can_be_ajax
@login_required
def add_to_new_collection(request, model_name, item_pk, is_ajax):
    item = resolve_object_or_404(model_name, item_pk)
    try:
        collection = Collection.objects.create_from(item, owner=request.user)
        url = reverse("favourites.collection_details", args=[collection.pk])
        if request.method == "POST" and is_ajax:
            return JSONResponse({"status": "OK", "action": "redirect", "url": url})   
        else:
            return HttpResponseRedirect(url)
    except (CollectionException):
        raise Http404()

@render_to('favourites/add_to_collection.html')
@can_be_ajax
@can_modify_collection
def add_to_collection(request, collection, model_name, item_pk, is_ajax):
    item = resolve_object_or_404(model_name, item_pk)
    try:
        collection.add_item(item)
        
        if request.method == "POST" and is_ajax:
            return JSONResponse({"status": "OK", "html": _show_links(item, request.user)})
        else:
            return HttpResponseRedirect(reverse("favourites.collection_details", args=[collection.pk]))
            
    except (CollectionException):
        raise Http404()

@render_to('favourites/remove_from_collection.html')
@can_be_ajax
@can_modify_collection
@resolve_or_404(Relation, pk_arg="relation_id", instance_arg="relation")
def remove_from_collection(request, collection, relation, is_ajax):  
    relation.delete() 
    
    if is_ajax and request.method == "POST":
        return JSONResponse({"status": "OK", "html": _show_links(relation.get_item(), request.user)})
    else:
        return HttpResponseRedirect(reverse("favourites.collection_details", args=[collection.pk]))