from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect, get_object_or_404

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {
        'page': page, 'paginator': paginator
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list_groups = group.posts.all()
    paginator = Paginator(post_list_groups, 10)
    page_number_groups = request.GET.get('page')
    page = paginator.get_page(page_number_groups)
    return render(request, 'group.html', {
        'group': group, 'page': page, 'paginator': paginator
    })


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')
    return render(request, 'new.html', {
        'form': form, 'is_new_post': True
    })


def profile(request, username):
    author = get_object_or_404(User, username=username)
    author_posts = author.posts.all()
    paginator = Paginator(author_posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    count = author_posts.count()
    followers_count = author.following.all().count()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=author).exists()
    return render(request, 'profile.html', {
        'page': page, 'author': author, 'count': count,
        'following': following, "followers_count": followers_count
    })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    count = post.author.posts.count()
    form = CommentForm()
    comments = post.comments.all()
    return render(request, 'post.html', {
        'post': post, 'author': post.author, 'count': count,
        'form': form, 'comments': comments
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'new.html', {
        'form': form, 'post': post,
        'is_new_post': False
    })


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'includes/comments.html', {
        'form': form, 'post': post
    })


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {
        'page': page,
        'paginator': paginator,
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)
