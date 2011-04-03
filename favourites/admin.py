from models import FavouritesList
from django.contrib import admin

class FavouritesListAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'owners_display', 'created', 'is_public')
    list_filter = ('is_public',)
    list_select_related = True
    raw_id_fields = ('creator', 'owners', 'viewers', 'editors',)
    search_fields = ('title', 'owners__username', )
    readonly_fields = ('created', 'modified')
    ordering = ('-created', )
    
admin.site.register(FavouritesList, FavouritesListAdmin)
