from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            slug='test-slug',
            title='Название',
            description='Описание'
        )
        cls.user = User.objects.create_user(username='leo')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_exists_at_desired_location(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_group_slug_exists_at_desired_location(self):
        """Страница /group/<slug>/ доступна любому пользователю."""
        response = self.guest_client.get(
            reverse('groups', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_new_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('new_post'))
        self.assertEqual(response.status_code, 200)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'index.html': reverse('index'),
            'group.html': reverse('groups', kwargs={'slug': self.group.slug}),
            'new.html': reverse('post_edit', kwargs={
                'username': self.post.author.username, 'post_id': self.post.id
            }),
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech')
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_profile_exists_at_desired_location(self):
        """Страница /<username>/ доступна любому пользователю."""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': self.post.author.username})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_exists_at_desired_location(self):
        """Страница /<username>/<post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(reverse('post', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        self.assertEqual(response.status_code, 200)

    def test_new_post_exists_at_desired_location(self):
        """Страница /<str:username>/<int:post_id>/edit/
         доступна автору поста."""
        self.authorized_client.login(username=self.user.username)
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        self.assertEqual(response.status_code, 200)

    def test_new_post_url_redirect_anonymous(self):
        """Страница /<str:username>/<int:post_id>/edit/
         перенаправляет анонимного пользователя."""
        response = self.guest_client.get(reverse('post_edit', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        self.assertEqual(response.status_code, 302)

    def test_task_detail_url_redirect_not_author(self):
        """Страница /<str:username>/<int:post_id>/edit/  перенаправляет не автора.
        """
        self.authorized_client.logout()
        self.authorized_client.login(username='Kate')
        response = self.authorized_client.get(reverse('post_edit', kwargs={
            'username': self.post.author.username, 'post_id': self.post.id
        }))
        self.assertEqual(response.status_code, 302)

    def test_post_exists_at_desired_location(self):
        """Страница /about/tech/ доступна любому пользователю."""
        response = self.guest_client.get(reverse('about:tech'))
        self.assertEqual(response.status_code, 200)

    def test_post_exists_at_desired_location(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = self.guest_client.get(reverse('about:author'))
        self.assertEqual(response.status_code, 200)

    def test_post_exists_at_desired_location(self):
        """Страница /about/author/ доступна любому пользователю."""
        response = self.guest_client.get('/wrong/page')
        self.assertEqual(response.status_code, 404)
