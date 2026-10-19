from django.db.models import F
from django.shortcuts import get_object_or_404, render

from .models import Book


def book_list(request):
    books = Book.objects.all()
    return render(request, "books/book_list.html", {"books": books})


def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    Book.objects.filter(pk=pk).update(likes=F("likes") + 1)
    book.refresh_from_db()
    return render(request, "books/book_detail.html", {"book": book})
