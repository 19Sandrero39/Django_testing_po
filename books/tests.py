from django.test import TestCase
from django.urls import reverse

from .models import Book


class BookListTests(TestCase):
    """Проверки страницы со списком."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Мастер и Маргарита",
            author="Михаил Булгаков",
            description="Роман о добре и зле.",
        )

    def test_list_returns_200_and_uses_template(self):
        # 1. Страница открывается и использует нужный шаблон
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_list.html")

    def test_list_shows_book_content(self):
        # 2. На выходе получаем контент (название и автор)
        response = self.client.get(reverse("book_list"))
        self.assertContains(response, "Мастер и Маргарита")
        self.assertContains(response, "Михаил Булгаков")

    def test_list_contains_link_with_correct_id(self):
        # 3. В списке есть ссылка с правильным id
        response = self.client.get(reverse("book_list"))
        detail_url = reverse("book_detail", args=[self.book.pk])
        self.assertContains(response, f'href="{detail_url}"')

    def test_list_empty_shows_message(self):
        # 4. Если книг нет, показывается заглушка, а не ошибка
        Book.objects.all().delete()
        response = self.client.get(reverse("book_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Пока нет книг")

    def test_list_context_contains_all_books(self):
        # 5. В контексте приходят все книги из базы
        Book.objects.create(title="Вторая книга", author="Автор")
        response = self.client.get(reverse("book_list"))
        self.assertEqual(len(response.context["books"]), 2)


class BookDetailTests(TestCase):
    """Проверки детальной страницы."""

    def setUp(self):
        self.book = Book.objects.create(
            title="Война и мир",
            author="Лев Толстой",
            description="Эпопея.",
        )
        self.url = reverse("book_detail", args=[self.book.pk])

    def test_detail_returns_200_and_uses_template(self):
        # 6. Страница существующей книги открывается
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_detail.html")

    def test_detail_shows_correct_data(self):
        # 7. Получаем именно данные этой книги
        response = self.client.get(self.url)
        self.assertContains(response, "Война и мир")
        self.assertContains(response, "Лев Толстой")
        self.assertContains(response, "Эпопея.")
        self.assertEqual(response.context["book"].pk, self.book.pk)

    def test_detail_nonexistent_id_returns_404(self):
        # 8. Несуществующий id даёт 404
        response = self.client.get(reverse("book_detail", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_detail_invalid_id_format_returns_404(self):
        # 9. Нечисловой id не подходит под маршрут, тоже 404
        response = self.client.get("/abc/")
        self.assertEqual(response.status_code, 404)

    def test_detail_has_back_link_to_list(self):
        # 10. На детальной странице есть ссылка назад к списку
        response = self.client.get(self.url)
        self.assertContains(response, f'href="{reverse("book_list")}"')

    def test_follow_link_from_list_to_detail(self):
        # 11. Реально переходим по ссылке из списка
        list_response = self.client.get(reverse("book_list"))
        self.assertContains(list_response, self.url)
        detail_response = self.client.get(self.url)
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Война и мир")


class BookLikesTests(TestCase):
    """Счётчик лайков/просмотров."""

    def setUp(self):
        self.book = Book.objects.create(title="Тест", author="Автор")
        self.url = reverse("book_detail", args=[self.book.pk])

    def test_new_book_has_zero_likes(self):
        # У нового объекта лайков изначально 0
        self.assertEqual(self.book.likes, 0)

    def test_detail_view_increments_likes(self):
        # GET детальной страницы увеличивает счётчик на 1
        self.client.get(self.url)
        self.book.refresh_from_db()
        self.assertEqual(self.book.likes, 1)

    def test_two_visits_give_two_likes(self):
        # Два захода = 2
        self.client.get(self.url)
        self.client.get(self.url)
        self.book.refresh_from_db()
        self.assertEqual(self.book.likes, 2)

    def test_list_page_does_not_increment_likes(self):
        # Список счётчик не трогает
        self.client.get(reverse("book_list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.likes, 0)


class BookCrudTests(TestCase):
    """Проверки создания, редактирования и удаления."""

    def setUp(self):
        self.book = Book.objects.create(title="Старое", author="Автор")

    def test_create_page_opens(self):
        # Форма создания открывается
        response = self.client.get(reverse("book_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "books/book_form.html")

    def test_create_book_saves_to_db(self):
        # POST с верными данными создаёт книгу и ведёт на список
        response = self.client.post(
            reverse("book_create"),
            {
                "title": "Новая",
                "author": "Новый автор",
                "description": "Текст",
            },
        )
        self.assertRedirects(response, reverse("book_list"))
        self.assertTrue(Book.objects.filter(title="Новая").exists())

    def test_create_new_book_has_zero_likes(self):
        # Книга, созданная через форму, имеет 0 просмотров
        self.client.post(reverse("book_create"), {"title": "Х", "author": "Y"})
        self.assertEqual(Book.objects.get(title="Х").likes, 0)

    def test_create_invalid_data_not_saved(self):
        # Пустое название: книга не создаётся, форма показывает ошибку
        response = self.client.post(
            reverse("book_create"), {"title": "", "author": "A"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Book.objects.count(), 1)
        self.assertTrue(response.context["form"].errors)

    def test_update_book_changes_data(self):
        # POST на редактирование меняет данные
        response = self.client.post(
            reverse("book_update", args=[self.book.pk]),
            {
                "title": "Изменённое",
                "author": "Автор",
            },
        )
        self.assertRedirects(response, reverse("book_list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Изменённое")

    def test_update_page_prefilled(self):
        # Форма редактирования содержит текущие данные
        response = self.client.get(reverse("book_update", args=[self.book.pk]))
        self.assertContains(response, "Старое")

    def test_update_nonexistent_returns_404(self):
        # Редактирование несуществующей книги даёт 404
        response = self.client.get(reverse("book_update", args=[9999]))
        self.assertEqual(response.status_code, 404)

    def test_delete_get_shows_confirmation_and_keeps_book(self):
        # GET показывает подтверждение и ничего не удаляет
        response = self.client.get(reverse("book_delete", args=[self.book.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Book.objects.filter(pk=self.book.pk).exists())

    def test_delete_post_removes_book(self):
        # POST удаляет книгу и ведёт на список
        response = self.client.post(reverse("book_delete", args=[self.book.pk]))
        self.assertRedirects(response, reverse("book_list"))
        self.assertFalse(Book.objects.filter(pk=self.book.pk).exists())
