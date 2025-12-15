from django.db import models

# Create your models here.

from django.db import models

from media.mixins import BorrowableMixin, DownloadableMixin, StreamableMixin, ReviewableMixin
from django.db.models import Avg


# Предопределенные жанры для Movie
GENRE_CHOICES = [
    ('drama', 'Драма'),
    ('comedy', 'Комедия'),
    ('action', 'Боевик'),
    ('documentary', 'Документальный'),
    ('thriller', 'Триллер'),
]


class MediaItem(models.Model):
    title = models.CharField(max_length=200)
    creator = models.CharField(max_length=100)
    publication_date = models.DateField()
    _internal_id = models.CharField(max_length=50, blank=True)  # инкапсуляция

    class Meta:
        abstract = True

    def get_description(self):
        raise NotImplementedError("Метод должен быть переопределен в дочерних классах")

    def _generate_internal_id(self):
        return f"MEDIA_{self.title[:5].upper()}"



class Book(BorrowableMixin, MediaItem):
    isbn = models.CharField(max_length=20)
    page_count = models.IntegerField()
    is_borrowed = models.BooleanField(default=False)
    borrowed_by = models.CharField(max_length=100, blank=True)

    def get_description(self):
        return f"Книга '{self.title}' автора {self.creator}, {self.page_count} стр."

    def read_sample(self):
        return f"Чтение отрывка из книги '{self.title}'"

    def get_media_type(self):
        return "book"

class Movie(DownloadableMixin, StreamableMixin, ReviewableMixin, MediaItem):
    GENRE_CHOICES = GENRE_CHOICES
    duration = models.IntegerField()
    format = models.CharField(max_length=10)
    director = models.CharField(max_length=100, blank=True)
    genre = models.CharField(max_length=20, choices=GENRE_CHOICES, blank=True)

    def get_description(self):  # полиморфизм
        director = self.director or self.creator
        return f"Фильм '{self.title}' режиссера {director}, {self.duration} мин."

    def play_trailer(self):
        return f"Воспроизведение трейлера фильма '{self.title}'"

    def get_media_type(self):
        return "movie"

    def get_average_rating(self):
        agg = self.ratings.aggregate(avg=Avg('rating'))
        return agg['avg']

class AudioBook(DownloadableMixin, BorrowableMixin, MediaItem):
    duration = models.IntegerField()
    narrator = models.CharField(max_length=100)
    is_borrowed = models.BooleanField(default=False)
    borrowed_by = models.CharField(max_length=100, blank=True)

    def get_description(self):
        return f"Аудиокнига '{self.title}', читает {self.narrator}"

    def get_media_type(self):
        return "audiobook"


class Rating(models.Model):
    movie = models.ForeignKey(Movie, related_name='ratings', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.movie.title} - {self.rating}"