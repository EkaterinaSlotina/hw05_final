import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir='media')

        cls.group = Group.objects.create(
            title='Заголовок',
            slug='test-slug',
            description='Описание'
        )
        cls.group_second = Group.objects.create(
            title='Заголовок2',
            slug='test-slug2',
            description='Описание2'
        )

        cls.user = User.objects.create_user(username='leo')
        cls.amazing_follower = User.objects.create_user(username='valentinka')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

        for i in range(12):
            Post.objects.create(
                text='Тестовый пост',
                author=cls.user,
                group=cls.group,
                image=cls.uploaded
            )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_follower = Client()

        self.authorized_client.force_login(self.user)
        self.authorized_client_follower.force_login(self.amazing_follower)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': reverse('groups', kwargs={'slug': self.group.slug}),
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }

        for template, reverse_name in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_correct_context(self):
        """Шаблон new сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_home_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        post_object = response.context['page'][0]
        post_author = post_object.author
        post_text = post_object.text
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_text, self.post.text)
        self.assertTrue(post_object.image)

    def test_group_correct_context(self):
        """Шаблон groups сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('groups', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context['group'].title, self.group.title)
        self.assertEqual(
            response.context['group'].description, self.group.description
        )

        post_object = response.context['page'][0]
        post_author = post_object.author
        post_text = post_object.text
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_text, self.post.text)
        self.assertTrue(post_object.image)

    def test_home_incorrect_context(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('groups', kwargs={'slug': self.group_second.slug})
        )
        post_objects = response.context['page']
        self.assertEqual(len(post_objects), 0)

    def test_first_page_contain_ten_records(self):
        """Паджинатор, на странице отображается только
        определенное количество записей"""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_post_edit_correct_context(self):
        """Шаблон post_new сформирован с правильным контекстом."""
        self.authorized_client.login(username=self.user.username)
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('post', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        self.assertEqual(response.context['count'], 13)

        self.assertEqual(
            response.context['post'].author.username,
            self.post.author.username)
        self.assertEqual(
            response.context['post'].author, self.post.author)
        self.assertEqual(
            response.context['post'].pub_date, self.post.pub_date)
        self.assertEqual(response.context['post'].text, self.post.text)
        self.assertTrue(response.context['post'].image)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.post.author.username})
        )
        self.assertEqual(response.context['count'], 13)

        post_object = response.context['page'][0]
        post_author_user = post_object.author.username
        post_author = post_object.author
        post_text = post_object.text
        self.assertEqual(post_author_user, self.post.author.username)
        self.assertEqual(post_author, self.post.author)
        self.assertEqual(post_text, self.post.text)
        self.assertTrue(post_object.image)

    def test_index_page_cache(self):
        """Тестирование кеша. """
        response_1 = self.authorized_client.get(reverse('index'))

        Post.objects.create(
            text='Новый пост',
            author=self.user,
        )

        response_2 = self.authorized_client.get(reverse('index'))
        self.assertEqual(response_1.content, response_2.content)

        cache.clear()

        response_3 = self.authorized_client.get(reverse('index'))
        self.assertNotEqual(response_1.content, response_3.content)

    def test_authorized_client_follow(self):
        """Тестирование подписки """

        response = self.authorized_client_follower.get(
            reverse('profile', kwargs={'username': self.post.author.username})
        )

        followers_count = response.context['followers_count']

        self.authorized_client_follower.get(
            reverse('profile_follow', kwargs={
                'username': self.post.author.username
            }))

        response_2 = self.authorized_client_follower.get(
            reverse('profile', kwargs={
                'username': self.post.author.username
            }))

        self.assertEqual(
            response_2.context['followers_count'], followers_count + 1
        )

    def test_authorized_client_unfollow(self):
        """Тестирование отписки """
        self.authorized_client_follower.get(
            reverse('profile_follow', kwargs={
                'username': self.post.author.username
            }))

        response = self.authorized_client_follower.get(
            reverse('profile', kwargs={'username': self.post.author.username})
        )

        self.authorized_client_follower.get(
            reverse('profile_unfollow', kwargs={
                'username': self.post.author.username
            }))

        response_3 = self.authorized_client_follower.get(
            reverse('profile', kwargs={'username': self.post.author.username})
        )

        self.assertEqual(
            response_3.context['followers_count'],
            response.context['followers_count'] - 1
        )

    def test_new_sign_follower(self):
        """Новая запись появляется у подписчиков. """
        self.authorized_client_follower.get(
            reverse('profile_follow', kwargs={
                'username': self.post.author.username
            }))

        response = self.authorized_client_follower.get(
            reverse('follow_index'))

        Post.objects.create(
            text='Новый пост',
            author=self.user,
        )

        response_2 = self.authorized_client_follower.get(
            reverse('follow_index'))

        self.assertNotEqual(response_2.content, response.content)

    def test_new_sign_not_follower(self):
        """Новая запись не появляется у тех, кто не подписан. """
        response = self.authorized_client_follower.get(
            reverse('follow_index'))

        Post.objects.create(
            text='Новый пост',
            author=self.user,
        )

        response_2 = self.authorized_client_follower.get(
            reverse('follow_index'))

        self.assertEqual(response_2.content, response.content)
