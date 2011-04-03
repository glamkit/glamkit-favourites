from django import forms

from favourites.models import FavouritesList, FavouriteItem

class FavouritesListForm(forms.ModelForm):
    def as_ul(self):
        return u"<ul>" + super(FavouritesListForm, self).as_ul() + u"</ul>"
    
    class Meta:
        model = FavouritesList
        fields = ['title', 'description', 'is_public']

class FavouriteItemForm(forms.ModelForm):
    def as_ul(self):
        return u"<ul>" + super(FavouriteItemForm, self).as_ul() + u"</ul>"
    
    class Meta:
        model = FavouriteItem