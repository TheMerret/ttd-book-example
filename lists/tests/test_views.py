import unittest
from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils.html import escape
from django.contrib.auth import get_user_model
from django.http import HttpRequest
from lists.models import Item, List
from lists.forms import (DUPLICATE_ITEM_ERROR, EMPTY_ITEM_ERROR,
                         ExistingListItemForm, ItemForm)
from lists.views import new_list

User = get_user_model()


class HomePageTest(TestCase):
    """тест домашней страницы"""

    def test_home_page_returns_correct_html(self):
        """тест: домашняя страница возвращает правильный html"""
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'home.html')

    def test_home_page_uses_item_form(self):
        """тест: домашняя страница использует форму для элемента"""
        response = self.client.get('/')
        self.assertIsInstance(response.context['form'], ItemForm)


class ListViewTest(TestCase):
    """тест представления списка"""

    def test_uses_list_template(self):
        """тест: используется шаблон списка"""
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertTemplateUsed(response, 'list.html')

    def test_displays_only_items_for_that_list(self):
        """тест: отображаются все элементы списка"""
        correct_list = List.objects.create()
        Item.objects.create(text='itemey 1', list=correct_list)
        Item.objects.create(text='itemey 2', list=correct_list)
        other_list = List.objects.create()
        Item.objects.create(text='other list item 1', list=other_list)
        Item.objects.create(text='other list item 2', list=other_list)

        response = self.client.get(f'/lists/{correct_list.id}/')

        self.assertContains(response, 'itemey 1')
        self.assertContains(response, 'itemey 2')
        self.assertNotContains(response, 'other list item 1')
        self.assertNotContains(response, 'other list item 2')

    def test_displays_item_form(self):
        """тест: отображается форма для элемента списка"""
        list_ = List.objects.create()
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertIsInstance(response.context['form'], ExistingListItemForm)
        self.assertContains(response, 'name="text"')

    def test_passes_correct_list_to_template(self):
        """тест: передается правильный шаблон списка"""
        other_list = List.objects.create()
        correct_list = List.objects.create()
        response = self.client.get(f'/lists/{correct_list.id}/')
        self.assertEqual(response.context['list'], correct_list)

    def test_can_save_a_POST_request_to_an_existing_list(self):
        """тест: можно сохранить post-запрос в существующий список"""
        other_list = List.objects.create()
        correct_list = List.objects.create()

        self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )

        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new item for an existing list')
        self.assertEqual(new_item.list, correct_list)

    def test_POST_redirects_to_list_view(self):
        """тест: переадресуется в представление списка"""
        other_list = List.objects.create()
        correct_list = List.objects.create()

        response = self.client.post(
            f'/lists/{correct_list.id}/',
            data={'text': 'A new item for an existing list'}
        )

        self.assertRedirects(response, f'/lists/{correct_list.id}/')

    def post_invalid_input(self):
        """отправляет недопустимый ввод"""
        list_ = List.objects.create()
        return self.client.post(
            f'/lists/{list_.id}/',
            data={'text': ''}
        )

    def test_for_invalid_input_nothing_saved_to_db(self):
        """тест на недопустимый ввод: ничего не сохраняется в БД"""
        self.post_invalid_input()
        self.assertEqual(Item.objects.count(), 0)

    def test_for_invalid_input_renders_list_template(self):
        """тест на недопустимый ввод: отображается шаблон списка"""
        response = self.post_invalid_input()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'list.html')

    def test_for_invalid_input_passes_form_to_template(self):
        """тест на недопустимый ввод: форма передается в шаблон"""
        response = self.post_invalid_input()
        self.assertIsInstance(response.context['form'], ExistingListItemForm)

    def test_for_invalid_input_shows_error_on_page(self):
        """тест на недопустимый ввод: на странице показывается ошибка"""
        response = self.post_invalid_input()
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))

    def test_duplicate_item_validation_errors_end_up_on_lists_page(self):
        """тест: ошибки валидации повторяющегося элемента
           оканчиваются на странице списков"""
        list1 = List.objects.create()
        item1 = Item.objects.create(list=list1, text='textey')
        response = self.client.post(
            f'/lists/{list1.id}/',
            data={'text': 'textey'}
        )
        expected_error = escape(DUPLICATE_ITEM_ERROR)
        self.assertContains(response, expected_error)
        self.assertTemplateUsed(response, 'list.html')
        self.assertEqual(Item.objects.all().count(), 1)


class NewListViewIntegratedTest(TestCase):
    """интегрированный тест нового представления списка"""

    def test_can_save_POST_request(self):
        """тест: можно сохранить post-запрос"""
        self.client.post('/lists/new', data={'text': 'A new list item'})
        self.assertEqual(Item.objects.count(), 1)
        new_item = Item.objects.first()
        self.assertEqual(new_item.text, 'A new list item')

    def test_list_owner_is_saved_if_user_is_authenticated(self):
        """тест: владелец списка сохраняется, если
        пользователь аутентифицирован"""
        user = User.objects.create(email='a@b.com')
        self.client.force_login(user)
        self.client.post('/lists/new', data={'text': 'new item'})
        list_ = List.objects.first()
        self.assertEqual(list_.owner, user)

    def test_for_invalid_input_doesnt_save_but_shows_errors(self):
        """тест: недопустимый ввод не сохраняется, но показывает ошибки"""
        response = self.client.post('/lists/new', data={'text': ''})
        self.assertEqual(List.objects.count(), 0)
        self.assertContains(response, escape(EMPTY_ITEM_ERROR))


