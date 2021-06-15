from django.test import TestCase


class HomePageTest(TestCase):
    """тест домашней страницы"""

    def test_home_page_returns_correct_html(self):
        """тест: домашняя страница возвращает правильный html"""
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')
