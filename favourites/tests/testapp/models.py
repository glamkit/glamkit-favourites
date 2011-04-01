from django.db import models
from django.core.urlresolvers import reverse

from ixc_common.decorators import create_basic_admin

@create_basic_admin
class Painting(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='uploads/painting')
    
    def get_absolute_url(self):
        return reverse("myapp.painting_details", args=[self.id])
    
    def __unicode__(self):
        return u"'%s'" % self.title
    
@create_basic_admin
class Book(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='uploads/book')
    
    def get_absolute_url(self):
        return reverse("myapp.book_details", args=[self.id])
    
    def __unicode__(self):
        return u"'%s'" % self.title
        
    
# can't be added to favourites
class Movie(models.Model):
    title = models.CharField(max_length=200)