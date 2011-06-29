import datetime
import re
from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.urlresolvers import reverse

from convenient.decorators import post_save_handler
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
    def create_from_item(self, item, creator, **kwargs):
        """
        Create a new collection from an item.
        kwargs correspond to parameters of FavouritesList

        item has to be a model instance

        @throws: FavouritesListException
        """

        c = self.model.objects.create(creator=creator, **kwargs)
        c.add_item(item, added_by=creator)
        return c

    def containing_item(self, item):
        """
        @returns: QS of collections containing the given item
        """
        collections = self.model.items.related.model.objects.filter(content_type=ContentType.objects.get_for_model(item), object_id=item.pk).values_list(('collection'), flat=True)
        return self.filter(id__in=collections)

    def containing_item_and_visible_to(self, item, user):
        """
        @returns: QS of lists containing the given item and visible to a given user
        """
        collections = self.model.items.related.model.objects.filter(content_type=ContentType.objects.get_for_model(item), object_id=item.pk).values_list(('collection'), flat=True)
        return self.visible_to(user).filter(id__in=collections)

    def owned_by(self, user):
        """
        Returns lists owned by a given user
        """
        if user.is_anonymous():
            return self.none()

        return self.filter(owners=user)

    def edited_by(self, user):
        """
        Returns lists edited by a given user
        """
        if user.is_anonymous():
            return self.none()

        return self.filter(editors=user)

    def visible_to(self, user):
        """
        Visible if:
        * I am an owner
        * I am an editor
        * I am a viewer
        * The list is public
        * I have change permission in admin.
        """
        if user.is_anonymous():
            return self.filter(is_public = True)

        if user.has_perm('favourites.change_favouriteslist'):
            return self.all()

        return self.filter(owners=user) | self.filter(editors=user) | self.filter(viewers=user) | self.filter(is_public = True)

    def owned_by_visible_to(self, owner, current_user):
        return self.owned_by(owner) & self.visible_to(current_user)

    def edited_by_visible_to(self, owner, current_user):
        return self.edited_by(owner) & self.visible_to(current_user)

    def editable_by_visible_to(self, owner, current_user):
        editable_qs = (self.owned_by(owner) | self.edited_by(owner))
        return self.visible_to(current_user).filter(id__in=[x.id for x in editable_qs])