@patch('lists.views.NewListForm')
class NewListViewUnitTest(unittest.TestCase):
    """модульный тест нового представления списка"""

    def setUp(self) -> None:
        """установка"""
        self.request = HttpRequest()
        self.request.POST['text'] = 'new list item'
        self.request.user = Mock()

    def test_passes_POST_data_to_NewListForm(self, mockNewListForm: Mock):
        """тест: передаются POST-данные в новую форму списка"""
        new_list(self.request)
        mockNewListForm.assert_called_once_with(data=self.request.POST)

    def test_saves_form_with_owner_if_form_valid(self, mockNewListForm: Mock):
        """тест: сохраняет форму с владельцем, если форма допустима"""
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        new_list(self.request)
        mock_form.save.assert_called_once_with(owner=self.request.user)

    @patch('lists.views.redirect')
    def test_redirects_to_form_returned_object_if_form_valid(
            self, mock_redirect: Mock, mockNewListForm: Mock
    ):
        """тест: переадресует в возвращаемый формой объект,
           если форма допустима"""
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = True
        response = new_list(self.request)
        self.assertEqual(response, mock_redirect.return_value)
        mock_redirect.assert_called_once_with(mock_form.save.return_value)

    @patch('lists.views.render')
    def test_renders_home_template_with_form_if_form_invalid(
            self, mock_render, mockNewListForm
    ):
        """тест: отображает домашний шаблон с формой, если форма недопустима"""
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        response = new_list(self.request)

        self.assertEqual(response, mock_render.return_value)

        mock_render.assert_called_once_with(
            self.request, 'home.html', {'form': mock_form}
        )

    def test_does_not_save_if_form_invalid(self, mockNewListForm: Mock):
        """тест: не сохраняет, если форма недопустима"""
        mock_form = mockNewListForm.return_value
        mock_form.is_valid.return_value = False
        new_list(self.request)
        self.assertFalse(mock_form.save.called)


class MyListTest(TestCase):
    """Тест моих списков"""

    def test_my_lists_url_renders_my_lists_template(self):
        """URL «мои списки» использует шаблон «мои списки»"""
        User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertTemplateUsed(response, 'my_lists.html')

    def test_passes_correct_owner_to_template(self):
        """тест: передается правильный владелец в шаблон"""
        User.objects.create(email='wrong@owner.com')
        correct_user = User.objects.create(email='a@b.com')
        response = self.client.get('/lists/users/a@b.com/')
        self.assertEqual(response.context['owner'], correct_user)


class ShareListTest(TestCase):
    """Тест обмена списками"""

    def test_post_redirects_to_list_page(self):
        """тест: POST переадресует на страницу того же списка"""
        other_owner = User.objects.create(email='a@b.com')
        List.objects.create(owner=other_owner)
        list_id = List.objects.create().id
        response = self.client.post(
            f'/lists/{list_id}/share',
            data={'sharee': other_owner.email}
        )
        self.assertRedirects(response, f'/lists/{list_id}/')

    def test_post_saves_to_shared_with(self):
        """тест: POST с данными другого пользователя сохраняет в shared_with списка"""
        list_ = List.objects.create()
        other_owner = User.objects.create(email='share@email.com')
        List.objects.create(owner=other_owner)
        self.client.post(
            f'/lists/{list_.id}/share',
            data={'sharee': other_owner.email}
        )
        self.assertIn(other_owner, list_.shared_with.all())

    def test_shared_with_users_shows_at_page(self):
        """тест: пользователи с кем поделились отображаются на старице"""
        list_ = List.objects.create()
        other_owner = User.objects.create(email='share@email.com')
        List.objects.create(owner=other_owner)
        self.client.post(
            f'/lists/{list_.id}/share',
            data={'sharee': other_owner.email},
        )
        response = self.client.get(f'/lists/{list_.id}/')
        self.assertContains(response, other_owner.email)

    def test_other_user_can_see_shared_list(self):
        """тест: другой пользователь можеть видеть спискок"""
        owner = User.objects.create(email='a@b.com')
        list_ = List.create_new('ab item', owner=owner)
        other_owner = User.objects.create(email='share@email.com')
        List.create_new('Share item', owner=other_owner)
        self.client.post(
            f'/lists/{list_.id}/share',
            data={'sharee': other_owner.email},
        )
        response = self.client.get(
            f'/lists/users/{other_owner.email}/'
        )
        self.assertContains(response, 'ab item')

    def test_other_user_can_see_list_owner(self):
        owner = User.objects.create(email='a@b.com')
        list_ = List.create_new('ab item', owner=owner)
        other_owner = User.objects.create(email='share@email.com')
        List.create_new('Share item', owner=other_owner)
        self.client.post(
            f'/lists/{list_.id}/share',
            data={'sharee': other_owner.email},
        )
        response = self.client.get(
            f'/lists/users/{other_owner.email}/'
        )
        self.assertContains(response, owner.email)

