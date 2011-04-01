from ixc_common.decorators import render_to, resolve_or_404

from models import Book, Painting

@render_to("myapp/book.html")
@resolve_or_404(Book, pk_arg="book_id", instance_arg="book")
def book_details(request, book):
    return locals()

@render_to("myapp/painting.html")
@resolve_or_404(Painting, pk_arg="painting_id", instance_arg="painting")
def painting_details(request, painting):
    return locals()
    
@render_to("myapp/book_list.html")
def book_list(request):
    return {"book_list": Book.objects.all()}

@render_to("myapp/painting_list.html")
def painting_list(request):
    return {"painting_list": Painting.objects.all()}