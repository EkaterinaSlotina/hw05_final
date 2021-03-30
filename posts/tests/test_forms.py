import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, User, Group, Comment


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        settings.MEDIA_ROOT = tempfile.mkdtemp(dir='media')

        cls.group = Group.objects.create(
            slug='test-slug',
            title='Название',
            description='Описание'
        )
        cls.user = User.objects.create_user(username='leo')
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
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст из формы',
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_change_post(self):
        """Валидная форма изменяет запись в Post."""

        form_data1 = {
            'text': 'Текст из формы1',
        }
        form_data2 = {
            'text': 'Текст из формы2',
        }
        self.authorized_client.post(
            reverse('new_post'),
            data=form_data1,
            follow=True
        )
        self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': self.post.author.username, 'post_id': self.post.id
            }),
            data=form_data2,
            follow=True
        )

        post = get_object_or_404(
            Post, author__username=self.post.author.username, id=self.post.id
        )
        self.assertEqual(post.text, form_data2['text'])

    def test_image_exist(self):
        """Проверяем, что создалась запись с нашей картинкой."""

        form_data = {
            'text': 'Текст из формы',
            'image': self.uploaded,
        }

        self.authorized_client.post(
            reverse('post_edit', kwargs={
                'username': self.post.author.username, 'post_id': self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertTrue(
            Post.objects.filter(
                image='posts/small.gif'
            ).exists()
        )

    def test_create_comment(self):
        """Только авторизованный клиент может создавать комментарии."""
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Комментарий',
        }

        self.authorized_client.post(
            reverse('add_comment', kwargs={
                'username': self.post.author.username, 'post_id': self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        self.guest_client.post(
            reverse('add_comment', kwargs={
                'username': self.post.author.username, 'post_id': self.post.id
            }),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
