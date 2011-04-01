import unittest
from string import digits

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from ixc_common import testing

from favourites.models import Collection

class FavouritesTest(unittest.TestCase):
    def setUp(self):
        testing.load_dummy_app('favourites.tests.testapp')
        from testapp.models import Painting, Book
        
        u1 = User.objects.create(username='user1')
        u2 = User.objects.create(username='user2')
        u3 = User.objects.create(username='user3')
        
        for i in range(1, 10):
            exec 'p%s = Painting.objects.create(title="Painting %s")' % (i, i)
            exec 'b%s = Book.objects.create(title="Book %s")' % (i, i)
        
        book_type = ContentType.objects.get(app_label='myapp', model='book')
        painting_type = ContentType.objects.get(app_label='myapp', model='painting')
        
        cmr = CollectionModelRelation
        
        
        c1 = Collection.objects.create(owner=u1)
        cmr.objects.create(collection=c1, content_type=book_type)
        cmr.objects.create(collection=c1, content_type=painting_type)

        c1.add_item(b2)
        c1.add_item(b4)
        c1.add_item(b6)
        
        c2 = Collection.objects.create(owner=u2)
        c2.allowed_models = [painting_type]
        c2.add_item(p1)
        c2.add_item(p3)
        c2.add_item(p5)
        
        c3 = Collection.objects.create(owner=u3)
        c3.allowed_models = [book_type, painting_type]
        c3.add_item(p1)
        c3.add_item(b2)
        c3.add_item(p7)
        c3.add_item(b9)
        
        for var_name, var in locals().items():
            if len(var_name) == 2 and var_name[0] in ('u', 'p', 'b', 'c',) and var_name[1] in digits:
                setattr(self, var_name, var)
        
        self.ae = self.assertEquals
        
        
    def tearDown(self):
        Painting.objects.all().delete()
        Book.objects.all().delete()
        User.objects.all().delete()
        testing.cleanup()

    def testBasic(self):
        pass