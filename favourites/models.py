import datetime

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.urlresolvers import reverse

from ixc_common.decorators import post_save_handler
from ixc_common import testing
from django.contrib.contenttypes import generic


"""
Preferably all calls to the favouriting system
should be done through the API provided by the
FavouritesList class

It is also preferable to use high-level API
(FavouritesList.add_item, FavouritesList.remove_item, item in FavouritesList,
for item in FavouritesList, etc.)

"""
 
class FavouritesListManager(models.Manager):
    def create_from_item_id(self, content_type_id, object_id, **kwargs):
        item = ContentType.objects.get_for_id(content_type_id).model_class().objects.get(id=object_id)
        return self.create_from_item(item, **kwargs)
    
    def create_from_item(self, item, **kwargs):
        """
        Create a new collection from an item.
        kwargs correspond to parameters of FavouritesList
        
        item has to be a model instance
        
        @throws: FavouritesListException
        """
        
        c = self.model.objects.create(**kwargs)
        c.add_item(item)
        return c
        
    def containing(self, item):
        """
        @returns: QS of collections containing the given item
        """
        
        return self.model.objects.filter(favouriteitem__content_type=ContentType.objects.get_for_model(item), favouriteitem__object_id=item.pk)
        
    def owned_by(self, user):
        """
        @returns: QS of collections owned by the given user
        """
        return self.model.objects.filter(owner=user)
        
class FavouritesList(models.Model):
    """    
    # Setting settings first:
    >>> testing.load_dummy_app('favourites.tests.myapp')
    >>> from myapp.models import Book, Painting, Movie
    >>> favouritable_models.model_list = [Book, Painting]
    
    >>> u = User.objects.create(username='test')
    >>> c = FavouritesList.objects.create(owner=u, description='book collection')
    >>> book = Book.objects.create(title='awesome book')
    'add_item' is a syntax sugar for adding items to the collection
    It is the same as FavouriteItem.objects.create(collection=c, ...etc)
    >>> c.add_item(book)
    >>> painting = Painting.objects.create(title='awesome painting')
    >>> c.add_item(painting)
    Traceback (most recent call last):
        ...
    FavouritesListException: Adding an item of non-allowed type to the collection
    
    # FavouritesList manager has some syntactic sugar methods
    >>> treasure_island = Book.objects.create(title='Treasure island')
    >>> c = FavouritesList.objects.create_from(owner=u, item=treasure_island, description='awesome collection')
    >>> c.items.all()
    [<<Book: 'Treasure island'> for <FavouritesList: 'awesome collection'>>]
    
    # Custom manager method to get all collections containing a particular item
    >>> qs = FavouritesList.objects.containing(empire_v)
    >>> len(qs) == 1 and qs[0] == c1
    True
    
    # FavouritesList class defines custom __iter__ and __contains__ methods
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
    >>> c3 = FavouritesList.objects.create_from(empire_v, owner=u1)
    >>> times_favourited(empire_v)
    2
    >>> sorted([u.username for u in users_favourited(empire_v)])
    ['cheshire', 'test']
    >>> testing.cleanup()
    """
    
    is_public = models.BooleanField(default=False)
    
    created = models.DateTimeField(default=datetime.datetime.now, editable=False)
   
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    owner = models.ForeignKey(User, editable=False)
        
    objects = FavouritesListManager()
    
    def _new_collection_name(self):
        name = self.owner.first_name if self.owner.first_name else self.owner.username
        return settings.NEW_FAVOURITES_LIST_NAME % {'user': name}
    
    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self._new_collection_name()
        super(self.__class__, self).save(*args, **kwargs)
                
    def delete(self, *args, **kwargs):
        # at all times there needs to be at least one collection
        owner = self.owner
        r = super(self.__class__, self).delete(*args, **kwargs)
        count = owner.favouriteslist_set.count()
        if count == 0:
            _create_default_collection(instance=self.owner, created=True, sender=None)
        return r
    
    def __contains__(self, item):
        try:
            self.items.get(content_type=ContentType.objects.get_for_model(item), object_id=item.pk)
        except FavouriteItem.DoesNotExist:
            return False
        else:
            return True
        
    def _get_qs(self):
        """
        Get the queryset of items
        """
        return self.items.all()
        
    def __iter__(self):
        for item in self._get_qs():
            yield item
    
    def __getitem__(self, i):
        item = self._get_qs()[i]
        if isinstance(item, FavouriteItem): # collection[3]
            return item
        
        # collection[:12]
        return self._get_qs()
            
    def __unicode__(self):
        return self.title
    
    def _get_item(self, item):
        """
        Tries to get an item FavouriteItem instance, assuming the item is in 
        this collection
        
        @throws: FavouriteItem.DoesNotExist
        """
        return FavouriteItem.objects.get(collection=self, content_type=ContentType.objects.get_for_model(item), object_id=item.pk)
    
    def add_item(self, item, **kwargs):
        """
        Add an Item to the collection
        kwargs correspond to the optional fields in FavouriteItem
        
        @throws: FavouritesListException (item is of an inappropriate type)
        """
        if item in self:
            return
        FavouriteItem.objects.create(collection=self, content_type=ContentType.objects.get_for_model(item), object_id=item.pk, **kwargs)
        
    def add_item_id(self, content_type_id, object_id, **kwargs):
        item = ContentType.objects.get_for_id(content_type_id).model_class().objects.get(id=object_id)
        return self.add_item(item, **kwargs)

    def remove_item(self, item):
        """
        Remove an item from the collection
        
        @throws: FavouritesListException (item is not in the collection)
        """
        try:
            self._get_item(item).delete()
        except FavouriteItem.DoesNotExist:
            raise FavouritesListException("Trying to delete an item not in the collection")
            
    def get_absolute_url(self):
        return reverse('favourites.list', args=(self.owner.username, self.id))
        
    class Meta:
        unique_together = ()
        ordering = ["-created"]      
    
class FavouriteItem(models.Model):
    collection = models.ForeignKey(FavouritesList, editable=False, related_name="items")
    
    order = models.FloatField(editable=False, default = 0, db_index=True) # items with smaller order go first
    created = models.DateTimeField(default=datetime.datetime.now, editable=False, db_index=True)
    description = models.TextField(blank=True, null=True)
    
    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.CharField(max_length=255, editable=False)
    item = generic.GenericForeignKey('content_type', 'object_id')
        
    def __unicode__(self):
        return u"<%s> for <%s>" % (self.item, self.collection)
        
    class Meta:
        unique_together = (("content_type", "object_id", "collection",), )
        ordering = ["order"]
        
@post_save_handler(User)
def _create_default_collection(sender, instance, created, **kwargs):
    """
    Handler for the signal
    Create a default collection for the newly-created user
    x instance - user instance
    """
    if created:
        user = instance.first_name if instance.first_name else instance.username
        FavouritesList.objects.create(owner=instance, title=settings.DEFAULT_FAVOURITES_LIST_NAME % {'user': user })
    
class FavouritesListException(Exception):
    pass