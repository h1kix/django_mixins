from django.test import TestCase
from django.urls import reverse

from .models import Movie, Rating
from .services import MediaFactory
from .forms import MediaForm


class MovieModelTests(TestCase):
	def test_create_movie_and_methods(self):
		movie = Movie.objects.create(
			title='Test Movie',
			creator='Some Studio',
			publication_date='2020-01-01',
			duration=120,
			format='mp4',
			director='Jane Doe',
			genre='drama'
		)

		self.assertEqual(movie.get_description(), "Фильм 'Test Movie' режиссера Jane Doe, 120 мин.")
		self.assertEqual(movie.play_trailer(), "Воспроизведение трейлера фильма 'Test Movie'")
		# DownloadableMixin
		self.assertIn('Скачивание', movie.download())
		# StreamableMixin
		self.assertIn('Начинается потоковая', movie.stream())


class MediaFactoryTests(TestCase):
	def test_factory_creates_movie(self):
		movie = MediaFactory.create_media('movie',
										 title='Factory Movie',
										 creator='Studio',
										 publication_date='2021-01-01',
										 duration=90,
										 format='mkv',
										 director='Dir',
										 genre='comedy')
		self.assertIsInstance(movie, Movie)


class MediaFormTests(TestCase):
	def test_movie_form_validation_and_save(self):
		data = {
			'media_type': 'movie',
			'title': 'Form Movie',
			'creator': 'Creator',
			'publication_date': '2022-02-02',
			'duration': 95,
			'format': 'mp4',
			'director': 'Director Name',
			'genre': 'drama'
		}
		form = MediaForm(data)
		self.assertTrue(form.is_valid())
		obj = form.save()
		self.assertIsInstance(obj, Movie)


class RatingsAndFilteringTests(TestCase):
	def test_ratings_and_average(self):
		movie = Movie.objects.create(
			title='Rated Movie',
			creator='Creator',
			publication_date='2022-01-01',
			duration=100,
			format='mp4',
			director='Dir',
			genre='action'
		)
		Rating.objects.create(movie=movie, rating=4)
		Rating.objects.create(movie=movie, rating=5)
		self.assertEqual(movie.get_average_rating(), 4.5)

	def test_list_filtering_by_genre_and_director(self):
		Movie.objects.create(title='M1', creator='C', publication_date='2020-01-01', duration=90, format='mp4', director='A', genre='drama')
		Movie.objects.create(title='M2', creator='C', publication_date='2020-01-01', duration=90, format='mp4', director='B', genre='comedy')
		url = reverse('media_library:media_list')
		resp = self.client.get(url, {'genre': 'drama'})
		self.assertEqual(resp.status_code, 200)
		movies = resp.context['movies']
		self.assertEqual(len(movies), 1)
		self.assertEqual(movies[0].title, 'M1')
