# views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView, TemplateView

from .forms import MediaForm
from .models import Book, AudioBook, Movie
from .services import MediaFactory
from django.views.decorators.http import require_POST
from django.contrib import messages


class MediaListView(ListView):
    template_name = 'media_library/media_list.html'
    context_object_name = 'media_items'

    def get_queryset(self):
        books = list(Book.objects.all())
        audiobooks = list(AudioBook.objects.all())
        movies_qs = Movie.objects.all()

        # Фильтрация по параметрам запроса (по названию, жанру, режиссеру)
        q = self.request.GET.get('q')
        genre = self.request.GET.get('genre')
        director = self.request.GET.get('director')

        if q:
            movies_qs = movies_qs.filter(title__icontains=q)
        if genre:
            movies_qs = movies_qs.filter(genre=genre)
        if director:
            movies_qs = movies_qs.filter(director__icontains=director)

        movies = list(movies_qs)
        return books + movies + audiobooks

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Группируем по типам для отображения
        context['books'] = Book.objects.all()
        # Применим ту же фильтрацию, что и в get_queryset для показа фильтрованных фильмов
        movies_qs = Movie.objects.all()
        q = self.request.GET.get('q')
        genre = self.request.GET.get('genre')
        director = self.request.GET.get('director')
        if q:
            movies_qs = movies_qs.filter(title__icontains=q)
        if genre:
            movies_qs = movies_qs.filter(genre=genre)
        if director:
            movies_qs = movies_qs.filter(director__icontains=director)

        context['movies'] = movies_qs
        context['audiobooks'] = AudioBook.objects.all()
        context['genres'] = Movie.GENRE_CHOICES
        return context


class MediaDetailView(DetailView):
    template_name = 'media_library/media_detail.html'
    context_object_name = 'media_item'

    def get_object(self):
        pk = self.kwargs.get('pk')
        media_type = self.kwargs.get('media_type')
        # Если тип указан в URL, используем его напрямую
        if media_type:
            media_class = MediaFactory.get_media_class(media_type)
            if not media_class:
                raise Book.DoesNotExist("Media item not found")
            try:
                return media_class.objects.get(pk=pk)
            except media_class.DoesNotExist:
                raise media_class.DoesNotExist("Media item not found")

        # Фоллбек: пробуем найти по всем типам (устаревший путь)
        for media_type in MediaFactory.get_all_media_types():
            media_class = MediaFactory.get_media_class(media_type)
            try:
                return media_class.objects.get(pk=pk)
            except media_class.DoesNotExist:
                continue
        raise Book.DoesNotExist("Media item not found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        media_item = self.object

        # Определяем доступные действия на основе типа объекта и миксинов
        context['available_actions'] = self.get_available_actions(media_item)
        context['media_type'] = self.get_media_type(media_item)

        # Рейтинги и отзывы — подготовим в контексте, т.к. шаблон не вызывает методы
        if hasattr(media_item, 'get_average_rating') and callable(getattr(media_item, 'get_average_rating')):
            context['avg_rating'] = media_item.get_average_rating()
        else:
            context['avg_rating'] = None

        if hasattr(media_item, 'get_reviews') and callable(getattr(media_item, 'get_reviews')):
            try:
                context['reviews'] = list(media_item.get_reviews())
            except Exception:
                context['reviews'] = []
        else:
            context['reviews'] = []

        context['can_add_review'] = hasattr(media_item, 'add_review') and callable(getattr(media_item, 'add_review', None))

        return context

    def get_available_actions(self, media_item):
        actions = []

        # Базовые действия
        actions.append(('describe', 'Описание', 'btn-primary'))

        # Действия в зависимости от типа и миксинов
        if hasattr(media_item, 'read_sample'):
            actions.append(('read', 'Читать отрывок', 'btn-info'))

        if hasattr(media_item, 'play_trailer'):
            actions.append(('play_trailer', 'Смотреть трейлер', 'btn-warning'))

        if hasattr(media_item, 'stream'):
            actions.append(('stream', 'Смотреть онлайн', 'btn-dark'))

        if hasattr(media_item, 'borrow') and not media_item.is_borrowed:
            actions.append(('borrow', 'Взять в аренду', 'btn-success'))

        if hasattr(media_item, 'download'):
            actions.append(('download', 'Скачать', 'btn-secondary'))

        return actions

    def get_media_type(self, media_item):
        if isinstance(media_item, Book):
            return 'book'
        elif isinstance(media_item, Movie):
            return 'movie'
        elif isinstance(media_item, AudioBook):
            return 'audiobook'
        return 'unknown'


class MediaCreateView(TemplateView):
    template_name = 'media_library/media_form.html'

    def get(self, request, *args, **kwargs):
        form = MediaForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = MediaForm(request.POST)
        if form.is_valid():
            # Используем фабрику через форму
            form.save()
            return redirect('media_library:media_list')
        # Debug: log form errors to console to help diagnose why save didn't occur
        if form.errors:
            print('MediaForm errors:', form.errors.as_json())
        return render(request, self.template_name, {'form': form})


def media_action(request, media_type, item_id):
    # Используем фабрику для получения класса медиа
    media_class = MediaFactory.get_media_class(media_type)
    if not media_class:
        return JsonResponse({'error': 'Неизвестный тип медиа'}, status=400)

    # Диспетчеризация через словарь
    action_handlers = {
        'book': {
            'describe': lambda obj: obj.get_description(),
            'read': lambda obj: obj.read_sample(),
            'borrow': lambda obj: obj.borrow(request.user.username if request.user.is_authenticated else 'Гость'),
            'download': lambda obj: "Книги недоступны для скачивания",
        },
        'audiobook': {
            'describe': lambda obj: obj.get_description(),
            'download': lambda obj: obj.download(),
            'borrow': lambda obj: obj.borrow(request.user.username if request.user.is_authenticated else 'Гость'),
            'play_trailer': lambda obj: "Аудиокниги не имеют трейлеров",
        }
        ,
        'movie': {
            'describe': lambda obj: obj.get_description(),
            'play_trailer': lambda obj: obj.play_trailer(),
            'stream': lambda obj: obj.stream(),
            'download': lambda obj: obj.download(),
        }
    }

    action = request.POST.get('action', 'describe')

    # Получаем обработчик действия
    handler_dict = action_handlers.get(media_type, {})
    handler = handler_dict.get(action)
    if not handler:
        return JsonResponse({'error': 'Неизвестное действие'}, status=400)

    # Получаем объект и выполняем действие
    try:
        item = media_class.objects.get(id=item_id)
        result = handler(item)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'result': result})
        else:
            return redirect('media_library:media_detail', media_type=media_type, pk=item_id)

    except media_class.DoesNotExist:
        return JsonResponse({'error': 'Объект не найден'}, status=404)


