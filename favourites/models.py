import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings

from ixc_common.decorators import alters_data, post_save_handler
from ixc_common import testing


"""
Preferably all calls to the favouriting system
should be done through the API provided by the
Collection class

It is also preferable to use high-level API
(Collection.add_item, Collection.remove_item, item in Collection,
for item in Collection, etc.)

"""



def favouritable_models():
    if hasattr(favouritable_models, "model_list"):
        return favouritable_models.model_list
    from django.db.models.loading import get_model
    favouritable_models.model_list = []
    l = favouritable_models.model_list # shortcut
    error = "Model defined in settings.FAVOURITABLE_MODELS does not exist"
    for model_name in settings.FAVOURITABLE_MODELS.values():
        if model_name.count(".") < 1:
            raise CollectionException(error)
        model = get_model(*model_name.split(".", 1))
        if model is None:
            raise CollectionException(error)
        l.append(model)
    return l
    

class CollectionModelRelation(models.Model):
    collection = models.ForeignKey('Collection')
    content_type = models.ForeignKey(ContentType)
    
    def save(self, *args, **kw):
        if not self.content_type.model_class() in favouritable_models():
            raise CollectionException("allowed_models has to be a subset of settings.FAVOURITABLE_MODELS")
        return super(self.__class__, self).save(*args, **kw)
    
    class Meta:
        unique_together = (("content_type", "collection"),)
    
class CollectionManager(models.Manager):
    def create_from(self, item, **kwargs):
        """
        Create a new collection from an item, where allowed_models is the list containing an item class
        kwargs correspond to parameters of Collection
        
        item has to be a model instance
        
        @throws: CollectionException
        """
        
        c = self.model.objects.create(allowed_models=[item.__class__], **kwargs)
        c.add_item(item)
        return c
        
    def containing(self, item):
        """
        @returns: QS of collections containing the given item
        """
        
        return self.model.objects.filter(relation__content_type=ContentType.objects.get_for_model(item), relation__object_id=item.pk)
        
    def owned_by(self, user):
        """
        @returns: QS of collections owned by the given user
        """
        return self.model.objects.filter(owner=user)
        