class FavouritesList(models.Model):
    created = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    modified = models.DateTimeField(db_index=True)

    title = models.CharField(max_length=200, db_index=True)
    description = models.TextField(blank=True, null=True)

    is_public = models.BooleanField(default=False, db_index=True)

    creator = models.ForeignKey(User) #who created this list?
    owners = models.ManyToManyField(User, blank=True, related_name="owned_lists") #users who can delete this list. always contains creator.
    editors = models.ManyToManyField(User, blank=True, related_name="editable_lists") #users who can edit (but not delete) this list
    viewers = models.ManyToManyField(User, blank=True, related_name="viewable_lists") #users who can view this list (overridden by owners, editors and is_public = true)

    objects = FavouritesListManager()

    @staticmethod
    def get_permissions_on_lists_owned_by(owner, user):
        return {
            'can_add_list': FavouritesList.can_user_add_list_for_other_user(user=user, other_user=owner),
        }

    @staticmethod
    def can_user_add_list_for_other_user(user, other_user):
        """
        Yes if:
        * I am the other user
        * I have add permission in admin
        """
        if user.is_anonymous():
            return False

        return user == other_user or \
            user.has_perm("favourites.add_favouriteslist")

    def get_permissions_for_user(self, user):
        return {
            'can_view': self.can_user_view(user),
            'can_edit': self.can_user_edit(user),
            'can_delete': self.can_user_delete(user),
            'can_add_item': self.can_user_add_item(user),
            'can_delete_any_item': self.can_user_delete_any_item(user),
        }

    def can_user_view(self, user):
        """
        Yes if:
        * I am an owner
        * I am an editor
        * I am a viewer
        * The list is public
        * I have change permission in admin.
        """
        if user.is_anonymous():
            return self.is_public

        return \
            user in self.owners.all() or \
            user in self.editors.all() or \
            user in self.viewers.all() or \
            user.has_perm("favourites.change_favouriteslist")

    def can_user_edit(self, user):
        """
        Yes if:
        * I am an owner
        * I am an editor
        * I have change permission in admin
        """
        return \
            user in self.owners.all() or \
            user in self.editors.all() or \
            user.has_perm("favourites.change_favouriteslist")

    def can_user_delete(self, user):
        """
        Yes if:
        * I am an owner
        * I have delete permission in admin
        """
        return \
            user in self.owners.all() or \
            user.has_perm("favourites.delete_favouriteslist")

    def can_user_add_item(self, user):
        """
        Yes if:
        * I am an owner
        * I am an editor
        * I have change permission in admin
        * I have add item permission in admin
        """
        return \
            self.can_user_edit(user) or \
            user.has_perm("favourites.add_favouriteitem")

    def can_user_delete_any_item(self, user):
        """
        Yes if:
        * I am an owner
        * I have change permission in admin
        * I have delete item permission in admin
        """
        return \
            user in self.owners.all() or \
            user.has_perm("favourites.change_favouriteslist") or \
            user.has_perm("favourites.delete_favouriteitem")

    def owners_display(self):
        return ", ".join([unicode(x) for x in self.owners.all()])
    owners_display.short_description = "owners"

    def _new_collection_name(self):
        """
        Return a name that is '1 more' than the most recently generated name.
        """
        creator = self.creator
        name = creator.first_name if creator.first_name else creator.username
        orig_title = settings.NEW_FAVOURITES_LIST_NAME % {'user': name}
        try:
            newest_similar_title = type(self).objects.filter(creator=self.creator, title__startswith=orig_title)[0].title
        except IndexError:
            return orig_title

        PATTERN = re.compile(r'^.* (\d+)$')
        match = re.match(PATTERN, newest_similar_title)
        if match:
            number = int(match.groups()[0]) + 1
        else:
            number = 1
        return "%s %s" % (orig_title, number)

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self._new_collection_name()
        self.modified = datetime.datetime.now()

        super(FavouritesList, self).save(*args, **kwargs)

        #check owners contains creator
        if self.creator not in self.owners.all():
            self.owners.add(self.creator)

    def delete(self, *args, **kwargs):
        # at all times there needs to be at least one collection for all creators
        creator = self.creator
        r = super(FavouritesList, self).delete(*args, **kwargs)

        count = creator.owned_lists.count()
        if count == 0:
            _create_default_collection(instance=creator, created=True, sender=None)
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

    def count(self):
        return self._get_qs().count()

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
        self.save() #update modified time (even if object already exists)
        if item in self:
            return
        FavouriteItem.objects.create(collection=self, content_type=ContentType.objects.get_for_model(item), object_id=item.pk, **kwargs)

    def remove_item(self, item):
        """
        Remove an item from the collection

        @throws: FavouritesListException (item is not in the collection)
        """
        try:
            self._get_item(item).delete()
            self.save() #update modified time
        except FavouriteItem.DoesNotExist:
            raise FavouritesListException("Trying to delete an item not in the collection")

    def get_absolute_url(self):
        return reverse('favourites.list', args=[self.id, ])

    class Meta:
        unique_together = ()
        ordering = ["-modified"]

class FavouriteItem(models.Model):
    collection = models.ForeignKey(FavouritesList, editable=False, related_name="items")

    added_by = models.ForeignKey(User) #useful for multi-party lists

    created = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    description = models.TextField(blank=True, null=True)

    content_type = models.ForeignKey(ContentType, editable=False)
    object_id = models.CharField(max_length=255, editable=False)
    item = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return u"<%s> for <%s>" % (self.item, self.collection)

    class Meta:
        unique_together = (("content_type", "object_id", "collection",), )
        ordering = ["-created"]

    def can_user_delete(self, user):
        """
        Yes, if:
        * I added this item
        * I can delete any items from the list (which includes admin permissions)
        """
        return user == self.added_by or \
            self.collection.can_user_delete_any_item(user)

    def can_user_edit(self, user):
        """
        Yes, if:
        * I added this item
        * I have the permission in admin.
        """
        return user == self.added_by or \
            user.has_perm('favourites.change_favouriteitem', self)


@post_save_handler(User)
def _create_default_collection(sender, instance, created, **kwargs):
    """
    Handler for the signal
    Create a default collection for the newly-created user
    x instance - user instance
    """
    creator = instance
    if created:
        userstring = creator.first_name if creator.first_name else creator.username
        l = FavouritesList.objects.create(creator = creator, title=settings.DEFAULT_FAVOURITES_LIST_NAME % {'user': userstring })

class FavouritesListException(Exception):
    pass
