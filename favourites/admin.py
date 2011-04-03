from models import FavouritesList
from django.contrib import admin

class FavouritesListAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created', 'is_public')
    list_filter = ('is_public',)
    list_select_related = True
    readonly_fields = ('owner',)
    search_fields = ('title', 'owner__username', )
    ordering = ('created',)
admin.site.register(FavouritesList, FavouritesListAdmin)