class Collection(models.Model):
    """    
    # Setting settings first:
    >>> testing.load_dummy_app('favourites.tests.myapp')
    >>> from myapp.models import Book, Painting, Movie
    >>> favouritable_models.model_list = [Book, Painting]
    
    # 'allowed_models' sets what items are allowed in the collection
    # 'allowed_models' has to be a subset of settings.FAVOURITABLE_MODELS
    >>> u = User.objects.create(username='test')
    >>> c = Collection.objects.create(owner=u, allowed_models=[Book], description='book collection')
    >>> book = Book.objects.create(title='awesome book')
    'add_item' is a syntax sugar for adding items to the collection
    It is the same as Relation.objects.create(collection=c, ...etc)
    >>> c.add_item(book)
    >>> painting = Painting.objects.create(title='awesome painting')
    >>> c.add_item(painting)
    Traceback (most recent call last):
        ...
    CollectionException: Adding an item of non-allowed type to the collection
    >>> other_c = Collection.objects.create(owner=u, allowed_models=[Movie])
    Traceback (most recent call last):
        ...
    CollectionException: allowed_models has to be a subset of settings.FAVOURITABLE_MODELS
    
    # Collection manager has some syntactic sugar methods
    >>> treasure_island = Book.objects.create(title='Treasure island')
    >>> c = Collection.objects.create_from(owner=u, item=treasure_island, description='awesome collection')
    >>> unicode(c.allowed_models.all()) == unicode([ContentType.objects.get_for_model(book)])
    True
    >>> c.relation_set.all()
    [<<Book: 'Treasure island'> for <Collection: 'awesome collection'>>]
    
    >>> c1 = Collection.objects.create(description='awesome book collection', allowed_models=[Book], owner=u)
    >>> empire_v = Book.objects.create(title='Empire V')
    >>> c1.add_item(empire_v)
    
    # Custom manager method to get all collections containing a particular item
    >>> qs = Collection.objects.containing(empire_v)
    >>> len(qs) == 1 and qs[0] == c1
    True
    
    # Collection class defines custom __iter__ and __contains__ methods
    >>> harry_potter = Book.objects.create(title='Harry Potter')
    >>> c1.add_item(harry_potter)
    >>> do_NOT_read_me = Book.objects.create(title='Twilight')
    >>> do_NOT_read_me in c1
    False
    >>> harry_potter in c1
    True
    >>> for obj in c1:
    ...    print obj
    <Book: 'Empire V'>
    <Book: 'Harry Potter'>
    
    # some more syntactic sugar
    >>> from favourites.utils import times_favourited, users_favourited
    >>> u1 = User.objects.create(username='cheshire')
    >>> c3 = Collection.objects.create_from(empire_v, owner=u1)
    >>> times_favourited(empire_v)
    2
    >>> sorted([u.username for u in users_favourited(empire_v)])
    ['cheshire', 'test']
    >>> testing.cleanup()
    """
    
    is_public = models.BooleanField(default=False)
    
    created = models.DateField(default=datetime.date.today, editable=False)
   
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    owner = models.ForeignKey(User, editable=False)
    
    # the collection which is associated by default with the
    # user. There is only one default collection per user
    default = models.BooleanField(default=False, editable=False)
    
    allowed_models = models.ManyToManyField(ContentType, through=CollectionModelRelation, editable=False)
    
    objects = CollectionManager()
    
    def _new_collection_name(self):
        name = self.owner.first_name if self.owner.first_name else self.owner.username
        return settings.NEW_COLLECTION_NAME % name
    
    def save(self, *args, **kwargs):
        create_relations = False
        if not self.id:
            allowed_models = getattr(self, '_allowed_models', favouritable_models())
            create_relations = True
        if not self.title:
            self.title = self._new_collection_name()
        super(self.__class__, self).save(*args, **kwargs)
        if create_relations:
            for model in allowed_models:
                CollectionModelRelation.objects.create(collection=self, content_type=ContentType.objects.get_for_model(model))
                
    def delete(self, *args, **kwargs):
        if self.default:
            # at all times there needs to be exactly one default collection
            try:
                collection = self.owner.collection_set.filter(default=False)[0]
                collection.default = True
                collection.save()
            except IndexError:
                _create_default_collection(instance=self.owner, created=True, sender=None)
        super(self.__class__, self).delete(*args, **kwargs)
    
    def __contains__(self, item):
        try:
            self.relation_set.get(content_type=ContentType.objects.get_for_model(item), object_id=item.pk)
        except Relation.DoesNotExist:
            return False
        else:
            return True
        
    def _get_qs(self):
        """
        Get the queryset of relations
        """
        return self.relation_set.order_by('-importance')
        
    def __iter__(self):
        for relation in self._get_qs():
            item = relation.content_type.model_class().objects.get(pk=relation.object_id)
            # here comes a weird trick
            item.favourites_meta_info = relation # now we can do item.favourites_meta_info.description
            yield item
    
    def __getitem__(self, i):
        relations = self._get_qs()[i]
        if isinstance(relations, Relation): # collection[3]
            item = relation.content_type.model_class().objects.get(pk=relation.object_id)
            item.favourites_meta_info = relation
            return item
        
        # collection[:12]
        qs = []
        for relation in relations:
            item = relation.content_type.model_class().objects.get(pk=relation.object_id)
            item.favourites_meta_info = relation
            qs.append(item)
        return qs
            
            
    def __unicode__(self):
        return self.title
    
    def __init__(self, *args, **kwargs):
        if 'allowed_models' in kwargs:
            self._allowed_models = kwargs.pop('allowed_models')
        super(self.__class__, self).__init__(*args, **kwargs)
        
    def _get_item(self, item):
        """
        Tries to get an item Relation instance, assuming the item is in 
        this collection
        
        @throws: Relation.DoesNotExist
        """
        return Relation.objects.get(collection=self, content_type=ContentType.objects.get_for_model(item), object_id=item.pk)
    
    def add_item(self, item, **kwargs):
        """
        Add an Item to the collection
        kwargs correspond to the optional fields in Relation
        
        @throws: CollectionException (item is of an inappropriate type)
        """
        if item in self:
            return
        Relation.objects.create(collection=self, content_type=ContentType.objects.get_for_model(item), object_id=item.pk, **kwargs)
        
    def remove_item(self, item):
        """
        Remove an item from the collection
        
        @throws: CollectionException (item is not in the collection)
        """
        try:
            self._get_item(item).delete()
        except Relation.DoesNotExist:
            raise CollectionException("Trying to delete an item not in the collection")
        
    def get_meta_information(self, item):
        """
        Tries to get the meta information from the item,
        assuming the item is in the collection 'self'
        
        @returns: dict
        @throws: CollectionException (item is not in the collection)
        """
        try:
            return self._get_item(item)
        except Relation.DoesNotExist:
            raise CollectionException("Trying to get information about item not in the collection")
        
        
    class Meta:
        unique_together = ()
        
    
class Relation(models.Model):
    collection = models.ForeignKey(Collection, editable=False)
    
    importance = models.FloatField(editable=False, db_index=True) # items with larger importance go first
    description = models.TextField(blank=True, null=True)
    
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.PositiveIntegerField(editable=False)
    
    def get_item(self):
        return self.content_type.model_class().objects.get(pk=self.object_id)
    
    def save(self, *args, **kwargs):
        if not self.collection.allowed_models.filter(pk=self.content_type.pk).count():
            raise CollectionException("Adding an item of non-allowed type to the collection")
        if self.importance is None:
            max_importance = self.collection.relation_set.aggregate(models.Max('importance'))['importance__max']
            if max_importance is None:
                self.importance = 0
            else:
                self.importance = max_importance + 1
        return super(self.__class__, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return u"<%s> for <%s>" % (self.content_type.model_class().objects.get(pk=self.object_id), self.collection)
        
    class Meta:
        unique_together = (("content_type", "object_id", "collection",), )
        
@post_save_handler(User)
def _create_default_collection(sender, instance, created, **kwargs):
    """
    Handler for the signal
    Create a default collection for the newly-created user
    x instance - user instance
    """
    if created:
        name = instance.first_name if instance.first_name else instance.username
        Collection.objects.create(owner=instance, title=settings.DEFAULT_COLLECTION_NAME % name, default=True)
    
class CollectionException(Exception):
    pass