def borrow_media(request, pk):
    # Используем фабрику для поиска объекта
    for media_type in MediaFactory.get_all_media_types():
        media_class = MediaFactory.get_media_class(media_type)
        try:
            item = media_class.objects.get(pk=pk)
            if hasattr(item, 'borrow'):
                result = item.borrow(request.user.username if request.user.is_authenticated else 'Гость')
                return JsonResponse({'result': result})
        except media_class.DoesNotExist:
            continue

    return JsonResponse({'error': 'Невозможно взять в аренду'}, status=400)


def download_media(request, pk):

    for media_type in MediaFactory.get_all_media_types():
        media_class = MediaFactory.get_media_class(media_type)
        try:
            item = media_class.objects.get(pk=pk)
            if hasattr(item, 'download'):
                result = item.download()
                return JsonResponse({'result': result})
        except media_class.DoesNotExist:
            continue

    return JsonResponse({'error': 'Невозможно скачать'}, status=400)


@require_POST
def add_review(request, media_type, pk):
    media_class = MediaFactory.get_media_class(media_type)
    if not media_class:
        messages.error(request, 'Неизвестный тип медиа')
        return redirect('media_library:media_list')

    try:
        item = media_class.objects.get(pk=pk)
    except media_class.DoesNotExist:
        messages.error(request, 'Объект не найден')
        return redirect('media_library:media_list')

    if not hasattr(item, 'add_review'):
        messages.error(request, 'Нельзя оставить отзыв для этого типа медиа')
        return redirect('media_library:media_detail', media_type=media_type, pk=pk)

    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '')
    try:
        item.add_review(comment, rating)
        messages.success(request, 'Спасибо — отзыв добавлен')
    except Exception as e:
        messages.error(request, f'Не удалось добавить отзыв: {e}')

    return redirect('media_library:media_detail', media_type=media_type, pk=pk)