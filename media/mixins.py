class BorrowableMixin:
    def borrow(self, user):
        self.is_borrowed = True
        self.borrowed_by = user
        self.save()
        return f"{self.title} взято в аренду пользователем {user}"

class DownloadableMixin:
    def download(self):
        return f"Скачивание {self.title} началось..."

class ReviewableMixin:
    def add_review(self, review_text, rating):
        # Ожидаем, что в модели отзывов используется related_name='ratings'
        if rating is None or not (1 <= int(rating) <= 5):
            raise ValueError('Оценка должна быть от 1 до 5')
        return self.ratings.create(comment=review_text, rating=int(rating))

    def get_reviews(self):
        return self.ratings.all()


class StreamableMixin:
    def stream(self):
        return f"Начинается потоковая трансляция '{self.title}'"