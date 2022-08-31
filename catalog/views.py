from mimetypes import init
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Book, Author, BookInstance, Genre
from catalog.forms import RenewBookModelForm, SearchBookModelForm, SearchAuthorModelForm, RentBookModelForm
import datetime

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_books = Book.objects.count()
    num_instances = BookInstance.objects.count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()
    num_visits = request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits + 1

    context = {
        'num_books': num_books,
        'num_instances': num_instances,
        'num_instances_available': num_instances_available,
        'num_authors': num_authors,
        'num_visits': num_visits,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book
    
    def get_context_data(self, **kwargs):
        context = super(BookDetailView, self).get_context_data(**kwargs)
        context['genre_all'] = self.object.genre.all
        context['instance_all'] = self.object.bookinstance_set.all
        return context

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10


class AuthorDetailView(generic.DetailView):
    model = Author
    
    def get_context_data(self, **kwargs):
        context = super(AuthorDetailView, self).get_context_data(**kwargs)
        
        context['bookset_all'] = self.object.book_set.all
        return context

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user, status__exact='o').order_by('due_back')

class LoanedBooksAllListView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    permission_required = 'catalog.can_mark_returned'
    template_name = 'catalog/bookinstance_list_borrowed_all.html'
    paginate_by = 10

    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)
def renew_book_librarian(request, pk):
    """View function for renewing a specific BookInstance by librarian."""
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookModelForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['due_back']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookModelForm(initial={'due_back': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_renew_librarian.html', context)

def search_book(request):
    
    context = {}
    
    if request.method == 'POST':
        print('a')
        form = SearchBookModelForm(request.POST)
        if form.is_valid():
            context['book_list'] = Book.objects.filter(title__icontains=form.cleaned_data['title'],
                                                       author__exact=form.cleaned_data['author'],
                                                       genre__in=form.cleaned_data['genre'],
                                                       language__exact=form.cleaned_data['language']
                                                       )
            return render(request, 'catalog/book_list.html', context)

    else:
        form = SearchBookModelForm()

    context = {
        'search_item': 'Book',
        'form': form,
    }

    return render(request, 'catalog/search.html', context)

def search_author(request):
    
    context = {}
    
    if request.method == 'POST':
        form = SearchAuthorModelForm(request.POST)
        if form.is_valid():
            context['author_list'] = Author.objects.filter(first_name__icontains=form.cleaned_data['first_name'],
                                                           last_name__icontains=form.cleaned_data['last_name'],
                                                           )
            return render(request, 'catalog/author_list.html', context)

    else:
        form = SearchAuthorModelForm()

    context = {
        'search_item': 'Author',
        'form': form,
    }

    return render(request, 'catalog/search.html', context)

@login_required
def rentBook(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RentBookModelForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['due_back']
            book_instance.borrower = request.user
            book_instance.status = 'o'
            book_instance.save()

            return HttpResponseRedirect(reverse('my-borrowed'))

    else:
        proposed_rent_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RentBookModelForm(initial={'due_back': proposed_rent_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'catalog/book_rent.html', context)

@login_required
def returnBook(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)
    book_instance.due_back = None
    book_instance.borrower = None
    book_instance.status = 'a'
    book_instance.save()

    return HttpResponseRedirect(reverse('my-borrowed'))
    
class AuthorCreate(CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    permission_required = 'catalog.can_mark_returned'
    
    def get_context_data(self, **kwargs):
        context = super(AuthorCreate, self).get_context_data(**kwargs)
        context['title'] = 'Add Author'
        return context

class AuthorUpdate(UpdateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    date_of_death = datetime.date.today()
    initial = {'date_of_death': date_of_death}
    permission_required = 'catalog.can_mark_returned'
    
    def get_context_data(self, **kwargs):
        context = super(AuthorUpdate, self).get_context_data(**kwargs)
        context['title'] = 'Update Author info'
        return context

class AuthorDelete(DeleteView):
    model = Author
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.can_mark_returned'

class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'
    
    def get_context_data(self, **kwargs):
        context = super(BookCreate, self).get_context_data(**kwargs)
        context['title'] = 'Add Book'
        return context

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    permission_required = 'catalog.can_mark_returned'
    
    def get_context_data(self, **kwargs):
        context = super(BookUpdate, self).get_context_data(**kwargs)
        context['title'] = 'Update Book info'
        return context

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    success_url = reverse_lazy('books')
    permission_required = 'catalog.can_mark_returned'
