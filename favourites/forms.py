from django import forms

from favourites.models import Collection, Relation

class CollectionForm(forms.ModelForm):
    def as_ul(self):
        return u"<ul>" + super(CollectionForm, self).as_ul() + u"</ul>"
    
    class Meta:
        model = Collection
        fields = ['title', 'description', 'is_public']

class RelationForm(forms.ModelForm):
    def as_ul(self):
        return u"<ul>" + super(RelationForm, self).as_ul() + u"</ul>"
    
    class Meta:
        model = Relation