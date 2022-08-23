from django.forms import ModelForm
from catalog.models import BookInstance, Book, Author
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import datetime

class RenewBookModelForm(ModelForm):
    def clean_due_back(self):
       data = self.cleaned_data['due_back']

       if data < datetime.date.today():
           raise ValidationError(_('Invalid date - renewal in past'))

       if data > datetime.date.today() + datetime.timedelta(weeks=4):
           raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

       return data

    class Meta:
        model = BookInstance
        fields = ['due_back']
        labels = {'due_back': _('Renewal date')}
        help_texts = {'due_back': _('Enter a date between now and 4 weeks (default 3).')}

class SearchBookModelForm(ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'genre', 'language']

class SearchAuthorModelForm(ModelForm):
    class Meta:
        model = Author
        fields = ['first_name', 'last_name']
