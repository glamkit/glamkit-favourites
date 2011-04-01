from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

from favourites.models import _create_default_collection
        
class Command(NoArgsCommand):
    help = """
    Create default collections (if they do not exist yet) for all users
    
    Useful when attaching the favourites application to the already existing project
    """

    def handle_noargs(self, **options):
        for user in User.objects.all():
            if not user.collection_set.count():
                _create_default_collection(None, user, True)