# forms.py
from django import forms
from .services import MediaFactory
from .models import Movie


class MediaForm(forms.Form):
    MEDIA_TYPES = [
        ('book', 'Книга'),
        ('movie', 'Фильм'),
        ('audiobook', 'Аудиокнига'),
    ]

    media_type = forms.ChoiceField(choices=MEDIA_TYPES, label='Тип медиа')
    title = forms.CharField(max_length=200, label='Название')
    creator = forms.CharField(max_length=100, label='Автор/Режиссер')
    publication_date = forms.DateField(
        label='Дата публикации',
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d']
    )

    # Поля для книг
    isbn = forms.CharField(max_length=20, required=False, label='ISBN')
    page_count = forms.IntegerField(required=False, label='Количество страниц', min_value=1)

    # Поля для аудиокниг и фильмов (общая длительность)
    narrator = forms.CharField(max_length=100, required=False, label='Чтец')
    duration = forms.IntegerField(required=False, label='Длительность (минуты)', min_value=1)

    # Поля для фильмов
    format = forms.CharField(max_length=10, required=False, label='Формат')
    director = forms.CharField(max_length=100, required=False, label='Режиссер')
    genre = forms.ChoiceField(choices=Movie.GENRE_CHOICES, required=False, label='Жанр')

    def __init__(self, *args, **kwargs):
        kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        media_type = cleaned_data.get('media_type')

        # Валидация в зависимости от типа медиа
        if media_type == 'book':
            if not cleaned_data.get('isbn'):
                self.add_error('isbn', 'ISBN обязателен для книг')
            if not cleaned_data.get('page_count'):
                self.add_error('page_count', 'Количество страниц обязательно для книг')

        elif media_type == 'audiobook':
            if not cleaned_data.get('narrator'):
                self.add_error('narrator', 'Чтец обязателен для аудиокниг')
            if not cleaned_data.get('duration'):
                self.add_error('duration', 'Длительность обязательна для аудиокниг')

        elif media_type == 'movie':
            if not cleaned_data.get('duration'):
                self.add_error('duration', 'Длительность обязательна для фильма')
            if not cleaned_data.get('format'):
                self.add_error('format', 'Формат обязателен для фильма')
            if not cleaned_data.get('director'):
                self.add_error('director', 'Режиссер обязателен для фильма')
            # Жанр необязателен, но если указан, проверим совпадение
            if cleaned_data.get('genre') and cleaned_data.get('genre') not in dict(Movie.GENRE_CHOICES):
                self.add_error('genre', 'Неверный жанр')

        return cleaned_data

    def save(self):
        media_type = self.cleaned_data['media_type']

        # Подготавливаем данные для фабрики
        media_data = {
            'title': self.cleaned_data['title'],
            'creator': self.cleaned_data['creator'],
            'publication_date': self.cleaned_data['publication_date'],
        }

        # Добавляем специфичные поля для каждого типа
        if media_type == 'book':
            media_data.update({
                'isbn': self.cleaned_data['isbn'],
                'page_count': self.cleaned_data['page_count']
            })
        elif media_type == 'audiobook':
            media_data.update({
                'duration': self.cleaned_data['duration'],
                'narrator': self.cleaned_data['narrator']
            })
        elif media_type == 'movie':
            media_data.update({
                'duration': self.cleaned_data['duration'],
                'format': self.cleaned_data['format'],
                'director': self.cleaned_data['director'],
                'genre': self.cleaned_data.get('genre', ''),
            })

        # Используем фабрику для создания объекта
        return MediaFactory.create_media(media_type, **media_data)